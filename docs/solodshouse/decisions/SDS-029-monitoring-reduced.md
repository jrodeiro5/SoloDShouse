# SDS-029: Monitorizacion reducida — Prometheus + Alertmanager + Apprise

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloLakehouse v2.5 no tenia monitorizacion (ADR-005 diferio Grafana/Prometheus). El ADR-015 de v3 propuso Prometheus + Grafana + Alertmanager. SoloDShouse necesita monitorizacion pero debe minimizar el consumo de RAM.

Grafana (~300MB) y Loki (~100MB) anaden overhead significativo para un TFM single-user. Se necesita un stack de monitorizacion que alerte ante problemas pero que no consuma recursos excesivos.

## Decision

Prometheus + node_exporter (~100MB) para recoleccion de metricas. Alertmanager (~50MB) para enrutamiento de alertas. Apprise (libreria Python, 0MB) para notificaciones multi-canal (Telegram, Slack, WhatsApp) integrado via deepagents.

Grafana + Loki estan disponibles como perfil opcional de Docker Compose (`DAG_OFF` inverso — on-demand) pero NO forman parte del stack core. Langfuse (SDS-028) gestiona la observabilidad LLM por separado de la monitorizacion del sistema.

## Rationale

- **Minimizacion de RAM:** Prometheus + node_exporter + Alertmanager suman ~150MB. Grafana + Loki sumarian ~400MB adicionales. En un VPS de 4GB, esta diferencia es critica.
- **Alertas activas vs dashboards pasivos:** Para un TFM single-user, lo importante es saber cuando algo falla (alertas), no tener un dashboard bonito siempre visible. Las alertas se envian via Telegram/Slack.
- **Apprise via deepagents:** Apprise es una libreria Python que soporta decenas de canales de notificacion. En lugar de un container dedicado, se integra como una herramienta que los agentes de deepagents pueden invocar.
- **Grafana on-demand:** Cuando se necesita debug visual (raro en un TFM estable), se activa el perfil `monitoring` de Docker Compose. El resto del tiempo, Grafana esta apagado.

## Consequences

- **Positivas:** Reduccion de ~400MB de RAM en el stack base. Alertas proactivas via canales de mensajeria. Grafana disponible cuando se necesita sin penalizacion permanente.
- **Negativas:** No hay dashboard visual permanente. Para ver metricas historicas, hay que activar Grafana o consultar Prometheus directamente. Loki (logs) no esta disponible sin activar el perfil opcional.

## Alternatives Considered

- **Grafana + Prometheus + Loki (stack completo):** Rechazado por consumo excesivo de RAM para un TFM single-user. Grafana asume un operator que mira dashboards frecuentemente.
- **Netdata:** Rechazado porque, aunque ligero, es mas orientado a monitorizacion de sistema operativo que a metricas de aplicacion (tiempo de query Trino, tasa de ingestas fallidas, etc.).
- **Uptime Kuma:** Rechazado porque es un monitor de uptime simple (ping/HTTP), no un sistema de metricas y alertas con PromQL.
