---
title: Getting Started
summary: Front door to the SoloDShouse wiki — what the platform is, how to start, and where to read next for common tasks.
topics: [concepts, getting-started]
---

# Getting Started

SoloDShouse is a domain-agnostic, local-first data lakehouse + ML + AI agent
platform. It ships empty and connects to your data sources via a connector
architecture — no bundled collectors, transforms, or schemas.

This wiki documents the durable knowledge needed to work with SoloDShouse:
architectural decisions, multi-file flows, invariants, gotchas, and operational
procedures that code alone cannot convey.

## What SoloDShouse Is

SoloDShouse is a fork of SoloLakehouse v2.5 that has evolved into a
domain-agnostic platform. It runs on a single powerful local machine (64 GB
RAM, Mac Studio M4 Max) plus a low-cost Hetzner VPS for LLM inference.

The platform provides:

- **Lakehouse layer**: PostgreSQL + pgvector, SeaweedFS (S3-compatible), Hive
  Metastore, Trino, DuckDB, Apache Iceberg, dbt, Dagster
- **ML layer**: MLflow, BentoML, XGBoost, LightGBM, scikit-learn
- **Agent + AI layer**: deepagents (LangGraph), FastAPI proxy, Open WebUI,
  LiteLLM, kotaemon, mem0, ToolUniverse, AGT, garak, Adala
- **Observability**: Langfuse, Prometheus, Alertmanager
- **BI/Docs**: Evidence.dev, nginx portal, Astro Starlight, MongoDB

## Quick Start

```bash
make up              # Start core stack + init SeaweedFS buckets + Iceberg namespaces
make pipeline        # Run Dagster full_pipeline_job
make verify          # Health-check all services
make down            # Stop (data preserved under docker/data/)
```

Service endpoints after `make up`:

| Service | URL |
|---------|-----|
| SeaweedFS S3 | http://localhost:8333 |
| Trino UI | http://localhost:8080 |
| MLflow UI | http://localhost:5000 |
| Dagster UI | http://localhost:3000 |

## Where to Read Next

The wiki is organized by page type. Choose your entry point based on what
you need to do:

### I want to understand the system

Start with the **concepts** pages to grasp the mental models:

- [Medallion Architecture](concepts/medallion-architecture.md) — Bronze→Silver→Gold with Iceberg
- [Iceberg I/O](concepts/iceberg-io.md) — pyiceberg abstraction layer
- [Collector Pattern](concepts/collector-pattern.md) — plugin system for data ingestion
- [Dynamic Collector](concepts/dynamic-collector.md) — connection-backed auto-collectors
- [Schema Discovery](concepts/schema-discovery.md) — dlt-powered schema inference

### I need to change how the system works

Read the **architecture** pages to understand ownership and flow:

- [Ingestion Pipeline](architecture/ingestion-pipeline.md) — full data flow
- [Dagster Orchestration](architecture/dagster-orchestration.md) — pipeline orchestration
- [Connections Layer](architecture/connections-layer.md) — YAML-driven connection management
- [Docker Compose Profiles](architecture/docker-compose-profiles.md) — service deployment
- [Agent Proxy](architecture/agent-proxy.md) — FastAPI proxy for deepagents

### I need to add something new

Follow the **guides** for task-oriented instructions:

- [Add New Source](guides/add-new-source.md) — how to add a data source
- [Run Pipeline](guides/run-pipeline.md) — how to run and debug pipelines
- [Manage Connections](guides/manage-connections.md) — how to configure data connections

### I need to understand a past decision

Browse the **decisions** index:

- [Decisions Overview](decisions/overview.md) — all SDS-XXX decisions with status and context

### I need exact lookup material

Consult the **reference** pages:

- [Environment Variables](reference/environment-variables.md) — all env vars with defaults
- [Iceberg Schemas](reference/iceberg-schemas.md) — all schema definitions and formats

## Trust Order

When code and the wiki disagree, trust the code. When the wiki and ordinary
documentation disagree, trust the wiki. The wiki is maintained more regularly
and is more authoritative than ordinary repository documentation.

## See Also

- [Medallion Architecture](concepts/medallion-architecture.md)
- [Collector Pattern](concepts/collector-pattern.md)
- [Ingestion Pipeline](architecture/ingestion-pipeline.md)
- [Docker Compose Profiles](architecture/docker-compose-profiles.md)
- [Decisions Overview](decisions/overview.md)
