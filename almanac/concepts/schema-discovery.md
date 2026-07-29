---
title: Schema Discovery
summary: dlt-powered schema inference that probes connected data sources and writes declarative YAML schema configs for automatic collector registration.
topics: [concepts, architecture, ingestion, connections]
---

# Schema Discovery

Schema Discovery is SoloDShouse's mechanism for automatically inferring Iceberg
schemas from connected data sources using dlt (data load tool). It probes
connected sources, infers column names and types, and writes declarative YAML
schema configs to `config/schemas/{source}.yaml`.

The discovery process bridges the connections layer (SDS-044) with the collector
pattern (SDS-043): once a schema is discovered, the SDS-043 collector registry
picks it up automatically, enabling zero-configuration data ingestion.

## Architecture

The `SchemaDiscovery` class provides a single `discover()` method that takes a
source name and connection configuration, probes the source using dlt, and
writes the inferred schema to YAML. The discovered schemas are stored in
`config/schemas/` and follow the format expected by `load_schema_config()` and
`schema_from_config()` in the Iceberg schemas module.

```python
class SchemaDiscovery:
    def __init__(self, schemas_dir: str | Path = SCHEMAS_DIR) -> None:
        self._schemas_dir = Path(schemas_dir)
        self._schemas_dir.mkdir(parents=True, exist_ok=True)

    def discover(self, source_name: str, connection: ConnectionConfig) -> dict[str, Any]:
        """Probe *connection*, infer schema, and persist to YAML."""
        inferred = self._infer_schema(source_name, connection)
        self._write_config(source_name, inferred)
        return inferred
```

The discovery process works for four connection types: PostgreSQL, S3, REST,
and filesystem. Each type uses dlt's pipeline API to probe the source and
infer column types.

## PostgreSQL Schema Discovery

For PostgreSQL connections, the discovery process creates a dlt pipeline that
connects to the database, queries the specified table, and infers column types
from the result set.

```python
def _probe_postgres(self, source: str, config: PostgresConfig) -> list[dict[str, Any]]:
    table = config.table or source
    pipeline = dlt.pipeline(
        pipeline_name=f"discover_{source}",
        destination="duckdb",
        dataset_name="bronze",
    )
    conn_str = f"postgresql://{config.user}:{config.password}"
    f"{config.host}:{config.port}/{config.database}"
    src = sql_database.sql_database(
        credentials=conn_str,
        schema=config.schema,
        table_names=[table],
    )
    pipeline.run(src)
    return _columns_from_dlt_schema(pipeline.default_schema, table)
```

If dlt is not installed, the discovery falls back to returning a single
`_raw` string column, allowing the system to continue with minimal schema
information.

## S3 Schema Discovery

For S3 connections, the discovery process uses dlt's filesystem source to
probe objects in the specified bucket and prefix. It supports Parquet and CSV
formats, inferring column types from the file contents.

```python
def _probe_s3(self, source: str, config: S3Config) -> list[dict[str, Any]]:
    prefix = config.prefix or source
    bucket = config.bucket
    pipeline = dlt.pipeline(
        pipeline_name=f"discover_{source}",
        destination="duckdb",
        dataset_name="bronze",
    )
    src = filesystem.filesystem(
        bucket_url=f"s3://{bucket}/{prefix}",
        file_glob=config.file_glob,
    )
    pipeline.run(src)
    return _columns_from_dlt_schema(pipeline.default_schema, source)
```

## REST Schema Discovery

For REST connections, the discovery process makes HTTP GET requests to the
specified URL and endpoint, parsing JSON responses to infer column types.
It handles common response structures by looking for `data`, `results`,
`items`, or `records` keys.

```python
def _probe_rest(self, source: str, config: RestConfig) -> list[dict[str, Any]]:
    url = config.base_url
    endpoint = config.endpoint or ""
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else url
    _validate_rest_url(full_url)
    resp = requests.get(full_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    pipeline = dlt.pipeline(
        pipeline_name=f"discover_{source}",
        destination="duckdb",
        dataset_name="bronze",
    )
    if isinstance(data, list) and len(data) > 0:
        pipeline.run([data], table_name=source)
        return _columns_from_dlt_schema(pipeline.default_schema, source)
    return _infer_from_dict(_extract_first_record(data))
```

The `_validate_rest_url()` function prevents SSRF attacks by blocking requests
to internal or localhost addresses.

## Filesystem Schema Discovery

For filesystem connections, the discovery process scans local directories for
Parquet or CSV files using glob patterns, inferring column types from the file
contents.

```python
def _probe_filesystem(self, source: str, config: FilesystemConfig) -> list[dict[str, Any]]:
    path = config.path or f"./data/{source}"
    pipeline = dlt.pipeline(
        pipeline_name=f"discover_{source}",
        destination="duckdb",
        dataset_name="bronze",
    )
    src = filesystem.filesystem(
        bucket_url=path,
        file_glob=config.file_glob,
    )
    pipeline.run(src)
    return _columns_from_dlt_schema(pipeline.default_schema, source)
```

## Schema Output Format

Discovered schemas are written as YAML files in the following format:

```yaml
source: my_source
connection_type: postgres
columns:
  - name: id
    type: long
    nullable: true
  - name: name
    type: string
    nullable: false
auto_discovered: true
```

The YAML format is compatible with `load_schema_config()` and `schema_from_config()`
in the Iceberg schemas module, enabling automatic collector registration.

## Column Type Mapping

The discovery process maps dlt column types to Iceberg types using the
following mapping:

| dlt type | Iceberg type |
|----------|--------------|
| text, varchar | string |
| bigint | long |
| integer, smallint | int |
| boolean | boolean |
| double | double |
| float | float |
| timestamp | timestamp |
| date | date |
| decimal | decimal(38,18) |
| json, complex | string |

## See Also

- [Collector Pattern](collector-pattern.md) — plugin system with BaseCollector, registry
- [Dynamic Collector](dynamic-collector.md) — connection-backed auto-collector
- [Connections Layer](../architecture/connections-layer.md) — YAML-driven connection management
- [Medallion Architecture](medallion-architecture.md) — Bronze→Silver→Gold flow
