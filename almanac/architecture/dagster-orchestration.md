---
title: Dagster Orchestration
summary: Generic asset factory pattern for Dagster that auto-generates Bronze assets from collector registry, plus dbt transformation assets and freshness sensors.
topics: [architecture, orchestration, dagster]
---

# Dagster Orchestration

Dagster orchestrates SoloDShouse's data pipelines using a generic asset factory
pattern that auto-generates software-defined assets from the collector registry.
This design eliminates manual Dagster configuration when adding new data sources.

The orchestration layer defines assets, jobs, schedules, and sensors that
drive the complete data pipeline from collection through transformation.

## Asset Factory Pattern

The core innovation is `make_bronze_assets()`, which generates Dagster assets
dynamically from the collector registry:

```python
def make_bronze_assets() -> list:
    return [_make_bronze_asset(name) for name in list_sources()]
```

Each `_make_bronze_asset(source_name)` creates a Dagster `@asset` decorator
with:

- **Name**: `{source_name}_bronze` (e.g., `entso_generation_bronze`)
- **Group**: `"bronze"` (organizes assets in Dagster UI)
- **Retry policy**: 3 retries with 10s delay
- **Description**: `"Ingest {source_name} -> Bronze."`
- **Dependencies**: None (Bronze layer has no upstream dependencies)

The asset function:
1. Retrieves the collector class from the registry
2. Instantiates it with the Iceberg catalog
3. Calls `collect()` to execute the full ingestion pipeline
4. Records output metadata (valid/rejected counts)
5. Logs execution metrics

## dbt Transformation Asset

The `dbt_run_asset` represents the Silver→Gold transformation stage, depending
on all Bronze assets:

```python
@asset(
    name="dbt_run",
    group_name="gold",
    deps=[AssetKey(f"{name}_bronze") for name in list_sources()],
    description="Run dbt models on ingested Bronze sources.",
)
def dbt_run_asset(context) -> dict[str, Any]:
```

This asset:
1. Waits for all Bronze assets to complete
2. Executes dbt `run` and `test` commands against DuckDB
3. Logs stderr/stdout for debugging
4. Returns execution metadata

The dbt project lives in `transformations/dbt/` with DuckDB as the target.

## Job Definitions

Two jobs are defined in `definitions.py`:

```python
full_pipeline_job = define_asset_job(
    name="full_pipeline_job",
    selection=AssetSelection.assets(*all_assets),
)

bronze_only_job = define_asset_job(
    name="bronze_only_job",
    selection=AssetSelection.assets(*bronze_assets),
)
```

- **full_pipeline_job**: Executes all assets (Bronze + dbt transformation)
- **bronze_only_job**: Executes only Bronze assets (faster, for development)

## Schedule Configuration

A daily cron schedule triggers the full pipeline at 07:00 UTC:

```python
daily_pipeline_schedule = ScheduleDefinition(
    name="daily_pipeline_schedule",
    job=full_pipeline_job,
    cron_schedule="0 7 * * *",
    execution_timezone="UTC",
)
```

## Freshness Sensor

The `bronze_freshness_sensor` monitors Bronze table freshness and triggers
pipeline runs for stale sources (older than 30 days):

```python
@sensor(job_name="full_pipeline_job", minimum_interval_seconds=3600 * 24)
def bronze_freshness_sensor(iceberg_catalog: IcebergCatalogResource):
```

The sensor:
1. Scans all Bronze tables daily
2. Identifies sources with `_ingestion_timestamp` older than 30 days
3. Creates a `RunRequest` with asset selection for stale sources only
4. Skips the pipeline if all sources are fresh

## Resource Configuration

Dagster resources provide dependency injection:

```python
resources={
    "pipeline_config": PipelineConfigResource(),
    "iceberg_catalog": IcebergCatalogResource(),
}
```

### IcebergCatalogResource

Manages PyIceberg catalog creation with environment variable fallbacks:

```python
class IcebergCatalogResource(ConfigurableResource):
    hive_metastore_uri: str | None = None
    warehouse: str | None = None
    s3_endpoint: str | None = None
    access_key: str | None = None
    secret_key: str | None = None

    def get_catalog(self):
        from ingestion.iceberg_io import get_catalog
        return get_catalog(
            uri=self.hive_metastore_uri,
            warehouse=self.warehouse,
            s3_endpoint=self.s3_endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
        )
```

### PipelineConfigResource

Provides runtime configuration for the pipeline:

```python
class PipelineConfigResource(ConfigurableResource):
    bucket: str = DEFAULT_STORAGE_CONFIG.data_bucket
    audit_bucket: str = DEFAULT_STORAGE_CONFIG.audit_bucket
    mlflow_artifact_bucket: str = DEFAULT_STORAGE_CONFIG.mlflow_artifact_bucket
    mlflow_artifact_root: str = DEFAULT_STORAGE_CONFIG.mlflow_artifact_root
    warehouse_uri: str = DEFAULT_STORAGE_CONFIG.warehouse_uri
    mlflow_tracking_uri: str = os.environ.get("MLFLOW_TRACKING_URI", "http://localhost:5000")
    trino_url: str = os.environ.get("TRINO_URL", "http://localhost:8080")
```

## Module-Level Asset Generation

Assets are generated at module import time:

```python
_bronze_assets = make_bronze_assets()
_bronze_freshness_sensor = _make_freshness_sensor()

bronze_assets = _bronze_assets

all_assets = [*_bronze_assets, dbt_run_asset]
```

This means:
- Adding a new collector automatically creates a Bronze asset
- The dbt transformation asset depends on all Bronze sources
- The freshness sensor monitors all Bronze tables

## Error Handling

The orchestration handles several error scenarios:

- **Missing collectors**: `make_bronze_assets()` returns empty list if no
  collectors are registered
- **dbt failures**: Logs stderr and raises `RuntimeError` with last 300
  characters of error output
- **dbt test warnings**: Logs warnings but doesn't fail the pipeline
- **NoSuchTableError**: Freshness sensor skips missing tables gracefully

## See Also

- [Ingestion Pipeline](ingestion-pipeline.md) — full data flow
- [Collector Pattern](../concepts/collector-pattern.md) — plugin system
- [Dynamic Collector](../concepts/dynamic-collector.md) — connection-backed collectors
- [Medallion Architecture](../concepts/medallion-architecture.md) — Bronze→Silver→Gold
