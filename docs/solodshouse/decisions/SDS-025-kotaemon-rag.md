# SDS-025: kotaemon para RAG

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse necesita RAG (Retrieval-Augmented Generation) para Q&A basado en documentos sobre reportes ENTSO-E, PDFs, y datos del lakehouse. Se evaluaron varias opciones:

- **LlamaIndex vanilla:** Demasiado low-level para una UI usable. Requiere construir toda la interfaz desde cero.
- **LangChain:** Pesado, over-engineered, y su abstraccion de chains introduce complejidad innecesaria.
- **kotaemon:** 25.4k stars, multi-user, citaciones, visor de PDF, construido sobre LlamaIndex.

## Decision

kotaemon se adopta como la UI de RAG de SoloDShouse.

kotaemon proporciona: interfaz multi-user, upload y parsing de documentos, tracking de citaciones, visor de PDF integrado, y esta construido sobre LlamaIndex para la orquestacion RAG. El container consume ~1-2GB de RAM. LlamaIndex permanece como la libreria subyacente de RAG para acceso programatico.

## Rationale

- **UI completa out-of-the-box:** kotaemon incluye una interfaz web para subir documentos, hacer preguntas, y ver las citaciones con el PDF original resaltado. Esto ahorra meses de desarrollo frontend.
- **Citaciones:** Para un TFM academico, la capacidad de rastrear que fragmento de documento origino cada parte de la respuesta es critica. kotaemon implementa esto nativamente.
- **Construido sobre LlamaIndex:** No hay vendor lock-in. La logica de RAG (indexacion, retrieval, ranking) usa LlamaIndex, que es el estandar de facto. Si en el futuro se reemplaza kotaemon, los indices y la logica permanecen.
- **Multi-user:** Aunque SoloDShouse es single-user, la arquitectura multi-user de kotaemon permite separar colecciones de documentos por proyecto o dataset.

## Consequences

- **Positivas:** UI funcional inmediata sin desarrollo frontend. Citaciones integradas. Visor de PDF nativo. Separacion limpia entre UI (kotaemon) y engine (LlamaIndex).
- **Negativas:** ~1-2GB de RAM es significativo para un VPS de 4GB. kotaemon debe ejecutarse como perfil opcional o solo en el entorno de desarrollo (Mac Studio 64GB). En staging, puede estar desactivado por defecto.

## Alternatives Considered

- **LlamaIndex + Streamlit custom:** Rechazado porque requiere construir toda la UI, gestion de documentos, y visor de PDF desde cero. El tiempo de desarrollo no se justifica para un TFM.
- **LangChain + LangServe:** Rechazado por overhead de LangChain y falta de UI integrada. LangServe expone APIs, no una interfaz de usuario.
- **AnythingLLM:** Rechazado porque, aunque popular, su modelo de "workspaces" y su dependencia de vector databases especificas (LanceDB, Pinecone) introduce acoplamiento que no se desea.
