# SDS-033: AGT (Microsoft) para gobernanza de agentes

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse ejecuta agentes de IA (deepagents) que interactuan con datos del lakehouse. Surgen preocupaciones de gobernanza: que tools pueden invocar los agentes, a que datos pueden acceder, rate limiting, y audit trails. Sin control, un agente podria consultar tablas sensibles o hacer peticiones excesivas a APIs externas (ENTSO-E).

## Decision

Usar AGT (Agent Governance Toolkit, Microsoft) como capa de gobernanza de agentes.

## Rationale

- **Policy enforcement.** AGT actua como middleware entre deepagents y la ejecucion de tools. Permite definir politicas en YAML: que tools puede usar cada agente, que tablas puede consultar, limites de rate.
- **Audit logging.** Todas las decisiones de politica se loguean. Complementa Langfuse trace tracking con un registro de gobernanza explicito.
- **Ligero.** Libreria Python (~50MB), sin contenedor adicional. Se integra en el runtime de deepagents.
- **Patron middleware.** No requiere cambiar la arquitectura de agentes existente. Se inserta entre el agente y el tool executor.

## Consequences

- Positivas: control granular de acceso, auditoria completa, prevencion de abuso de APIs y datos.
- Negativas: AGT es relativamente nuevo (4.1k stars). Menos maduro que soluciones enterprise. Politicas YAML requieren mantenimiento manual.

## Alternatives Considered

- **Control manual en codigo:** Implementar checks ad-hoc en cada tool. Rechazado por fragilidad y falta de centralizacion.
- **OPA (Open Policy Agent):** Mas potente y generico, pero requiere contenedor sidecar y Rego. Rechazado por complejidad innecesaria para un TFM.
- **Sin gobernanza:** Rechazado por riesgo obvio de acceso no controlado a datos de mercado de energia.
