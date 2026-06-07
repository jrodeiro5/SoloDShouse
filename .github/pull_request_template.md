## What changed

Briefly describe the main changes in this PR.

## Why

Explain the motivation and expected outcome.

## Layer

- [ ] Lakehouse (ingestion, Iceberg, Dagster)
- [ ] ML (training, MLflow, BentoML)
- [ ] Agent (deepagents, MCP tools, LiteLLM)
- [ ] Observability (Langfuse, Prometheus, Alertmanager)
- [ ] BI (Evidence.dev, nginx portal)
- [ ] Infra / Docker Compose
- [ ] Docs / ADR

## Validation

- [ ] `make verify`
- [ ] `make pipeline` (if lakehouse/ML flow changed)
- [ ] `make lint`
- [ ] `make typecheck`
- [ ] `make test`
- [ ] Tested with `act push` locally (if workflow changed)

## Checklist

- [ ] ADR written in `docs/solodshouse/decisions/` if architectural decision made
- [ ] Docs updated if behavior changed
- [ ] No secrets or credentials added
- [ ] `OBJECT_STORE_*` env vars used (not `MINIO_*`) for new object store code
- [ ] VPS RAM impact considered (Hetzner CPX21 = 4 GB limit)
