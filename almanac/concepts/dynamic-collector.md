---
title: Dynamic Collector
summary: Connection-backed auto-collector (SDS-044) that bridges the collector pattern with the connections layer, automatically registering collectors for each YAML connection entry.
topics: [concepts, architecture, ingestion, connections]
---

# Dynamic Collector

The Dynamic Collector bridges the collector pattern (SDS-043) with the
connections layer (SDS-044). It automatically registers a collector for each
entry in `config/connections.yaml`, enabling connection-backed data ingestion
without manual collector registration.

The Dynamic Collector reads connection configurations, fetches data using
appropriate drivers, validates records against YAML schemas, and writes valid
data to the Bronze Iceberg layer while tracking rejected records separately.

## Architecture

The Dynamic Collector operates at import time, scanning `config/connections.yaml`
and registering a collector instance for each connection entry. This happens
automatically when the `ingestion.collectors` module is imported, creating a
seamless bridge between the static collector registry and dynamic connection
configurations.

```python
if _MGR is not None:
    for _name in _MGR.list_connections():
        _cls = type(f"_Dynamic_{_name}", (DynamicCollector,), {"_source": _name})
        register_collector(_name)(_cls)
```

Each connection entry becomes a dynamically-typed collector class that inherits
from `DynamicCollector` and is registered under the connection's name.

## Fetch Helpers

The Dynamic Collector includes specialized fetch helpers for four connection
types, each implementing the appropriate data retrieval mechanism:

### REST Connections

The `_fetch_rest()` helper makes HTTP GET requests to REST API endpoints,
parsing JSON responses and extracting data arrays. It handles common response
structures by looking for `data`, `results`, `items`, or `records` keys.

```python
def _fetch_rest(config: Any) -> list[dict[str, Any]]:
    import requests
    url = config.base_url
    endpoint: str = getattr(config, "endpoint", "") or ""
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else url
    resp = requests.get(full_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "items", "records"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    return []
```

### S3 Connections

The `_fetch_s3()` helper uses boto3 to list and read objects from S3-compatible
storage (SeaweedFS in this deployment). It supports both Parquet and CSV formats,
reading up to 10 files by default.

```python
def _fetch_s3(source: str, config: Any) -> list[dict[str, Any]]:
    import boto3
    bucket = config.bucket
    prefix: str = getattr(config, "prefix", "") or source
    file_glob: str = getattr(config, "file_glob", "*.parquet")
    client = boto3.client("s3", ...)
    resp = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=10)
    # ... reads and converts to records
```

### PostgreSQL Connections

The `_fetch_postgres()` helper executes `SELECT *` queries against PostgreSQL
tables with a LIMIT of 1000 rows, converting results to dictionaries for
validation and Bronze writes.

```python
def _fetch_postgres(config: Any) -> list[dict[str, Any]]:
    import psycopg2
    conn = psycopg2.connect(host=config.host, port=config.port, ...)
    cur = conn.cursor()
    query = sql.SQL("SELECT * FROM {}.{} LIMIT 1000").format(...)
    cur.execute(query)
    cols = [desc[0] for desc in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows
```

### Filesystem Connections

The `_fetch_filesystem()` helper scans local directories for Parquet or CSV
files using glob patterns, reading and converting them to record lists.

```python
def _fetch_filesystem(config: Any) -> list[dict[str, Any]]:
    from pathlib import Path
    path: str = getattr(config, "path", "") or ""
    file_glob: str = getattr(config, "file_glob", "*.parquet")
    dir_path = Path(path)
    files = sorted(dir_path.rglob(file_glob)) if dir_path.exists() else []
    rows: list[dict[str, Any]] = []
    for f in files[:10]:
        if f.suffix == ".parquet":
            df = pd.read_parquet(f)
        elif f.suffix == ".csv":
            df = pd.read_csv(f)
        rows.extend(df.to_dict(orient="records"))
    return rows
```

## Validation Flow

The `_validate_records()` method validates fetched data against the source's
YAML schema configuration. It loads the schema using `load_schema_config()` and
extracts column names, then splits records into valid and rejected batches:

```python
def _validate_records(self, raw: list[dict[str, Any]], *args: Any, **kwargs: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not raw:
        return [], []
    try:
        schema_cfg = load_schema_config(self._source)
        col_names = {c["name"] for c in schema_cfg.get("columns", [])}
    except FileNotFoundError:
        col_names = set(raw[0].keys()) if raw else set()

    valid: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for record in raw:
        try:
            valid.append({k: record.get(k) for k in col_names if k not in ("_ingestion_timestamp", "_source")})
        except Exception:
            rejected.append({"rejection_reason": "validation_error", "payload": str(record)[:500]})
    return valid, rejected
```

Records that match the schema columns are added to the valid batch; records
that fail validation are added to the rejected batch with a reason and the
original payload as JSON (truncated to 500 characters).

## Module-Level Auto-Registration

The module-level auto-registration triggers when `ConnectionManager` is
available, scanning all connection entries and registering dynamic collectors
for each one. This happens automatically at import time, creating a seamless
bridge between the static collector registry and dynamic connection
configurations.

```python
if _MGR is not None:
    for _name in _MGR.list_connections():
        _cls = type(f"_Dynamic_{_name}", (DynamicCollector,), {"_source": _name})
        register_collector(_name)(_cls)
        logger.info("dynamic_collector_registered", source=_name)
```

This means adding a new data connection to `config/connections.yaml`
automatically creates a collector for it—no manual registration required.

## Error Handling

The Dynamic Collector handles several error scenarios gracefully:

- Missing `connections.yaml` file: logs warning and continues with empty registry
- Unset `SOLODSHOUSE_VAULT_KEY`: logs warning and continues with statically registered collectors
- Connection configuration errors: logs warning and continues with available collectors

This ensures the system remains functional even when connection configurations
are incomplete or unavailable.

## See Also

- [Collector Pattern](collector-pattern.md) — plugin system with BaseCollector, registry
- [Schema Discovery](schema-discovery.md) — dlt-powered schema inference
- [Connections Layer](../architecture/connections-layer.md) — YAML-driven connection management
- [Medallion Architecture](medallion-architecture.md) — Bronze→Silver→Gold flow
