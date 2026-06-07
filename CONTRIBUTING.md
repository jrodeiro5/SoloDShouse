# Contributing

SoloDShouse is a personal TFM project (UCM Madrid). External contributions are welcome for bug fixes and documentation improvements.

## Fork Context

This project is a fork of [SoloLakehouse v2.5](https://github.com/Jiahong-Que-9527/SoloLakehouse). The original docs are preserved in [`docs/sololakehouse_legacy_docs/`](docs/sololakehouse_legacy_docs/) and must not be modified. SoloDShouse-specific docs live in [`docs/solodshouse/`](docs/solodshouse/).

## Workflow

- Branch from `main`
- Work in a feature branch or agent worktree (`magnetic-mile`, `sphenoid-toothbrush`)
- PR back to `main`
- Never push directly to `main`

## Code Standards

- Python 3.13+, managed with `uv` + `.venv`
- `ruff` for linting (`make lint`)
- `mypy` for type checking (`make typecheck`)
- `pytest` for tests (`make test`)
- Follow patterns in `CLAUDE.md`

## ADRs

Architecture decisions for SoloDShouse go in `docs/solodshouse/decisions/` with `SDS-XXX` prefix. See existing ADRs for format.

## Full Setup

See [docs/solodshouse/tfm-architecture-guide.md](docs/solodshouse/tfm-architecture-guide.md) for full stack context.
