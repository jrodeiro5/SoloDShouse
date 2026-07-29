---
title: Ingestion Pipeline
summary: Full data ingestion flow from external sources through Bronze Iceberg tables, including collector execution, validation, and freshness monitoring.
topics: [architecture, ingestion, data-flow]
---

# Ingestion Pipeline

The ingestion pipeline processes data from external sources through a
multi-stage flow: collection, validation, Bronze layer writing, and freshness
monitoring. This architecture enables domain-agnostic data ingestion through
the collector plugin system (SDS-043) and connection-backed dynamic collectors
(SDS-044).

The pipeline executes within Dagster, with each data source represented as a
software-defined asset that triggers on a daily schedule or freshness sensor
activation.

## Pipeline Stages

### 1. Collection

Collectors fetch raw data from external sources using source-specific
mechanisms:

- **Static collectors** (SDS-043): Custom collectors for specific APIs (e.g.,
  ENTSO-E, Open-Meteo) implemented as subclasses of `BaseCollector`
- **Dynamic collectors** (SDS-044): Auto-generated collectors from
  `config/connections.yaml` entries, using `DynamicCollector` with fetch
  helpers for REST, S3, PostgreSQL, and filesystem sources

Each collector receives a PyIceberg `Catalog` and uses it to write data to
the Bronze layer.

### 2. Validation

Raw records are validated against the source's YAML schema configuration.
Records are split into two batches:

- **Valid records**: Match the schema columns and are ready for Bronze writing
- **Rejected records**: Fail validation with reasons and original payloads
  stored in the `bronze.rejected_records` table

Validation uses `load_schema_config()` to retrieve column definitions, falling
back to the first record's keys if no schema exists.

### 3. Bronze Writing

Valid records are appended to Bronze Iceberg tables using `append_table()`,
preserving historical data for audit and reprocessing. Each Bronze table is
partitioned by day on `_ingestion_timestamp` for efficient time-range queries.

Rejected records are written to a separate `bronze.rejected_records` table with
source, rejection reason, and original payload as JSON (truncated to 500
characters).

### 4. Dagster Asset Execution

Each collector becomes a Dagster software-defined asset:

```python
@asset(
    name=f"{source_name}_bronze",
    group_name="bronze",
    retry_policy=RetryPolicy(max_retries=3, delay=10),
    description=f"Ingest {source_name} -> Bronze.",
)
def _impl(context, iceberg_catalog: IcebergCatalogResource) -> dict[str, Any]:
    started = time.perf_counter()
    result = collector_cls(iceberg_catalog.get_catalog()).collect()
    context.add_output_metadata({
        "valid": result.get("valid", 0),
        "rejected": result.get("rejected", 0)
    })
    _emit_metric(f"{source_name}_bronze", started)
    return result
```

Assets are grouped under "bronze" and include retry policies (3 retries, 10s
delay) for resilience.

### 5. Freshness Monitoring

A freshness sensor monitors Bronze tables daily, triggering pipeline runs for
stale sources:

```python
@sensor(job_name="full_pipeline_job", minimum_interval_seconds=3600 * 24)
def bronze_freshness_sensor(iceberg_catalog: IcebergCatalogResource):
    catalog = iceberg_catalog.get_catalog()
    stale_sources: list[str] = []

    for source_name in list_sources():
        try:
            df = iceberg_io.scan_table(catalog, "bronze", source_name)
            if not df.empty and "_ingestion_timestamp" in df.columns:
                latest = pd.to_datetime(
                    df["_ingestion_timestamp"], utc=True
                ).max().date()
        except NoSuchTableError:
            pass

        if latest is None or (
            datetime.now(timezone.utc).date() - latest
        ).days >= 30:
            stale_sources.append(source_name)

    if stale_sources:
        return RunRequest(
            run_key=f"freshness-{datetime.now(timezone.utc).date().isoformat()}",
            asset_selection=[AssetKey(f"{s}_bronze") for s in stale_sources],
        )
    return SkipReason("All bronze sources have fresh data")
```

Sources are considered stale if their latest `_ingestion_timestamp` is more
than 30 days old or if the table doesn't exist yet.

## Error Handling

The pipeline handles several error scenarios:

- **Missing collectors**: Logs warning and continues with available sources
- **Validation failures**: Records rejected data separately, doesn't fail the
  entire pipeline
- **Network errors**: Fetch helpers use timeouts (30s for REST, configurable
  for others) and retry on transient failures
- **Schema mismatches**: Falls back to first-record keys when no schema exists
- **Dagster retries**: 3 retries with 10s delay for transient failures

## Metrics and Logging

Each pipeline step logs structured metrics:

- `bronze_written`: Source, row count, Iceberg path
- `bronze_rejected_written`: Source, rejection count
- `pipeline_metric`: Step name, duration in milliseconds
- `schema_discovered`: Source, connection type, column count
- `dynamic_collector_registered`: Source name

All logs use `structlog.get_logger()` for consistent formatting and structured
output.

## See Also

- [Collector Pattern](../concepts/collector-pattern.md) — plugin system
- [Dynamic Collector](../concepts/dynamic-collector.md) — connection-backed collectors
- [Schema Discovery](../concepts/schema-discovery.md) — dlt-powered schema inference
- [Medallion Architecture](../concepts/medallion-architecture.md) — Bronze→Silver→Gold
- [Iceberg I/O](../concepts/iceberg-io.md) — pyiceberg abstraction
- [Dagster Orchestration](dagster-orchestration.md) — pipeline orchestration
