# SDS-028: Langfuse para trazas + eval + prompts

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse necesita observabilidad para los flujos de trabajo de agentes LLM: trazas, evaluacion, y gestion de prompts. Se evaluaron varias opciones:

- **Opik (Comet):** Menos features, comunidad mas pequena.
- **LangSmith:** Propio de LangChain, vendor lock-in, requiere cuenta cloud.
- **Langfuse:** Open-source, trazas + eval + gestion de prompts en una sola herramienta.

## Decision

Langfuse se adopta como la herramienta de observabilidad LLM de SoloDShouse.

Langfuse proporciona: tracking end-to-end de trazas para flujos de agentes, scoring de evaluacion para outputs de LLM, versionado y gestion de prompts, y tracking de coste por modelo. El container consume ~300MB de RAM. Reemplaza la necesidad de tener Opik + una herramienta separada de gestion de prompts.

## Rationale

- **Open-source:** Langfuse se puede desplegar localmente via Docker. No hay vendor lock-in ni dependencia de servicios cloud.
- **Trazas + Eval + Prompts:** Es la unica herramienta del mercado que combina estas tres funcionalidades criticas en un solo producto. Esto reduce el numero de herramientas a mantener.
- **Integracion con LiteLLM:** LiteLLM (SDS-023) tiene integracion nativa con Langfuse. Las llamadas a la API se loguean automaticamente como trazas.
- **Cost tracking:** En un TFM que evalua diferentes modelos (7B local, 70B local, Groq API), saber el coste por inferencia es critico para el analisis de viabilidad.

## Consequences

- **Positivas:** Unica herramienta para tres necesidades (trazas, eval, prompts). Integracion automatica con LiteLLM. Despliegue local sin dependencias cloud. Interfaz web para explorar trazas y comparar modelos.
- **Negativas:** ~300MB de RAM adicional. En el VPS de 4GB, Langfuse debe ejecutarse como perfil opcional o con recursos limitados. La base de datos de Langfuse (PostgreSQL) anade otro container.

## Alternatives Considered

- **Opik:** Rechazado por menor madurez de features y comunidad mas pequena. No tiene gestion de prompts integrada.
- **LangSmith:** Rechazado por ser propietario de LangChain, requerir cuenta cloud, y no poder desplegarse localmente de forma sencilla.
- **MLflow + custom:** Rechazado porque MLflow esta orientado a experimentos de ML tradicional, no a trazas de LLM. Requeriria construir toda la infraestructura de observabilidad LLM desde cero.
