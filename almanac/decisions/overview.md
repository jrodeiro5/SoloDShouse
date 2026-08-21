---
title: Decisions Overview
summary: Index of all SDS-XXX architectural decisions for SoloDShouse, with status, context, and consequence summaries.
topics: [decisions, architecture, reference]
---

# Decisions Overview

This page indexes all architectural decisions for SoloDShouse, documented as
SDS-XXX (SoloDShouse Decision) files in `docs/solodshouse/decisions/`.

These decisions record architecturally meaningful choices that affect the
structure of the system, dependencies, interfaces, workflows, persistence,
provider boundaries, construction techniques, or important operational
behavior.

## Decision Index

### Infrastructure Decisions

| ID | Title | Status | Summary |
|----|-------|--------|---------|
| [SDS-007](docs/solodshouse/decisions/SDS-007-local-first-over-k8s.md) | Local-first over K8s | Active | Reject Kubernetes; use Docker Compose profiles for local-first deployment |
| [SDS-016](docs/solodshouse/decisions/SDS-016-spark-on-demand-dbt-duckdb.md) | Spark on-demand + dbt-duckdb | Active | Spark only as on-demand compose profile; dbt-duckdb for local SQL |
| [SDS-019](docs/solodshouse/decisions/SDS-019-seaweedfs-replaces-minio.md) | SeaweedFS replaces MinIO | Active | Replace MinIO with SeaweedFS (S3-compatible) for object storage |
| [SDS-036](docs/solodshouse/decisions/SDS-036-orbstack-docker-runtime.md) | OrbStack Docker runtime | Active | Use OrbStack instead of Docker Desktop on macOS for better performance |
| [SDS-037](docs/solodshouse/decisions/SDS-037-vps-gateway-role.md) | VPS gateway role | Active | Hetzner VPS acts as gateway for LLM inference, not primary compute |
| [SDS-046](docs/solodshouse/decisions/SDS-046-skypilot-gpu-scheduler-rejected.md) | SkyPilot GPU scheduler rejected | Rejected | Reject SkyPilot; use direct Docker Compose for GPU workloads |

### Data Platform Decisions

| ID | Title | Status | Summary |
|----|-------|--------|---------|
| [SDS-002](docs/solodshouse/decisions/SDS-002-duckdb-complements-trino.md) | DuckDB complements Trino | Active | DuckDB for local queries, Trino for federated SQL |
| [SDS-014](docs/solodshouse/decisions/SDS-014-eliminate-openmetadata.md) | Eliminate OpenMetadata | Active | Remove OpenMetadata; use dbt docs + MetricFlow + Adala for data governance |
| [SDS-021](docs/solodshouse/decisions/SDS-021-evidence-dev-bi.md) | Evidence.dev BI | Proposed | Use Evidence.dev (markdown-first static BI) as the sole BI tool; deployed in the bi compose profile |
| [SDS-022](docs/solodshouse/decisions/SDS-022-superset-eliminated.md) | Superset eliminated | Active | Remove Apache Superset; Evidence.dev covers BI needs |
| [SDS-023](docs/solodshouse/decisions/SDS-023-no-ollama-llm-inference.md) | No Ollama LLM inference | Active | Use llama.cpp/vLLM + LiteLLM instead of Ollama for LLM inference |
| [SDS-025](docs/solodshouse/decisions/SDS-025-kotaemon-rag.md) | Kotaemon RAG | Active | Use kotaemon for RAG UI with multi-user support and citations |
| [SDS-026](docs/solodshouse/decisions/SDS-026-garak-llm-audit.md) | Garak LLM audit | Active | Use garak (NVIDIA) for LLM vulnerability scanning (audit-only) |
| [SDS-027](docs/solodshouse/decisions/SDS-027-fastmcp-mcp-framework.md) | FastMCP MCP framework | Active | Use FastMCP for MCP tool implementation |
| [SDS-028](docs/solodshouse/decisions/SDS-028-langfuse-traces-eval.md) | Langfuse traces + eval | Active | Use Langfuse for LLM traces, evaluation, and prompt management |
| [SDS-029](docs/solodshouse/decisions/SDS-029-monitoring-reduced.md) | Monitoring reduced | Active | Reduce monitoring overhead; use Prometheus + Alertmanager for system metrics |
| [SDS-031](docs/solodshouse/decisions/SDS-031-pgvector-over-qdrant.md) | pgvector over Qdrant | Active | Use pgvector instead of Qdrant for vector storage in PostgreSQL |
| [SDS-032](docs/solodshouse/decisions/SDS-032-astro-starlight-docs.md) | Astro Starlight docs | Active | Use Astro Starlight for documentation site generation |
| [SDS-033](docs/solodshouse/decisions/SDS-033-agt-agent-governance.md) | AGT agent governance | Active | Use Microsoft AGT for agent governance and policy enforcement |
| [SDS-034](docs/solodshouse/decisions/SDS-034-adala-data-labeling.md) | Adala data labeling | Active | Use Adala for automated data labeling and annotation |
| [SDS-035](docs/solodshouse/decisions/SDS-035-nginx-portal-hub.md) | Nginx portal hub | Active | Use nginx as central portal hub for all services |
| [SDS-038](docs/solodshouse/decisions/SDS-038-llm-gateway-model-selection.md) | LLM gateway model selection | Active | Use LiteLLM as unified LLM gateway with model selection |
| [SDS-039](docs/solodshouse/decisions/SDS-039-pii-detection-presidio.md) | PII detection Presidio | Active | Use Microsoft Presidio for PII detection and redaction |
| [SDS-040](docs/solodshouse/decisions/SDS-040-dataset-strategy-ai-energy-cost.md) | Dataset strategy AI energy cost | Active | Use AI energy cost datasets for carbon-aware computing |
| [SDS-041](docs/solodshouse/decisions/SDS-041-medallion-schema-dbt-design.md) | Medallion schema dbt design | Active | Use medallion architecture with dbt for schema design |
| [SDS-042](docs/solodshouse/decisions/SDS-042-entsoe-historical-data-strategy.md) | ENTSO-E historical data strategy | Active | Use ENTSO-E historical data for energy sector domain |
| [SDS-043](docs/solodshouse/decisions/SDS-043-domain-agnostic-platform.md) | Domain-agnostic platform | Active | Platform is domain-agnostic; no bundled collectors or schemas |
| [SDS-044](docs/solodshouse/decisions/SDS-044-connection-layer-dlt.md) | Connection layer dlt | Active | Use dlt for connection layer with schema discovery |
| [SDS-045](docs/solodshouse/decisions/SDS-045-mirage-vfs-agent-layer.md) | Mirage VFS agent layer | Active | Use Mirage VFS for agent file system operations |

### Application Decisions

| ID | Title | Status | Summary |
|----|-------|--------|---------|
| [SDS-024](docs/solodshouse/decisions/SDS-024-deepagents-agent-harness.md) | Deepagents agent harness | Active | Use deepagents (LangGraph) as agent harness |
| [SDS-030](docs/solodshouse/decisions/SDS-030-entso-e-domain.md) | ENTSO-E domain | Active | Default domain is ENTSO-E for energy sector use case |

## Legacy Decisions (SoloLakehouse)

The following decisions are from the original SoloLakehouse project and are
preserved as read-only historical reference:

- ADR-001 through ADR-020 in `docs/sololakehouse_legacy_docs/decisions/`

These decisions are not modified but may be referenced for context when
understanding the evolution of SoloDShouse.

## Decision Format

Each decision file follows this format:

```markdown
# SDS-XXX: Decision Title

## Status
Active | Superseded | Rejected

## Context
What are the forces at play? What are the tradeoffs?

## Decision
What is the chosen path? What does the project do?

## Consequences
What becomes easier? What becomes harder? What are the risks?
```

## See Also

- [Medallion Architecture](../concepts/medallion-architecture.md) — Bronze→Silver→Gold
- [Docker Compose Profiles](../architecture/docker-compose-profiles.md) — service deployment
- [Environment Variables](../reference/environment-variables.md) — all env vars
