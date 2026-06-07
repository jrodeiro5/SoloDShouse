# Architecture Docs

Mermaid diagrams covering SoloDShouse at every level of detail (C4 model + domain-specific flows).

## C4 Model

| Level | File | What it shows |
|-------|------|---------------|
| C1 — System Context | [C1-system-context.md](C1-system-context.md) | Users + external APIs surrounding SoloDShouse |
| C2 — Containers | [C2-containers.md](C2-containers.md) | All Docker services + their communication |
| C3 — Components | [C3-components-ingestion.md](C3-components-ingestion.md) | Dagster assets, collectors, transforms + data stores |

## Domain Diagrams

| File | What it shows |
|------|---------------|
| [data-flow.md](data-flow.md) | Full Bronze→Silver→Gold pipeline, idempotency flow, schema ER diagram |
| [deployment.md](deployment.md) | Mac (dev) vs Hetzner VPS (staging) deployment + RAM budgets |
| [ruflo-integration.md](ruflo-integration.md) | Ruflo plugin priority + integration architecture plan |

## Render Locally

All diagrams use Mermaid — rendered natively by GitHub. For local preview:

```bash
# VS Code extension (recommended)
code --install-extension bierner.markdown-mermaid

# CLI render to PNG
npx @mermaid-js/mermaid-cli -i docs/solodshouse/architecture/data-flow.md -o /tmp/data-flow.png
```
