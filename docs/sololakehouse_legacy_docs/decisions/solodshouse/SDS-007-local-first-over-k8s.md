# SDS-007: Local-first con Docker Compose profiles, no Kubernetes

**Status:** Proposed
**Date:** 2026-06-07
**Supersedes:** ADR-007

## Context

ADR-007 propuso migrar a Kubernetes+Helm+Terraform para infraestructura de produccion en SoloLakehouse v3. SoloDShouse tiene restricciones diferentes: es un proyecto de TFM, no un producto enterprise. El objetivo es una unica Mac Studio M4 Max (64GB) para desarrollo y un Hetzner CPX21 (4GB, ~5 EUR/mes) para staging. El principio es local-first, anti-cloud, minimizar coste.

## Decision

SoloDShouse usa Docker Compose profiles exclusivamente. No Kubernetes, Helm, ni Terraform. Profiles: core (~2.8GB), ml (~3.3GB), agent (~5.4GB), full (~6.6GB), llm-7b (~12.6GB), llm-70b (~56.6GB), +spark (~4GB on-demand). Staging en VPS usa perfil minimal + LLM externo via Groq API o tunel SSH.

## Rationale

K8s anade 2+ GB RAM de overhead solo para el control plane. Un VPS de 4GB no puede ejecutar K8s. Los profiles de Docker Compose dan control granular de RAM. El TFM no necesita HA, aislamiento multi-tenant, ni despliegues rolling. El proyecto es una arquitectura de referencia single-user, no un SaaS de produccion.

## Consequences

No se demuestran habilidades de K8s, pero los profiles de Docker Compose son mas relevantes para la demostracion local-first del TFM. El despliegue es `docker compose --profile X up`. El despliegue en VPS se simplifica (sin Helm charts). No se necesita Terraform — un unico `docker-compose.vps.yml` es suficiente.

## Alternatives Considered

1. **K8s en VPS** — rechazado: un VPS de 4GB no puede ejecutar K8s.
2. **K8s solo en Mac** — rechazado: anade complejidad sin beneficio para el TFM.
3. **Nomad** — rechazado: menos ecosistema que Compose.
4. **Mantener Compose como en ADR-001** — aceptado pero los profiles son nuevos.
