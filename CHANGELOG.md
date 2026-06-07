# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

> **SoloDShouse fork begins here.**
> This repo is a fork of SoloLakehouse v2.5. Entries below the `[SoloDShouse Fork]` marker belong to the original project and are preserved for historical context. SoloDShouse changes appear above.
>
> Original docs: [`docs/sololakehouse_legacy_docs/`](docs/sololakehouse_legacy_docs/)
> SoloDShouse ADRs: [`docs/solodshouse/decisions/`](docs/solodshouse/decisions/)

---

## [SoloDShouse Unreleased]

### Added
- `docs/solodshouse/` — SoloDShouse-specific docs space (ADRs, session memory, TFM guide)
- `docs/solodshouse/decisions/` — SDS-XXX ADR series (SDS-002 through SDS-035)
- `docs/solodshouse/session-memory.md` — full stack decisions and context log
- `docs/solodshouse/tfm-architecture-guide.md` — TFM architecture reference

### Changed
- `CLAUDE.md` — rewritten for SoloDShouse identity (Solo Data Science House, TFM UCM Madrid)
- `README.md` — rewritten: new mission, 3-layer architecture, ENTSO-E domain, cost table, UCM coverage
- `CONTRIBUTING.md` — updated for SoloDShouse fork workflow
- `task.md` — updated to SoloDShouse build phases

### Structural
- `docs/sololakehouse_legacy_docs/` — original SoloLakehouse docs preserved intact (read-only)
- Worktrees `magnetic-mile` and `sphenoid-toothbrush` established for agent isolation

### Key Fork Decisions (see SDS ADRs)
- Domain: ECB/DAX (finance) -> ENTSO-E + Open-Meteo (energy) — SDS-030
- SeaweedFS replaces MinIO (MinIO archived Apr 2026) — SDS-019
- DuckDB added as local query engine alongside Trino — SDS-002
- AI agent layer: deepagents + Open WebUI + LiteLLM — SDS-024
- OpenMetadata eliminated; replaced by dbt docs + MetricFlow + Adala — SDS-014
- Superset eliminated; replaced by Evidence.dev — SDS-022
- Spark on-demand compose profile only — SDS-016
- K8s deferred indefinitely; Docker Compose profiles are the deployment model — SDS-007
- pgvector in PostgreSQL replaces standalone Qdrant — SDS-031
- Langfuse for LLM observability; Prometheus + Alertmanager for system metrics — SDS-028/029

---

## [SoloDShouse Fork Point] — forked from SoloLakehouse v2.5 on 2026-06-07

> Everything below this line is original SoloLakehouse history. Preserved unchanged.

## [Unreleased]

### Changed
- Standardized runtime to a single v2.5 execution path (`make pipeline` via Dagster only).
- Promoted OpenMetadata and Superset from optional profiles to default mandatory stack components.
- Updated verification/bootstrap/release docs to reflect v2.5 single-track operations.
- Local Compose durable state uses **bind mounts** under `docker/data/` (with `make prepare-data-dirs`) instead of Docker named volumes; `make clean` removes those directories and purges legacy named volumes when present.

### Fixed
- `scripts/bootstrap-postgres.py` verifies TCP PostgreSQL credentials after Docker-exec bootstrap and aligns the DB role password with `.env` when it has drifted from the data directory (avoids recurring Hive Metastore auth failures).

### Removed
- Legacy host-side pipeline entrypoint (`scripts/run-pipeline.py`).
- Legacy Makefile switches and targets (`PIPELINE_MODE`, `pipeline-v1`, `pipeline-legacy`).

## [v2.5.0] - 2026-03-28 (reference extension)

**Note (2026-04):** Subsequent mainline changes merged OpenMetadata and Superset into the default `make up` path (Compose is always stacked from the `Makefile`; profile-only `make up-openmetadata` / `make up-superset` targets were removed). Local persistence later moved from Docker named volumes to `docker/data/` bind mounts.

### Added
- Apache Iceberg Gold table via Trino (`iceberg.gold.ecb_dax_features_iceberg`) with Hive Metastore as the catalog backend (see [ADR-013](docs/decisions/ADR-013-iceberg-gold-trino.md)).
- Trino `iceberg` catalog configuration template (`config/trino/catalog/iceberg.properties`).
- Optional OpenMetadata 1.5.x compose profile (`make up-openmetadata`) for data catalog, metadata lineage, and Trino connector discovery (see [ADR-014](docs/decisions/ADR-014-openmetadata-optional-profile.md)).
- Optional Apache Superset 6.0.0 compose profile (`make up-superset`) with Trino SQLAlchemy support for SQL and dashboard exploration.
- Automatic Superset bootstrap for two Trino connections: `trino_iceberg_gold` and `trino_hive_default`.
- Integration test for Trino Iceberg table creation and query (`tests/integration/test_trino_iceberg.py`).
- `make verify-openmetadata` target for optional service health-check.
- `make verify-superset` target for optional Superset health-check.

## [v2.0.0] - 2026-03-28

### Added
- Dagster orchestration layer: six software-defined assets (`ecb_bronze`, `dax_bronze`, `ecb_silver`, `dax_silver`, `gold_features`, `ml_experiment`).
- `full_pipeline_job` Dagster job replacing the linear legacy script as the default execution path.
- `daily_pipeline_schedule` (weekdays 06:00 UTC) and `ecb_data_freshness_sensor` (30-minute interval).
- `gold_features_min_rows_check` asset check as a quality gate.
- Dagster webserver and daemon services in Docker Compose; `dagster_storage` PostgreSQL database.
- `dagster/io_managers.py` with `ParquetIOManager` for DataFrame-native asset experiments.
- `make pipeline` defaults to v2 Dagster path (legacy `PIPELINE_MODE` / script path removed in v2.5+).
- Bootstrap script (`scripts/bootstrap-postgres.py`) with Docker-exec and TCP fallback modes.

### Changed
- `make pipeline` now invokes Dagster job by default (was legacy script in v1).
- Harden integration test execution and local release bootstrap.

## [v1.0.0] - 2026-03-26

### Added
- Complete SoloLakehouse core stack with Docker Compose services:
  MinIO, PostgreSQL, Hive Metastore, Trino, and MLflow.
- Ingestion layer with schema validation, bronze quality checks, collectors, and rejected-record handling.
- Transformation layer for Bronze-to-Silver and Silver-to-Gold feature engineering.
- ML training and MLflow experiment evaluation modules.
- End-to-end pipeline and environment verification scripts.
- Unit and integration test scaffolding plus CI workflow for lint, typecheck, and tests.

### Changed
- Upgraded all dependencies to latest stable versions: MinIO RELEASE.2025-09-07,
  PostgreSQL 17, Trino 480, MLflow 3.10.1, PyArrow 23.0.1, Pydantic 2.12.5,
  XGBoost 3.2.0, scikit-learn 1.8.0, structlog 25.5.0, ruff 0.15.7, mypy 1.19.1.
- Standardized project quality tooling with Ruff and MyPy configuration files.
- Expanded repository documentation for deployment, quick validation, and troubleshooting.

### Fixed
- Improved pipeline reliability with retry handling for ingestion steps.
- Added explicit health and readiness checks to reduce startup ambiguity across services.
