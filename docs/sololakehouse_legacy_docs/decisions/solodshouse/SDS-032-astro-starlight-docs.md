# SDS-032: Astro Starlight para docs

**Status:** Proposed
**Date:** 2026-06-07

## Context

SoloDShouse necesita un sitio de documentacion para el TFM: docs de arquitectura, referencia API, guias de usuario, guias de despliegue. SoloLakehouse usaba Markdown basico en `docs/`. Se evaluaron varias opciones de static site generator orientadas a documentacion tecnica.

## Decision

Usar Astro Starlight como framework de documentacion.

## Rationale

- **MDX nativo.** Permite componentes interactivos dentro de la documentacion, util para mostrar dashboards de energia o diagramas de arquitectura embebidos.
- **Island architecture.** Solo hidrata lo necesario. Builds rapidos, output estatico ligero.
- **Ecosistema web amplio.** Familiar para desarrolladores web, mas componentes y themes disponibles que en MkDocs.
- **Output estatico puro.** ~200MB en build time, 0 MB runtime. Los archivos estaticos se sirven via nginx portal, sin necesidad de Node.js en produccion.
- **Theming y i18n.** Buen soporte para temas oscuros/claricos y futura traduccion si el TFM lo requiere.

## Consequences

- Positivas: builds rapidos, sitio rapido, componentes ricos, despliegue trivial via nginx.
- Negativas: curva de aprendizaje de Astro/MDX para quien solo conozca Markdown puro. Ecosistema menor que Docusaurus (Meta).

## Alternatives Considered

- **Quarkdown:** 15.4k stars, formato .qd propietario, poco conocido. Rechazado por lock-in de formato.
- **MkDocs Material:** Bueno, rapido, pero menos ecosistema de componentes. Rechazado por limitaciones de interactividad.
- **Docusaurus:** Meta, maduro, pero mas pesado. Rechazado porque genera mas JS del necesario para un TFM donde se prefiere output estatico minimal.
