# SDS-024: deepagents como agent harness

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse necesita un framework de agentes para que los agentes de IA interactuen con el lakehouse. Se evaluaron varias opciones del ecosistema actual:

- **LangGraph:** Low-level, requiere boilerplate significativo para casos de uso comunes.
- **deer-flow:** 70.6k stars, multi-agent, pero consume ~16GB RAM y esta orientado a flujos de trabajo enterprise complejos.
- **agno:** 25k+ stars, plataforma AgentOS, mas pesado de lo necesario para un TFM.
- **deepagents:** 24k stars, ~200MB, basado en LangGraph pero batteries-included, con integracion nativa al stack de analitica.

## Decision

deepagents se adopta como el agent harness de SoloDShouse.

deepagents proporciona: tool calling, gestion de memoria, razonamiento multi-step, e integracion con el stack de analitica. Consume aproximadamente ~200MB de RAM. Un proxy FastAPI traduce llamadas API de formato OpenAI al formato nativo de deepagents (deepagents no expone una API compatible con OpenAI de forma nativa).

## Rationale

- **Batteries-included sobre LangGraph:** deepagents esta construido sobre LangGraph pero abstrae la complejidad de grafos de estados para casos de uso estandar. No se reinventa, se encapsula.
- **Integracion con analitica:** deepagents tiene integraciones nativas con herramientas de observabilidad y trazas, lo que alinea con el stack de Langfuse (SDS-028).
- **RAM razonable:** ~200MB es aceptable para un VPS de 4GB, especialmente comparado con los 16GB de deer-flow.
- **Tool calling robusto:** deepagents gestiona el ciclo completo de tool calling: el LLM decide que herramienta usar, el framework ejecuta la herramienta, y el resultado vuelve al LLM.

## Consequences

- **Positivas:** Framework maduro con comunidad activa. Integracion nativa con el ecosistema de trazas y evaluacion. No requiere escribir grafos de LangGraph manualmente para casos simples.
- **Negativas:** deepagents no expone API OpenAI-compatible nativamente. Requiere un proxy FastAPI para que LiteLLM (SDS-023) y otros clientes OpenAI puedan comunicarse. Esto anade una capa de traduccion que debe mantenerse.

## Alternatives Considered

- **LangGraph puro:** Rechazado porque requiere demasiado boilerplate para un TFM. deepagents es esencialmente una opinionated layer sobre LangGraph que acelera el desarrollo.
- **deer-flow:** Rechazado por consumo excesivo de RAM (~16GB) y orientacion a flujos multi-agent enterprise que exceden el alcance de un TFM.
- **agno:** Rechazado porque es una plataforma completa (AgentOS) con overhead de infraestructura que no se justifica para un proyecto academico single-user.
- **CrewAI:** Rechazado porque, aunque popular, su modelo de "crews" y "tasks" es mas orientado a flujos de trabajo colaborativos simulados que a interaccion directa con lakehouse.
