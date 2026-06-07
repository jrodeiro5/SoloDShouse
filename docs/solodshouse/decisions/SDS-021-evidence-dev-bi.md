# SDS-021: Evidence.dev como BI unico

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloLakehouse v2.5 utiliza Apache Superset como herramienta de BI. Superset es pesado (~2GB container), orientado a entornos enterprise, y excesivo para un TFM con un unico usuario. SoloDShouse necesita una solucion de BI ligera que genere reportes a partir de queries SQL y los presente como un sitio estatico.

Evidence.dev es una herramienta markdown-first que genera sitios estaticos a partir de SQL. Se integra nativamente con DuckDB y Trino, y su container consume aproximadamente ~200MB de RAM. Esto la convierte en una opcion viable para el principio local-first de SoloDShouse.

## Decision

Evidence.dev reemplaza a Superset como la unica herramienta de BI del stack.

Evidence.dev se conecta a Trino para queries federadas y a DuckDB para analitica local. Produce reportes basados en markdown que se despliegan como un sitio estatico. No se incluye Superset, Lightdash, ni Metabase en ninguna modalidad.

## Rationale

- **Minimizacion de RAM:** Evidence.dev (~200MB) vs Superset (~2GB). En un entorno de staging con 4GB (Hetzner CPX21), esta diferencia es critica.
- **Simplicidad operativa:** No requiere Redis ni base de datos propia. Los reportes son archivos markdown con queries SQL embebidas.
- **Alineacion con local-first:** Genera sitios estaticos que pueden servirse localmente sin dependencias externas.
- **Integracion nativa:** DuckDB y Trino son first-class citizens en Evidence.dev.
- **Single-user:** El modelo de Superset asume multiples usuarios, roles y permisos. Evidence.dev asume un analista individual escribiendo SQL y markdown.

## Consequences

- **Positivas:** Reduccion de ~1.8GB de RAM en el stack base. Eliminacion de dependencias Redis y PostgreSQL dedicadas para Superset. Los reportes son versionables en git (markdown + SQL).
- **Negativas:** No hay drag-and-drop chart builder. Los usuarios deben escribir SQL y markdown. No hay dashboards interactivos con filtros dinamicos complejos (aunque Evidence.dev soporta parametros basicos).

## Alternatives Considered

- **Superset (status quo):** Rechazado por consumo excesivo de RAM y complejidad operativa para un TFM single-user.
- **Lightdash:** Rechazado porque, aunque ligero, requiere dbt Cloud o dbt Core con configuracion adicional, y su modelo de semantic layer es overkill para este contexto.
- **Metabase:** Rechazado porque, aunque mas ligero que Superset, sigue siendo un application server con base de datos propia (~500MB) y su modelo de preguntas/guardados no aporta valor sobre Evidence.dev para este caso de uso.
