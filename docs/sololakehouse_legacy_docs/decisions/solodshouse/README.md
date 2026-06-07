# SoloDShouse Architecture Decision Records (ADRs)

> **Origen**: SoloDShouse es un fork de [SoloLakehouse v2.5](https://github.com/Jiahong-Que-9527/SoloLakehouse).
> Los ADRs del proyecto original (ADR-001 a ADR-020) se encuentran en [../](..) y **NO se modifican**.
> Los ADRs aqui documentados (`SDS-XXX`) son decisiones propias de SoloDShouse que divergen del upstream o anaden componentes nuevos.

## Convenciones

- **Prefijo**: `SDS-` distingue nuestras decisiones de las del upstream (`ADR-`)
- **Numeracion**: Continua a partir de donde tenga sentido referenciar el ADR upstream que supersede, o a partir de 021 para decisiones nuevas sin conflicto
- **Supersedes**: Cuando un ADR nuestro contradice uno del upstream, se indica explicitamente con `Supersedes: ADR-XXX`
- **Idioma**: Castellano (el TFM es para UCM Madrid)
- **Fecha**: Formato ISO 8601 (YYYY-MM-DD)

## ADRs que superseden decisiones del upstream

| ADR | Decision | Supersedes | Fecha |
|-----|----------|------------|-------|
| [SDS-002](SDS-002-duckdb-complements-trino.md) | DuckDB complementa Trino (no lo reemplaza) | ADR-002 (Trino over DuckDB) | 2026-06-07 |
| [SDS-007](SDS-007-local-first-over-k8s.md) | Local-first con Docker Compose profiles, no K8s | ADR-007 (K8s+Helm+Terraform) | 2026-06-07 |
| [SDS-014](SDS-014-eliminate-openmetadata.md) | Eliminar OpenMetadata | ADR-014 (OpenMetadata como profile) | 2026-06-07 |
| [SDS-016](SDS-016-spark-on-demand-dbt-duckdb.md) | Spark on-demand + dbt-duckdb | ADR-016 (Spark+dbt-spark) | 2026-06-07 |
| [SDS-019](SDS-019-seaweedfs-replaces-minio.md) | SeaweedFS/floci reemplaza MinIO | ADR-019 (Defer MinIO migration) | 2026-06-07 |

## Decisiones nuevas (sin conflicto directo con upstream)

| ADR | Decision | Fecha |
|-----|----------|-------|
| [SDS-021](SDS-021-evidence-dev-bi.md) | Evidence.dev como BI unico | 2026-06-07 |
| [SDS-022](SDS-022-superset-eliminated.md) | Superset eliminado completamente | 2026-06-07 |
| [SDS-023](SDS-023-no-ollama-llm-inference.md) | Ollama eliminado: llama.cpp/vLLM + LiteLLM | 2026-06-07 |
| [SDS-024](SDS-024-deepagents-agent-harness.md) | deepagents como agent harness | 2026-06-07 |
| [SDS-025](SDS-025-kotaemon-rag.md) | kotaemon para RAG | 2026-06-07 |
| [SDS-026](SDS-026-garak-llm-audit.md) | garak para auditoria LLM | 2026-06-07 |
| [SDS-027](SDS-027-fastmcp-mcp-framework.md) | FastMCP como framework MCP | 2026-06-07 |
| [SDS-028](SDS-028-langfuse-traces-eval.md) | Langfuse para trazas + eval + prompts | 2026-06-07 |
| [SDS-029](SDS-029-monitoring-reduced.md) | Monitorizacion reducida: Prometheus + Alertmanager + Apprise | 2026-06-07 |
| [SDS-030](SDS-030-entso-e-domain.md) | Dominio ENTSO-E reemplaza ECB/DAX | 2026-06-07 |
| [SDS-031](SDS-031-pgvector-over-qdrant.md) | pgvector sobre Qdrant | 2026-06-07 |
| [SDS-032](SDS-032-astro-starlight-docs.md) | Astro Starlight para docs | 2026-06-07 |
| [SDS-033](SDS-032-agt-agent-governance.md) | AGT (Microsoft) para gobernanza de agentes | 2026-06-07 |
| [SDS-034](SDS-034-adala-data-labeling.md) | Adala para data labeling | 2026-06-07 |
| [SDS-035](SDS-035-nginx-portal-hub.md) | Portal nginx como hub central | 2026-06-07 |

## ADRs heredados del upstream (solo lectura)

Los ADRs 001-020 en `docs/decisions/` pertenecen a SoloLakehouse y documentan decisiones del proyecto original. **No se modifican ni superseden localmente** -- cualquier divergencia se documenta aqui con `Supersedes: ADR-XXX`.

Ver: [docs/decisions/README.md](../README.md)

## Principio rector

**Local-first, anti-cloud, minimizar recursos (RAM y euros).** Toda decision debe evaluarse contra:
1. Puede correr en un Mac Studio M4 Max (64GB RAM) sin dependencias cloud?
2. Cual es el coste mensual total (incluyendo VPS staging)?
3. Cuanta RAM anade al stack?
4. Es compatible con el despliegue Docker Compose profiles?

## Formato de ADR

Cada fichero sigue el formato:

```markdown
# SDS-XXX: Titulo de la decision

**Status:** Proposed | Accepted | Deprecated | Superseded
**Date:** YYYY-MM-DD
**Supersedes:** ADR-XXX (si aplica)

## Context
## Decision
## Rationale
## Consequences
## Alternatives Considered
```