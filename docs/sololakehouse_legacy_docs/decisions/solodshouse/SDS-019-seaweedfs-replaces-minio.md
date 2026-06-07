# SDS-019: SeaweedFS/floci reemplaza MinIO

**Status:** Proposed
**Date:** 2026-06-07
**Supersedes:** ADR-019

## Context

ADR-019 aplazo la migracion de MinIO a SeaweedFS hasta despues del freeze de v2.5. Como SoloDShouse es un fork post-v2.5, el freeze ya no aplica. Mas criticamente, MinIO fue archivado en abril de 2026 (ya no se mantiene activamente). SoloDShouse necesita un almacenamiento de objetos compatible S3 mantenido para datos Iceberg, artefactos de MLflow, y almacenamiento de DAGs.

## Decision

Reemplazar MinIO con SeaweedFS o floci S3 como almacenamiento de objetos primario. SeaweedFS (13-150MB RAM) es el candidato primario. floci S3 (13MB binario) es el candidato de respaldo a la espera de pruebas de compatibilidad con Iceberg. MinIO se elimina de todas las configuraciones de Docker Compose. Todas las referencias de endpoint S3 se actualizan desde MinIO al nuevo almacen.

## Rationale

MinIO archivado (abril 2026) significa que no hay parches de seguridad ni correcciones de bugs — inaceptable para una arquitectura de referencia de TFM. SeaweedFS se mantiene activamente, es compatible S3, y mas ligero que MinIO. floci S3 es ultra-ligero (13MB) pero necesita verificacion de compatibilidad con Iceberg. Ambos respetan el principio local-first.

## Consequences

Todos los archivos de configuracion que referencian MINIO_ENDPOINT, S3_ACCESS_KEY, S3_SECRET_KEY deben actualizarse. La ruta del warehouse de Iceberg cambia de `s3://sololakehouse/warehouse/` (MinIO) al nuevo almacen. Las configuraciones del catalogo Hive de Trino y del catalogo Iceberg necesitan un nuevo endpoint S3. `docker-compose.yml` elimina el servicio MinIO, anade el servicio SeaweedFS/floci. `scripts/init-minio.sh` se reemplaza con un script de init para el nuevo almacen.

## Alternatives Considered

1. **Mantener MinIO** — rechazado: archivado, sin parches.
2. **SeaweedFS solo** — candidato primario.
3. **floci S3 solo** — candidato de respaldo a la espera de pruebas.
4. **Garage (S3)** — considerado: bueno pero menos adopcion de comunidad que SeaweedFS.
5. **Solo filesystem local** — rechazado: se pierde la compatibilidad S3 que Trino/Iceberg dependen.
