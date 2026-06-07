# SDS-031: pgvector sobre Qdrant

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse necesita almacenamiento vectorial para tres casos de uso principales: embeddings RAG (kotaemon/LlamaIndex), memoria de agentes (mem0) y busqueda de similitud de features. PostgreSQL ya esta en el stack (Hive Metastore, MLflow, Dagster). La pregunta es si reutilizar PG con la extension pgvector o anadir un contenedor Qdrant dedicado.

## Decision

Usar pgvector dentro del contenedor PostgreSQL 17 existente. Sin contenedor adicional.

## Rationale

- **Coste de memoria cero.** pgvector es una extension de PostgreSQL, no un servicio aparte. Anadir Qdrant implica ~300MB RAM adicionales en un entorno donde el staging corre en una VPS de 4GB.
- **Stack simplificado.** Ya hay PostgreSQL para Metastore, MLflow y Dagster. Una base de datos menos que operar, backupar y monitorizar.
- **Capacidad suficiente.** pgvector soporta HNSW indexing, distancias cosine/inner product/L2, y millones de vectores. Para embeddings de documentos ENTSO-E (~100K chunks), sobra.
- **PostGIS como bonus.** Se aprovecha el mismo contenedor PG para anadir PostGIS, necesario para datos geoespaciales de energia: limites de red, ubicaciones de plantas, zonas de mercado.

## Consequences

- Positivas: menos contenedores, menos RAM, backup unificado, operaciones simplificadas.
- Negativas: si en el futuro se escala a billones de vectores, pgvector podria no ser suficiente. Migracion a Qdrant o Milvus seria necesaria, pero es un problema para mas alla del TFM.

## Alternatives Considered

- **Qdrant:** ~300MB RAM, API REST propia, buen rendimiento. Rechazado por coste de memoria en VPS 4GB.
- **Milvus:** Mas potente pero mucho mas peso (varios contenedores). Rechazado por complejidad.
- **Chroma:** Ligero pero inmaduro para produccion. Rechazado por falta de HNSW y menor adopcion.
