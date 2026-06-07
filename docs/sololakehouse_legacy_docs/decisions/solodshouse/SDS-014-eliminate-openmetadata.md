# SDS-014: Eliminar OpenMetadata

**Status:** Proposed
**Date:** 2026-06-07
**Supersedes:** ADR-014

## Context

ADR-014 introdujo OpenMetadata como overlay opcional de Docker Compose. La baseline v2.5 lo integro en el stack por defecto de `make up`. OpenMetadata requiere MySQL, Elasticsearch, y el propio servidor OpenMetadata (~1.5GB RAM total). SoloDShouse prioriza DS + ML + agentes de AI. Las necesidades de catalogo de datos se cubren con alternativas mas ligeras.

## Decision

Eliminar OpenMetadata completamente. Reemplazar con: dbt docs (auto-generado desde modelos dbt), MetricFlow (capa declarativa de metricas), y Adala (agente de etiquetado de datos para calidad). Estas tres herramientas juntas proporcionan documentacion de datos, definiciones de metricas, y etiquetado de calidad de datos sin el overhead de 1.5GB.

## Rationale

Los 1.5GB RAM de OpenMetadata son ~23% del presupuesto total del stack (6.6GB sin LLM). Para un TFM con un unico usuario, un catalogo enterprise UI es excesivo. dbt docs se auto-genera desde codigo (sin entrada manual). MetricFlow proporciona la capa de metricas que OpenMetadata exponia. Adala proporciona etiquetado de calidad de datos. RAM combinada: ~0MB (todas son CLI/librerias Python, sin contenedores).

## Consequences

No hay UI de catalogo enterprise. El descubrimiento de datos se basa en el sitio estatico de dbt docs. Las definiciones de metricas son code-first (YAML de MetricFlow). Adala es software en estado alpha (riesgo). Se elimina `docker-compose.openmetadata.yml` y los targets relacionados del Makefile.

## Alternatives Considered

1. **Mantener OpenMetadata** — rechazado: 1.5GB RAM para un catalogo single-user es derrochador.
2. **DataHub** — rechazado: aun mas pesado (2GB+).
3. **Amundsen** — rechazado: Lyft lo ha archivado.
4. **dbt docs + MetricFlow solo (sin Adala)** — rechazado: se pierde el etiquetado de calidad de datos.
