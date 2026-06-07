# SDS-022: Superset eliminado completamente

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloLakehouse v2.5 incluye Superset en el stack por defecto (mergeado desde el perfil opcional del ADR-014). Superset anade ~2GB de RAM, requiere Redis, y su UI de construccion de charts asume multiples usuarios con diferentes roles. SoloDShouse es un proyecto single-user.

Incluso el SQL Lab de Superset es redundante. Las necesidades de queries ad-hoc estan cubiertas por el CLI de Trino y DuckDB, herramientas que ya forman parte del stack base. Mantener Superset como perfil opcional sigue implicando complejidad en el docker-compose y en la documentacion.

## Decision

Superset se elimina por completo del stack. No permanece ni como perfil opcional.

Evidence.dev cubre la generacion de reportes y dashboards estaticos. El CLI de Trino y DuckDB cubren las necesidades de queries ad-hoc interactivas. No hay funcionalidad de Superset que no tenga un reemplazo mas ligero en el nuevo stack.

## Rationale

- **Eliminacion de deuda tecnica:** Superset introduce dependencias (Redis, PostgreSQL dedicada, workers Celery) que complican el despliegue y el mantenimiento.
- **Principio anti-cloud:** Superset asume infraestructura de datos enterprise. SoloDShouse asume una maquina local o un VPS modesto.
- **Single-user:** No hay audiencia para el modelo multi-tenant de Superset.
- **Redundancia:** SQL Lab es un SQL editor web. El usuario de SoloDShouse puede ejecutar `trino-cli` o `duckdb` directamente con mejor performance y sin overhead de red.

## Consequences

- **Positivas:** Eliminacion de ~2GB de RAM y 3 containers (Superset, Redis, PostgreSQL-Analytics). Simplificacion del docker-compose.yml. Reduccion del tiempo de build y del surface de seguridad.
- **Negativas:** Los usuarios que esperen una UI tipo "Excel online" para explorar datos no la encontraran. Deben adaptarse a Evidence.dev (markdown + SQL) o a CLI interactivo.

## Alternatives Considered

- **Mantener Superset como opcional:** Rechazado porque, incluso como perfil opcional, requiere mantener configuracion, variables de entorno, y documentacion. La complejidad residual no justifica la funcionalidad.
- **Mantener solo SQL Lab:** Rechazado porque SQL Lab requiere todo el stack de Superset (Redis, DB, workers) para funcionar. No es modularizable.
