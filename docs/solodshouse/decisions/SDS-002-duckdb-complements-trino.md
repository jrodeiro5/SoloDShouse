# SDS-002: DuckDB complementa Trino (no lo reemplaza)

**Status:** Proposed
**Date:** 2026-06-07
**Supersedes:** ADR-002

## Context

ADR-002 eligio Trino sobre DuckDB porque Trino demuestra arquitectura lakehouse enterprise y tiene valor de senal para contratacion. SoloDShouse anade una capa de AI/agentes que necesita consultas locales rapidas para exploracion de datos, computo de features de ML, y construccion de contexto para agentes. Trino sigue siendo esencial para consultas federadas y acceso al catalogo Iceberg, pero DuckDB anade valor como complemento in-process.

## Decision

Anadir DuckDB como complemento LOCAL de Trino. DuckDB maneja: analytics in-process para feature engineering de ML, exploracion local de datos en notebooks, agregaciones rapidas sobre archivos Parquet/Iceberg sin round-trip por Trino, dbt-duckdb para transformaciones Silver/Gold. Trino sigue siendo el motor de consulta canonico para: consultas federadas entre catalogos, acceso al catalogo Hive Metastore, UCM Modulo 2 (SQL). Coste de RAM adicional cero — DuckDB es in-process, no necesita contenedor.

## Rationale

ADR-002 fue correcto en que Trino demuestra patrones enterprise. Pero SoloDShouse tiene prioridades diferentes: los agentes de ML necesitan consultas locales rapidas (ms, no round-trips de red). dbt-duckdb es mas ligero que dbt-spark (ADR-016 propuso dbt-spark). DuckDB lee Iceberg/Parquet nativamente. 0 overhead de RAM como libreria Python.

## Consequences

Dos motores de consulta coexisten (Trino para federacion, DuckDB para local). dbt-duckdb reemplaza la propuesta de dbt-spark de ADR-016. Los data engineers deben entender cuando usar cada motor.

## Alternatives Considered

1. **Trino solo** — rechazado: la latencia de red perjudica los workflows de ML/agentes.
2. **DuckDB solo** — rechazado: la justificacion de ADR-002 sigue siendo valida para patrones enterprise.
3. **Spark para local** — rechazado: overhead de 4GB+ RAM on-demand.
