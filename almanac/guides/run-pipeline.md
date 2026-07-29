---
title: Run Pipeline
summary: How to run the Dagster pipeline, verify service health, and debug common issues.
topics: [guides, orchestration, dagster, operations]
---

# Run Pipeline

This guide explains how to run the Dagster pipeline, verify service health,
and debug common issues. The pipeline processes data from external sources
through Bronze, Silver, and Gold layers.

## Quick Start

### Start the Stack

```bash
make up
```

This command:
1. Prepares data directories under `docker/data/`
2. Starts PostgreSQL and SeaweedFS
3. Waits for PostgreSQL to be ready (90s timeout)
4. Bootstraps additional databases (MLflow, etc.)
5. Builds and starts all services
6. Initializes SeaweedFS buckets
7. Initializes Iceberg namespaces (bronze, silver, gold)

Expected output:
```
SoloDShouse is ready.
  SeaweedFS S3:   http://localhost:8333
  Trino UI:       http://localhost:8080
  MLflow UI:      http://localhost:5000
  Dagster UI:     http://localhost:3000
```

### Stop the Stack

```bash
make down
```

Stops all services while preserving data under `docker/data/`.

### Clean Reset

```bash
make clean
```

Stops the stack, deletes all data directories, and recreates them. Use for
complete reset scenarios.

## Running the Pipeline

### Full Pipeline

```bash
make pipeline
```

Executes the `full_pipeline_job` Dagster job, which runs all Bronze assets
followed by the dbt transformation asset.

### Bronze-Only Pipeline

```bash
make pipeline DAGSTER_JOB=bronze_only_job
```

Runs only the Bronze layer assets, skipping dbt transformations. Useful for
development and testing.

### Specific Source

```bash
make pipeline DAGSTER_JOB=my_source_bronze
```

Runs a specific source's Bronze asset. Replace `my_source` with the actual
source name.

## Monitoring

### Dagster UI

Access the Dagster UI at http://localhost:3000 to:

- View pipeline runs and their status
- Inspect asset graphs and dependencies
- Monitor execution logs and metrics
- Trigger manual runs

### Logs

Pipeline logs are available in:

- **Dagster UI**: Individual run logs under "Runs" tab
- **Docker logs**: `docker logs <container_name>` for service-specific logs
- **File logs**: Check `docker/data/dagster/` for persisted state

## Verification

### Health Check

```bash
make verify
```

Runs `scripts/verify-setup.py` to check all services are running and
responsive. This script:

- Checks PostgreSQL connectivity
- Verifies SeaweedFS S3 endpoint
- Tests Hive Metastore connection
- Validates Trino accessibility
- Confirms MLflow availability

### Service Endpoints

| Service | Port | URL |
|---------|------|-----|
| PostgreSQL | 5432 | `postgresql://user:pass@localhost:5432/db` |
| SeaweedFS S3 | 8333 | `http://localhost:8333` |
| Hive Metastore | 9083 | `thrift://localhost:9083` |
| Trino | 8080 | `http://localhost:8080` |
| MLflow | 5000 | `http://localhost:5000` |
| Dagster | 3000 | `http://localhost:3000` |

## Debugging

### Common Issues

#### PostgreSQL Not Ready

**Symptom**: `make up` fails with "Postgres did not become ready in time"

**Solution**:
1. Check PostgreSQL logs: `docker logs sds-postgres`
2. Verify port 5432 is not in use: `lsof -i :5432`
3. Ensure `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB` are set in `.env`

#### SeaweedFS Initialization Fails

**Symptom**: Buckets not created, S3 operations fail

**Solution**:
1. Check SeaweedFS logs: `docker logs sds-seaweedfs`
2. Verify port 8333 is available
3. Ensure `docker/data/seaweedfs/` directory exists and is writable

#### Hive Metastore Connection Issues

**Symptom**: Iceberg catalog creation fails with connection errors

**Solution**:
1. Check Hive Metastore logs: `docker logs sds-hive-metastore`
2. Verify `HIVE_METASTORE_URI` is set correctly (default: `thrift://localhost:9083`)
3. Ensure port 9083 is accessible

#### Dagster Pipeline Failures

**Symptom**: Pipeline runs fail with asset errors

**Solution**:
1. Check Dagster UI for specific asset failures
2. Review asset logs for error details
3. Verify collector files are properly registered
4. Check schema files exist in `config/schemas/`

#### Iceberg Table Creation Errors

**Symptom**: `NoSuchTableError` or `NamespaceAlreadyExistsError`

**Solution**:
1. Check Iceberg namespace exists: `SELECT * FROM information_schema.schemata`
2. Verify schema files in `config/schemas/` match expected format
3. Check `ingestion/iceberg_io.py` for timestamp downcast issues

### Manual Pipeline Execution

For debugging, execute pipeline steps manually:

```python
from ingestion.iceberg_io import get_catalog, append_table, scan_table
from ingestion.collectors.registry import get_collector, list_sources

# Get catalog
catalog = get_catalog()

# List sources
sources = list_sources()

# Get specific collector
collector_cls = get_collector("my_source")

# Execute collector
result = collector_cls(catalog).collect()
print(result)  # {"valid": 100, "rejected": 0}

# Scan Bronze table
df = scan_table(catalog, "bronze", "my_source")
print(df.head())
```

## Make Commands Reference

| Command | Description |
|---------|-------------|
| `make up` | Start core stack + init SeaweedFS buckets + Iceberg namespaces |
| `make down` | Stop (data preserved under docker/data/) |
| `make pipeline` | Run Dagster full_pipeline_job |
| `make dagster-ui` | Open Dagster UI (http://localhost:3000) |
| `make verify` | Health-check all services |
| `make test` | Unit tests (pytest, no Docker needed) |
| `make lint` | ruff |
| `make typecheck` | mypy on ingestion/, transformations/, ml/, scripts/, dagster/ |
| `make clean` | Stop + delete docker/data/ + purge volumes |

## See Also

- [Ingestion Pipeline](../architecture/ingestion-pipeline.md) — full data flow
- [Dagster Orchestration](../architecture/dagster-orchestration.md) — pipeline orchestration
- [Docker Compose Profiles](../architecture/docker-compose-profiles.md) — service deployment
- [Add New Source](add-new-source.md) — how to add data sources
