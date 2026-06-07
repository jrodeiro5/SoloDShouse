# SDS-016: Spark on-demand + dbt-duckdb

**Status:** Proposed
**Date:** 2026-06-07
**Supersedes:** ADR-016

## Context

ADR-016 propuso migrar las transformaciones Silver/Gold de pandas a Spark + dbt-spark, haciendo que Trino fuera solo para consultas. SoloDShouse necesita Spark solo para demostraciones del Modulo 11 de UCM (Big Data), no como motor de transformacion por defecto. El principio de minimizar RAM implica que Spark (4GB por executor) no debe ejecutarse continuamente.

## Decision

Usar dbt-duckdb como motor de transformacion por defecto para Silver/Gold. Usar dbt-duckdb con DuckDB como motor de ejecucion local para todo el trabajo de transformacion. Spark se ejecuta solo como un profile on-demand de Docker Compose (`+spark`, +4GB) para demostraciones del Modulo 11 de UCM. Trino conserva su doble rol: consultas federadas Y verificacion de transformaciones (no solo consultas).

## Rationale

dbt-duckdb es zero-infraestructura (in-process), perfecto para una sola maquina. DuckDB maneja volumenes de transformacion (datos ENTSO-E son escala GB, no TB). dbt-spark requiere un cluster Spark en ejecucion (4GB+ RAM continuos). SoloDShouse es local-first — un overhead continuo de 4GB viola el principio. DuckDB lee/escribe Iceberg via pyiceberg, manteniendo compatibilidad de formato con Trino.

## Consequences

dbt-duckdb es la ruta principal de transformacion. El profile de Spark existe pero es opt-in. dbt-duckdb tiene algunas diferencias de dialecto SQL vs dbt-spark. El Modulo 11 de UCM (Big Data) usa el profile de Spark solo para demostraciones. ADR-020 (Iceberg en todas las capas) se preserva — dbt-duckdb escribe Iceberg via pyiceberg.

## Alternatives Considered

1. **dbt-spark como propuso ADR-016** — rechazado: overhead continuo de 4GB+.
2. **Transformaciones puras con pandas** — rechazado: sin capa de transformacion SQL, mas dificil de testear.
3. **SQLMesh** — rechazado: MetricFlow es prototipo, no listo para produccion.
4. **dbt-trino** — considerado: Trino puede ejecutar dbt, pero anade latencia de red para transformaciones locales.
