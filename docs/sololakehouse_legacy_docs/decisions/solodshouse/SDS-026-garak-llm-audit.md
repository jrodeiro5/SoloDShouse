# SDS-026: garak para auditoria LLM

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse ejecuta LLMs locales para flujos de agentes. Antes de desplegar cualquier modelo a produccion, los LLMs necesitan auditoria de seguridad para: prompt injection, hallucination, data leakage, y bias.

garak (desarrollado por NVIDIA, 8k stars) es una herramienta disenada especificamente para escaneo de vulnerabilidades en LLMs. Es una herramienta CLI (0 MB cuando esta inactiva, se ejecuta on-demand).

## Decision

garak se adopta como el escaner de vulnerabilidades LLM de SoloDShouse.

garak se ejecuta como paso de auditoria antes de promocionar cualquier modelo a produccion. Es una herramienta CLI, no requiere container. Escanea: prompt injection, data exfiltration, bias, toxicity. Los resultados se almacenan en MLflow para trazabilidad.

## Rationale

- **0 overhead:** garak es un paquete Python CLI. No hay daemon, no hay container, no hay RAM persistente. Se instala en el entorno virtual y se ejecuta on-demand.
- **Especializado:** A diferencia de herramientas de seguridad genericas, garak esta disenado especificamente para atacar LLMs: jailbreaks, prompt injection, extraction attacks, bias probes.
- **Trazabilidad:** Los resultados de garak (JSON, HTML) se loguean como artefactos en MLflow. Esto permite correlacionar cada modelo desplegado con su informe de auditoria.
- **NVIDIA backing:** Desarrollado por el equipo de seguridad de NVIDIA, con probes actualizadas y comunidad de seguridad ML activa.

## Consequences

- **Positivas:** Sin overhead de RAM o containers. Auditoria de seguridad replicable y versionable. Integracion directa con MLflow para trazabilidad de modelos.
- **Negativas:** garak es una herramienta de ataque, no de defensa. Identifica vulnerabilidades pero no las mitiga automaticamente. Requiere intervencion manual para hardening del modelo o del prompt.

## Alternatives Considered

- **Promptfoo:** Rechazado porque, aunque util para evaluacion de prompts, esta mas orientado a regression testing de prompts que a descubrimiento de vulnerabilidades de seguridad.
- **LLM Guard:** Rechazado porque es un firewall de entrada/salida (defensa), no un escaner de vulnerabilidades (ofensiva). Se complementa con garak pero no lo reemplaza.
- **Evaluacion manual:** Rechazado porque no es reproducible ni exhaustiva. garak ejecuta cientos de probes automaticamente.
