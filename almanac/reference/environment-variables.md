---
title: Environment Variables
summary: Reference for all environment variables used by SoloDShouse services, organized by subsystem.
topics: [reference, configuration, operations]
---

# Environment Variables

This reference documents all environment variables used by SoloDShouse
services. Variables are organized by subsystem and include defaults,
descriptions, and usage notes.

## Object Store (SeaweedFS)

| Variable | Default | Description |
|----------|---------|-------------|
| `OBJECT_STORE_ENDPOINT` | `http://localhost:8333` | SeaweedFS S3-compatible endpoint |
| `OBJECT_STORE_ACCESS_KEY` | `solodshouse` | S3 access key ID |
| `OBJECT_STORE_SECRET_KEY` | `solodshouse123` | S3 secret access key |
| `DATA_BUCKET` | `solodshouse-data` | Primary data bucket name |
| `WAREHOUSE_URI` | `s3a://solodshouse-data/warehouse/` | Iceberg warehouse URI (Hadoop format) |

**Note**: `WAREHOUSE_URI` uses `s3a://` (Hadoop format) but PyIceberg converts
to `s3://` internally. Use `OBJECT_STORE_*` variables in new code; `MINIO_*`
variables are legacy and should not be used.

## PostgreSQL

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_USER` | `solodshouse` | PostgreSQL username |
| `POSTGRES_PASSWORD` | `solodshouse` | PostgreSQL password |
| `POSTGRES_DB` | `solodshouse` | Default PostgreSQL database |
| `EXTRA_POSTGRES_DATABASES` | (none) | Additional databases to create (comma-separated) |

## Hive Metastore

| Variable | Default | Description |
|----------|---------|-------------|
| `HIVE_METASTORE_URI` | `thrift://localhost:9083` | Hive Metastore Thrift endpoint |

## Trino

| Variable | Default | Description |
|----------|---------|-------------|
| `TRINO_URL` | `http://localhost:8080` | Trino REST API endpoint |

## MLflow

| Variable | Default | Description |
|----------|---------|-------------|
| `MLFLOW_TRACKING_URI` | `http://localhost:5000` | MLflow tracking server URL |
| `MLFLOW_ARTIFACT_BUCKET` | `solodshouse-mlflow` | MLflow artifact storage bucket |
| `MLFLOW_ARTIFACT_ROOT` | `s3://solodshouse-mlflow/artifacts/` | MLflow artifact storage root |

## Agent Proxy

| Variable | Default | Description |
|----------|---------|-------------|
| `LITELLM_BASE_URL` | `http://litellm:4000` | LiteLLM gateway endpoint |
| `LITELLM_API_KEY` | (empty) | API key for agent proxy authentication |

## Connection Vault

| Variable | Default | Description |
|----------|---------|-------------|
| `SOLODSHOUSE_VAULT_KEY` | (required) | Fernet encryption key for connection secrets |

**Required**: This variable must be set for FernetVault to function. Generate
a key with:

```bash
python -c "from connections.vault import generate_key; print(generate_key())"
```

## Dagster

| Variable | Default | Description |
|----------|---------|-------------|
| `DAGSTER_HOME` | (none) | Dagster home directory (state persistence) |
| `DAGSTER_PRODUCTION_CHECK` | `1` | Enable production checks |

## Docker Compose

| Variable | Default | Description |
|----------|---------|-------------|
| `COMPOSE_FILE` | `docker/docker-compose.yml` | Docker Compose file path |
| `COMPOSE_STACK` | `-f docker/docker-compose.yml` | Docker Compose stack flag |
| `ENV_FILE` | `.env` | Environment file path |

## Scripts

| Variable | Default | Description |
|----------|---------|-------------|
| `DAGSTER_JOB` | `full_pipeline_job` | Default Dagster job name |
| `SUPERSET_DB_NAME` | `superset_metadata` | Superset metadata database name |

## Usage Notes

### PyIceberg Catalog Creation

The `get_catalog()` function in `ingestion/iceberg_io.py` reads these variables:

```python
storage_cfg = get_storage_config()
store_ep = os.environ.get("OBJECT_STORE_ENDPOINT", "http://localhost:8333")
raw_warehouse = storage_cfg.warehouse_uri
effective_warehouse = raw_warehouse.replace("s3a://", "s3://")

props = {
    "uri": os.environ.get("HIVE_METASTORE_URI", "thrift://localhost:9083"),
    "warehouse": effective_warehouse,
    "s3.endpoint": store_ep,
    "s3.access-key-id": os.environ.get("S3_ACCESS_KEY", os.environ.get("OBJECT_STORE_ACCESS_KEY", "solodshouse")),
    "s3.secret-access-key": os.environ.get("S3_SECRET_KEY", os.environ.get("OBJECT_STORE_SECRET_KEY", "solodshouse123")),
    "s3.path-style-access": "true",
}
```

### Connection Manager

The `ConnectionManager` class in `connections/manager.py` reads:

- `SOLODSHOUSE_VAULT_KEY` for FernetVault initialization
- `${ENV_VAR}` placeholders in YAML configuration files

### Agent Proxy

The `deepagents_proxy.py` module reads:

- `LITELLM_BASE_URL` for LiteLLM gateway endpoint
- `LITELLM_API_KEY` for authentication

### Dagster Resources

The `PipelineConfigResource` in `dagster/resources.py` reads:

- `MLFLOW_TRACKING_URI` for MLflow tracking URL
- `TRINO_URL` for Trino REST API endpoint

## See Also

- [Docker Compose Profiles](../architecture/docker-compose-profiles.md) — service deployment
- [Connections Layer](../architecture/connections-layer.md) — YAML-driven connection management
- [Iceberg I/O](../concepts/iceberg-io.md) — pyiceberg abstraction
