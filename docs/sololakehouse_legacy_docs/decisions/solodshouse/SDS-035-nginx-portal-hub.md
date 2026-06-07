# SDS-035: Portal nginx como hub central

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse ejecuta 10+ servicios web: Dagster UI, Trino UI, MLflow, Evidence.dev, kotaemon, Open WebUI, Langfuse, Prometheus/Alertmanager, y Astro Starlight docs. Los usuarios necesitan un punto de entrada unico. SoloLakehouse tenia un portal ligero (commit `6d2e657`). SoloDShouse necesita enrutar a todos los servicios con auth, HTTPS, y descubrimiento de servicios.

## Decision

Usar nginx como portal hub central.

## Rationale

- **Ligero.** ~10MB de contenedor. En una VPS de 4GB, cada MB cuenta.
- **Reverse proxy unificado.** Un solo puerto (80/443) expuesto al exterior. nginx enruta a cada servicio interno por path o subdomain.
- **Auth basica para staging.** En Hetzner CPX21, nginx proporciona basic auth antes de llegar a servicios que no tienen auth propio (Prometheus, Trino UI).
- **HTTPS termination.** nginx maneja los certificados SSL, descargando a los servicios internos de esa responsabilidad.
- **Landing page de servicios.** Una pagina HTML simple lista todos los servicios con enlaces, estado, y health checks visuales.
- **Docs estaticas.** En la VPS, nginx tambien sirve el sitio estatico de Astro Starlight docs.

## Consequences

- Positivas: unico punto de entrada, auth centralizada, HTTPS unificado, pagina de estado visual, sin coste de memoria significativo.
- Negativas: nginx no es un service mesh. No tiene descubrimiento automatico de servicios (se configura manualmente). Para escalar mas alla del TFM, Traefik o Caddy podrian ser mejores.

## Alternatives Considered

- **Traefik:** Buen descubrimiento automatico con Docker labels. Rechazado por mayor consumo de RAM y complejidad innecesaria para un stack fijo.
- **Caddy:** Configuracion mas simple, HTTPS automatico. Rechazado porque nginx es mas familiar y el portal HTML legacy de SoloLakehouse ya usaba nginx.
- **Exponer cada servicio en puerto propio:** Rechazado por caos de puertos, problemas de CORS, y sin auth centralizada.
