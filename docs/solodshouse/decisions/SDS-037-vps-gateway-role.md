# SDS-037: Rol del VPS como gateway always-on y backbone de observabilidad

**Status:** Draft
**Date:** 2026-06-07

## Context

SoloDShouse corre el stack completo (lakehouse, ML, agentes) en un Mac Studio M4 Max. El Mac es potente pero local: no tiene IP pública estática, puede estar apagado, y no sirve como punto de acceso externo. Se dispone de un Hetzner CX23 (2 vCPU / 4 GB RAM / 40 GB SSD, ~€4.83/mes) como única infraestructura cloud.

El VPS tiene 4 GB RAM — insuficiente para Trino, LLM inference, Dagster, o cualquier componente pesado del stack. Necesita un rol claro y acotado que aporte valor real sin solaparse con el Mac.

## Decision

El VPS actúa exclusivamente como **gateway always-on y backbone de observabilidad**. No ejecuta componentes del stack de datos ni LLM local.

**Servicios en VPS:**

| Servicio | RAM aprox. | Rol |
|----------|-----------|-----|
| nginx | ~10 MB | Reverse proxy, portal público, TLS termination |
| Prometheus + node_exporter | ~100 MB | Scrape métricas de VPS y Mac (via Tailscale) |
| Alertmanager + Apprise | ~50 MB | Alertas a Telegram/Slack — funciona aunque el Mac esté apagado |
| LiteLLM → Groq API | ~150 MB | Gateway LLM always-on; cuando el Mac está offline, queries rutan a Groq (free tier) |
| Astro Starlight docs (static) | ~50 MB servido | Docs TFM accesibles para revisores UCM sin necesidad del Mac |

**Total estimado:** ~360 MB. Deja ~3.4 GB de margen para OS y bursts.

**Conectividad Mac ↔ VPS:** Tailscale (free tier). El VPS hace proxy hacia el Mac cuando está activo.

## Rationale

- **Always-on**: alertas y monitorización funcionan independientemente del estado del Mac.
- **IP pública**: expone docs TFM y portal de servicios a revisores externos sin abrir el Mac a internet.
- **LLM fallback**: LiteLLM en VPS enruta a Groq (gratuito) cuando el Mac está apagado — el chat no queda sin respuesta.
- **40 GB disco**: suficiente para configuración, logs de nginx/Prometheus, y docs estáticos. No se almacenan datos de Iceberg ni trazas de Langfuse en VPS.
- **Langfuse queda en Mac**: requiere PostgreSQL y crece en disco — no cabe de forma segura en 40 GB a largo plazo.

## Consequences

- Nuevo VPS CX23 a crear desde cero (el anterior se elimina).
- Hardening inicial: SSH key-only, ufw, fail2ban.
- Tailscale instalado en Mac y VPS para túnel privado.
- `docker-compose.yml` separado para VPS (profile `gateway`), distinto del compose del Mac.
- Langfuse, deepagents, kotaemon, PostgreSQL, SeaweedFS, Trino, MLflow → Mac únicamente.
- LLM inference (llama.cpp, vLLM) → Mac únicamente.

## Alternatives Considered

1. **VPS como réplica staging del stack completo** — rechazado: 4 GB RAM no permite Trino (1.5 GB) + Dagster (~400 MB) + PG (~300 MB) simultáneamente con margen.
2. **Zabbix para monitorización** — rechazado: ~500 MB + PostgreSQL propio, redundante con Prometheus ya planificado.
3. **Sin VPS** — rechazado: pierde IP pública, alertas always-on, y LLM fallback. El coste de ~€5/mes justifica estos tres beneficios.
