# SDS-036: OrbStack como runtime Docker en macOS

**Status:** Accepted
**Date:** 2026-06-07

## Context

SoloDShouse usa Docker Compose para orquestar todos los servicios del stack (lakehouse, ML, agentes, observabilidad). En macOS, se necesita un runtime Docker. Docker Desktop es la opción más conocida pero tiene limitaciones relevantes para este proyecto: alto consumo de RAM, latencia en Apple Silicon bajo Rosetta, y licencia comercial para uso profesional.

## Decision

Usar **OrbStack** como runtime Docker en macOS (DEV). OrbStack provee la CLI estándar `docker` y `docker compose` sin cambios en ningún script o Makefile. En Hetzner VPS (STAGING/PROD), se usa Docker Engine nativo (Linux).

## Rationale

- **Rendimiento Apple Silicon**: OrbStack es nativo arm64, sin capa Rosetta. Los contenedores arrancan significativamente más rápido.
- **RAM**: OrbStack consume ~150 MB de overhead vs ~800 MB+ de Docker Desktop.
- **Compatibilidad**: CLI 100% compatible — `docker`, `docker compose`, `docker buildx` funcionan sin cambios.
- **Integración macOS**: Red y volúmenes integrados con el sistema de archivos macOS de forma más eficiente que Docker Desktop.
- **act (nektos)**: Necesario para correr GitHub Actions localmente — OrbStack provee el daemon Docker que `act` requiere.
- **Licencia**: OrbStack es gratuito para uso personal/estudiantes.

## Consequences

- Instalar: `brew install orbstack`
- No requiere cambios en `docker-compose.yml`, `Makefile`, ni scripts de CI.
- En CI (GitHub Actions), se usa el Docker Engine de ubuntu-latest — no OrbStack.
- Si se trabaja en Linux nativo, usar Docker Engine directamente.

## Alternatives Considered

1. **Docker Desktop** — rechazado: mayor RAM, peor rendimiento en ARM, licencia comercial.
2. **Colima** — considerado: más ligero pero menos integración macOS y sin UI.
3. **Podman Desktop** — rechazado: incompatibilidades con algunos compose profiles complejos.
