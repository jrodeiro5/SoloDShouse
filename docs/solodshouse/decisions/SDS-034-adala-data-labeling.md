# SDS-034: Adala para data labeling

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse necesita capacidades de calidad de datos y labeling. A escala ENTSO-E, esto significa: identificar lecturas anomalas, etiquetar eventos energeticos (apagones, picos de demanda), y crear datasets de entrenamiento para modelos ML. Las UIs tradicionales de labeling (Label Studio, Prodigy) son pesadas y excesivas para este caso.

## Decision

Usar Adala como componente de data labeling.

## Rationale

- **LLM-assisted labeling.** Adala usa LLMs para sugerir etiquetas automaticamente, reduciendo el trabajo manual. Un humano revisa y corrige. Ideal para eventos energeticos donde los patrones son reconocibles pero voluminosos.
- **Sin overhead de contenedor.** Libreria Python pura (0 MB adicionales de contenedor). Se ejecuta dentro del entorno de deepagents o como job de Dagster.
- **Integracion con Iceberg.** Via pyiceberg, Adala lee y escribe directamente en las tablas del lakehouse. Los labels se almacenan como tablas Iceberg versionadas.
- **Reemplazo parcial de OpenMetadata.** OpenMetadata proporcionaba data quality y profiling. Adala cubre el labeling, complementado por Great Expectations para validaciones.

## Consequences

- Positivas: labeling rapido con asistencia LLM, integracion nativa con el lakehouse, sin infraestructura extra.
- Negativas: Adala esta en estado alpha. APIs pueden cambiar. Requiere supervision humana para evitar hallucinations en labels criticos (eventos de red).

## Alternatives Considered

- **Label Studio:** UI completa, pero requiere contenedor con base de datos propia. Rechazado por peso (~500MB RAM) y complejidad.
- **Prodigy:** Comercial, bueno pero costoso y pesado. Rechazado por coste y lock-in.
- **Labeling manual con scripts Python:** Rechazado por lentitud y falta de asistencia inteligente.
