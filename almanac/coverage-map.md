---
title: Coverage Map
summary: Frozen page inventory for the first wiki build of SoloDShouse.
topics: [build, wiki, reference]
sources: []
---

# Coverage Map

Frozen page inventory for the first wiki build. Each page is assigned to a
writing sub-agent in Phase 2. The inventory below is the contract — Phase 2
writes exactly these pages and no more.

## Page Inventory

### concepts/

| Path | Slug | Purpose | Evidence |
|------|------|---------|----------|
| `concepts/collector-pattern.md` | `collector-pattern` | Define the collector plugin system (SDS-043): `BaseCollector`, `register_collector`, `list_sources`, `get_collector`. | `ingestion/collectors/base.py`, `ingestion/collectors/registry.py` |
| `concepts/dynamic-collector.md` | `dynamic-collector` | Define the connection-backed auto-collector (SDS-044): `DynamicCollector`, fetch helpers, module-level auto-registration. | `ingestion/collectors/dynamic.py` |
| `concepts/schema-discovery.md` | `schema-discovery` | Define dlt-powered schema inference: `SchemaDiscovery.discover()`, YAML output, column mapping. | `connections/discovery.py` |
| `concepts/medallion-architecture.md` | `medallion-architecture` | Define Bronze→Silver→Gold medallion with Iceberg: append-only Bronze, full-overwrite Silver/Gold, partitioning strategy. | `ingestion/iceberg_io.py`, `ingestion/iceberg_schemas.py`, `dagster/assets.py` |
| `concepts/iceberg-io.md` | `iceberg-io` | Define the pyiceberg abstraction layer: `get_catalog`, `append_table`, `overwrite_table`, `scan_table`, timestamp downcast. | `ingestion/iceberg_io.py` |

### architecture/

| Path | Slug | Purpose | Evidence |
|------|------|---------|----------|
| `architecture/ingestion-pipeline.md` | `ingestion-pipeline` | Full ingestion flow: collector → validate → Bronze write → Dagster asset → freshness sensor. | `ingestion/collectors/`, `ingestion/bronze_writer.py`, `dagster/assets.py` |
| `architecture/dagster-orchestration.md` | `dagster-orchestration` | Generic asset factory pattern: `make_bronze_assets()`, `dbt_run_asset`, freshness sensor, daily cron schedule. | `dagster/definitions.py`, `dagster/assets.py`, `dagster/resources.py` |
| `architecture/connections-layer.md` | `connections-layer` | YAML-driven connection management: `ConnectionManager`, `FernetVault`, `SchemaDiscovery`, role-based access. | `connections/manager.py`, `connections/vault.py`, `connections/discovery.py` |
| `architecture/docker-compose-profiles.md` | `docker-compose-profiles` | Docker Compose profiles, RAM targets, service map, make commands, SeaweedFS init. | `docker/docker-compose.yml`, `Makefile` |
| `architecture/agent-proxy.md` | `agent-proxy` | FastAPI proxy for deepagents: OpenAI-compatible API → LiteLLM → LangGraph stub. | `agents/deepagents_proxy.py` |

### guides/

| Path | Slug | Purpose | Evidence |
|------|------|---------|----------|
| `guides/add-new-source.md` | `add-new-source` | How to add a new data source: collector file + YAML schema + connection config. | `ingestion/collectors/`, `connections/`, `config/schemas/` |
| `guides/run-pipeline.md` | `run-pipeline` | How to run the Dagster pipeline: `make pipeline`, verify, debug. | `Makefile`, `dagster/` |
| `guides/manage-connections.md` | `manage-connections` | How to add/configure data connections: YAML, vault encryption, role-based access. | `connections/manager.py`, `connections/vault.py` |

### decisions/

| Path | Slug | Purpose | Evidence |
|------|------|---------|----------|
| `decisions/overview.md` | `decisions-overview` | Index of all SDS-XXX decisions with status, context, and consequence summary. | `docs/solodshouse/decisions/` (46 ADR files) |

### reference/

| Path | Slug | Purpose | Evidence |
|------|------|---------|----------|
| `reference/environment-variables.md` | `environment-variables` | All environment variables: object store, Hive Metastore, LiteLLM, vault key, etc. | `ingestion/iceberg_io.py`, `dagster/resources.py`, `connections/manager.py` |
| `reference/iceberg-schemas.md` | `iceberg-schemas` | All Iceberg schema definitions (Bronze/Silver), YAML-driven schema format, partition specs. | `ingestion/iceberg_schemas.py`, `config/schemas/` |

### getting-started

| Path | Slug | Purpose | Evidence |
|------|------|---------|----------|
| `getting-started.md` | `getting-started` | Front door: what SoloDShouse is, how to start, where to read next. | `README.md`, `Makefile`, all wiki pages |
