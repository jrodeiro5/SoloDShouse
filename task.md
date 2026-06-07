# SoloDShouse — Build Tasks

## Context

SoloDShouse is a fork of SoloLakehouse v2.5, pivoted from financial data (ECB/DAX) to a full data science + AI agent platform for European energy data (ENTSO-E). This is a TFM at Universidad Complutense de Madrid (Master in Big Data, Data Science & AI).

**Guiding principle:** Local-first, anti-cloud, minimize RAM and cost. Mac Studio M4 Max (64 GB) for dev, Hetzner CPX21 (4 GB, ~EUR 5/mo) for staging.

See `docs/solodshouse/session-memory.md` for all stack decisions and context.
See `docs/solodshouse/decisions/` for SDS-XXX ADRs.

---

## Phase 0: Foundation (fork cleanup) — CURRENT

Goal: clean fork identity, correct docs structure, no SoloLakehouse branding in active files.

- [x] Docs restructured: `docs/sololakehouse_legacy_docs/` (legacy, read-only), `docs/solodshouse/` (ours)
- [x] SDS ADRs moved to `docs/solodshouse/decisions/`
- [x] `CLAUDE.md` rewritten for SoloDShouse
- [x] `README.md` rewritten for SoloDShouse
- [x] `CHANGELOG.md` fork point marked
- [x] `CONTRIBUTING.md` updated
- [x] `task.md` updated (this file)
- [ ] `docs/decisions/README.md` committed (currently modified/untracked)
- [ ] Commit Phase 0 as `chore: fork identity and docs restructure`
- [ ] Tag `sds-v0.1.0` (fork baseline)

---

## Phase 1: Lakehouse Layer Migration

Goal: replace SoloLakehouse v2.5 runtime components with SoloDShouse stack.

### 1.1 Object Storage (MinIO -> SeaweedFS)

- [ ] Replace MinIO service in `docker/docker-compose.yml` with SeaweedFS
- [ ] Update `OBJECT_STORE_*` env vars in `.env.example`
- [ ] Update `ingestion/iceberg_io.py` to use `OBJECT_STORE_ENDPOINT` instead of `MINIO_ENDPOINT`
- [ ] Update Trino catalog templates (`config/trino/catalog/*.properties`)
- [ ] Update `scripts/init-iceberg-namespaces.py` for new bucket names
- [ ] Verify Iceberg read/write via SeaweedFS
- [ ] `make verify` passes with SeaweedFS

### 1.2 Database Extensions (PostgreSQL)

- [ ] Add pgvector extension to PostgreSQL init (`config/postgres/init.sql`)
- [ ] Add PostGIS extension
- [ ] Verify extensions loaded on `make up`

### 1.3 DuckDB Integration

- [ ] Add DuckDB as in-process library in `requirements.txt`
- [ ] Add dbt-core + dbt-duckdb
- [ ] Create `transformations/dbt/` project structure
- [ ] Verify DuckDB can query Iceberg Gold via pyiceberg scan

### 1.4 Domain Pivot (ECB/DAX -> ENTSO-E)

- [ ] Create `ingestion/collectors/entso_collector.py` (replaces ECBCollector)
- [ ] Create `ingestion/collectors/open_meteo_collector.py` (replaces DAXCollector)
- [ ] Create `ingestion/schema/entso_records.py` (Pydantic v2)
- [ ] Create `ingestion/schema/weather_records.py` (Pydantic v2)
- [ ] Create `ingestion/iceberg_schemas.py` entries for ENTSO-E/weather tables
- [ ] Create `transformations/entso_bronze_to_silver.py`
- [ ] Create `transformations/weather_bronze_to_silver.py`
- [ ] Create `transformations/silver_to_gold_features.py` (ENTSO-E + weather join)
- [ ] Update Dagster assets in `dagster/assets.py` for new collectors
- [ ] `make pipeline` succeeds with ENTSO-E data
- [ ] Gold table queryable via Trino and DuckDB

### Phase 1 Exit Criteria

- [ ] `make up` starts core stack (no MinIO, no OpenMetadata, no Superset)
- [ ] `make pipeline` runs ENTSO-E -> Bronze -> Silver -> Gold
- [ ] `make test` passes (new collectors, schemas, transforms)
- [ ] Gold table queryable via Trino and DuckDB
- [ ] Commit and tag `sds-v0.2.0`

---

## Phase 2: ML Layer

Goal: ML experiments for energy forecasting using new Gold features.

- [ ] Create `ml/train_energy_forecast.py` (XGBoost/LightGBM + TimeSeriesSplit)
- [ ] Add LSTM forecasting (`ml/lstm_forecast.py`) — UCM module 10
- [ ] Add anomaly detection (`ml/anomaly_detection.py`) — UCM module 7
- [ ] MLflow experiments tracked for all models
- [ ] BentoML serving for at least one model
- [ ] `make pipeline` includes ML step
- [ ] Evidence.dev BI reports reading Gold features
- [ ] Commit and tag `sds-v0.3.0`

---

## Phase 3: AI Agent Layer

Goal: natural-language data queries over the lakehouse via deepagents.

- [ ] `docker/docker-compose.yml`: add Open WebUI, LiteLLM, deepagents services
- [ ] Create `agents/deepagents_proxy.py` (FastAPI: OpenAI API -> deepagents)
- [ ] Create `agents/tools/iceberg_query_tool.py` (MCP tool: DuckDB -> Gold)
- [ ] Create `agents/tools/entso_api_tool.py` (MCP tool: live ENTSO-E queries)
- [ ] Register ToolUniverse tools via FastMCP
- [ ] LiteLLM routes to Groq (VPS) or llama.cpp/vLLM (Mac)
- [ ] Open WebUI connects to FastAPI proxy
- [ ] mem0 memory layer wired to deepagents
- [ ] kotaemon RAG over project docs
- [ ] garak audit run before staging deploy
- [ ] AGT policy config for agent tool calls
- [ ] Commit and tag `sds-v0.4.0`

---

## Phase 4: Observability + BI

Goal: production-grade observability and BI.

- [ ] Langfuse: LLM traces + eval + prompt management
- [ ] Prometheus + node_exporter: system metrics
- [ ] Alertmanager + Apprise: alerts to Telegram
- [ ] Evidence.dev reports for all Gold datasets
- [ ] nginx portal hub (SDS-035)
- [ ] Astro Starlight docs site (SDS-032)
- [ ] Adala data labeling pipeline for Bronze quality
- [ ] Commit and tag `sds-v0.5.0`

---

## Phase 5: VPS Staging Deploy

Goal: full stack running on Hetzner CPX21 within 4 GB RAM.

- [ ] `docker/docker-compose.vps.yml` (lean profile: core + agent, no LLM local)
- [ ] LiteLLM routes to Groq API on VPS
- [ ] CI: GitHub Actions builds multi-arch images -> GHCR
- [ ] SSH deploy to Hetzner
- [ ] `make verify` passes on VPS
- [ ] Tailscale tunnel Mac -> VPS for LLM inference (optional)
- [ ] Commit and tag `sds-v1.0.0`

---

## Phase 6: TFM Completion

Goal: all 15 UCM modules demonstrably covered, thesis-ready.

- [ ] Module 3 (Tableau): connect Tableau Desktop to DuckDB/PG, document
- [ ] Module 5 (NoSQL): MongoDB service + document store use case
- [ ] Module 11 (Spark): on-demand compose profile, one PySpark job
- [ ] Module 14 (TFM Context): IberGrid framing documented
- [ ] Full `make demo` path: ENTSO-E -> Bronze -> Silver -> Gold -> ML -> Agent
- [ ] Evidence.dev dashboards: generation mix, price forecast, anomaly alerts
- [ ] All ADRs (SDS-XXX) written and indexed
- [ ] TFM document references repo

---

## Pi Agent Tasks

### PI-001: GitHub Stars Python Library Audit

**Owner:** pi-qa
**Status:** unclaimed
**Branch:** agent/pi-qa (worktree: `.superset/worktrees/.../pi-qa`)

Scrape and audit jrodeiro5's GitHub starred repos for Python libraries relevant to SoloDShouse.

**Source:** https://github.com/jrodeiro5?language=python&tab=stars

**Goal:** Identify starred Python libraries worth adding to `pyproject.toml` groups (`prod`, `dev`, `qa`). Cross-reference against existing deps — no duplicates.

**Output:** `docs/solodshouse/gotchas/pi-001-starred-python-libs.md` with this structure:

```markdown
# PI-001: Starred Python Library Audit

## Prod candidates
| Lib | Stars | Why useful | pyproject group |
|-----|------:|-----------|----------------|

## Dev candidates
| Lib | Stars | Why useful | pyproject group |

## QA candidates
| Lib | Stars | Why useful | pyproject group |

## Rejected / already covered
| Lib | Reason skipped |
```

**Rules:**
- Use Playwright or gh CLI to paginate all starred pages (language=python filter)
- Score by: relevance to SoloDShouse stack (lakehouse, ML, agents, observability), star count, last commit recency
- Skip anything already in `pyproject.toml` or `requirements-dagster.txt`
- Do NOT add to pyproject.toml — audit + recommend only, human decides
- PR to main when doc is written

---

## Phase 0.5: Dev Tooling Foundation — NEXT (assign to opencode-builder)

### 0.5.1 Python Dependency Structure

**Owner:** opencode-builder  
**Status:** unclaimed

Migrate from flat `requirements.txt` to `pyproject.toml` with `uv`-managed groups.

- [ ] Create `pyproject.toml` with dep groups: `prod`, `dev`, `qa`
- [ ] `prod` = runtime deps for Docker images (no pytest, no ruff, no mypy)
- [ ] `dev` = prod + linting/typing tools (ruff, mypy, types-*)
- [ ] `qa` = prod + test tools (pytest, pytest-cov) + browser automation (playwright)
- [ ] Add `markitdown` to `dev` group (Moodle content extraction, dev-only)
- [ ] Add `playwright` to `qa` group
- [ ] Run `uv venv .venv` + `uv pip install -e ".[dev]"` — verify clean install
- [ ] Update `Makefile` targets: `make install` uses `uv`, `make install-qa` adds qa group
- [ ] Keep `requirements-dagster.txt` separate (Dagster has own constraints)
- [ ] Delete `requirements.txt` after pyproject.toml verified

### 0.5.2 Moodle Content Extraction (UCM Masters → Dev Context)

**Owner:** opencode-builder  
**Status:** unclaimed  
**Purpose:** Extract UCM master's module content so Claude Code has domain grounding during implementation. This is dev tooling, NOT a product feature.

**Approach:** Moodle REST API + markitdown conversion → markdown files indexed by qmd.

Steps:
- [ ] Investigate Moodle REST API at UCM (`/webservice/rest/server.php`) — requires user token
- [ ] Create `scripts/extract_moodle.py`:
  - Auth via Moodle token (env var `MOODLE_TOKEN`)
  - List enrolled courses → filter TFM master modules
  - For each module: fetch course contents (files, pages, resources)
  - Download HTML/PDF resources
  - Convert to markdown via `markitdown`
  - Write to `docs/solodshouse/ucm-modules/module-{N:02d}-{slug}.md`
- [ ] Fallback: if Moodle API blocked, use Playwright to scrape authenticated session
  - `scripts/extract_moodle_browser.py` using playwright + Chrome DevTools
  - Login flow → navigate course pages → extract text + download attachments
- [ ] Run `qmd update` after extraction to index for Claude Code queries
- [ ] Add `MOODLE_TOKEN` to `.env.example` (empty, with comment)
- [ ] Script is one-shot, idempotent (skip already-extracted modules)

**Output structure:**
```
docs/solodshouse/ucm-modules/
  module-01-business-intelligence.md
  module-02-sql.md
  module-03-tableau.md
  ...
  module-15-applied-data-science.md
  README.md   ← index of modules + coverage map vs SoloDShouse stack
```

**Blocked by:** MOODLE_TOKEN — user must provide. Leave placeholder, don't block on it.

---

## Backlog / Pending Decisions

| Item | Status | Notes |
|------|:------:|-------|
| Feast (feature store) | pending | Evaluate vs dbt MetricFlow |
| Marimo (reactive notebooks) | pending | Evaluate vs Jupyter |
| Evidently AI (drift monitoring) | pending | Evaluate alongside Langfuse |
| SQLMesh vs dbt-core | pending | SQLMesh technically superior but MetricFlow = prototype |
| graphiti vs mem0 | pending | graphiti: KG temporal, needs Neo4j; mem0: simpler |
| floci S3 vs SeaweedFS | pending | floci = 13 MB vs 150 MB; test Iceberg compat |
| turbovec | pending | 16x pgvector compression; evaluate if RAM is bottleneck |
| IberGrid framing (Mod 14) | pending | Real or fictional energy utility context |
| Grafana/Loki as optional profile | pending | Currently eliminated from core; may add as compose profile |

---

## Note on Inherited Tasks

The original `task.md` entity-split planning from SoloLakehouse v2.5 (finlakehouse / aviation-lakehouse split) is preserved in [`docs/sololakehouse_legacy_docs/`](docs/sololakehouse_legacy_docs/) for reference. That model is superseded by the SoloDShouse fork strategy.
