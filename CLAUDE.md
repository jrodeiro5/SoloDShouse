# Agent Guide for SoloDShouse

Read before any changes. SoloDShouse = **fork** of SoloLakehouse v2.5 — not that project.

## What This Project Is

**SoloDShouse (Solo Data Science House)** — local-first DS + AI agent platform, TFM at Universidad Complutense de Madrid (Master in Big Data, Data Science & AI).

**Mission:** Full DS/ML/AI stack — data lakehouse, ML experiments, AI agents, neural networks — runs on single powerful local machine + €5/month Hetzner VPS. Zero cloud surprise bills. Zero vendor lock-in.

**Domain:** European energy data (ENTSO-E grid + Open-Meteo weather) replacing original SoloLakehouse financial domain (ECB/DAX).

**Forked from:** SoloLakehouse v2.5 (github.com/Jiahong-Que-9527/SoloLakehouse). Original ADRs 001-020 in `docs/sololakehouse_legacy_docs/decisions/` — read-only, never modify.

**SoloDShouse ADRs:** `docs/solodshouse/decisions/` (SDS-XXX prefix).

## Coding Guidelines (mandatory for all agents)

### 1. Think Before Coding

No assumptions. No hidden confusion. Surface tradeoffs.

Before implementing:
- State assumptions explicitly. Uncertain → ask.
- Multiple interpretations → present them, don't pick silently.
- Simpler approach exists → say so. Push back when warranted.
- Unclear → stop. Name what's confusing. Ask.

### 2. Simplicity First

Minimum code. Nothing speculative.
- No features beyond what was asked.
- No abstractions for single-use code.
- No unrequested "flexibility" or "configurability".
- No error handling for impossible scenarios.
- 200 lines could be 50 → rewrite it.

Ask: "Would senior engineer call this overcomplicated?" Yes → simplify.

### 3. Surgical Changes

Touch only what you must. Clean only your own mess.

Editing existing code:
- Don't "improve" adjacent code, comments, formatting.
- Don't refactor things not broken.
- Match existing style even if you'd differ.
- Unrelated dead code → mention it, don't delete.

Your changes create orphans:
- Remove imports/variables/functions **your** changes made unused.
- Don't remove pre-existing dead code unless asked.

Test: every changed line traces directly to user's request.

### 4. Goal-Driven Execution

Define success criteria. Loop until verified.

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write test reproducing it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

Multi-step tasks, state brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria → loop independently. Weak ("make it work") → constant clarification.

## Hardware Targets

| Environment | Machine | RAM | Cost |
|-------------|---------|:---:|:----:|
| DEV | Mac Studio M4 Max | 64 GB | owned |
| STAGING | Hetzner CX23 (2 vCPU / 4 GB / 40 GB) | 4 GB | ~€4.83/mo |

**Docker runtime (macOS):** OrbStack — replaces Docker Desktop. Faster on Apple Silicon, lower RAM overhead, native `docker` and `docker compose` CLI. Install: `brew install orbstack`.

## Tech Stack

### Lakehouse Layer (Base)

| Component | Role | RAM |
|-----------|------|:---:|
| PostgreSQL 17 + pgvector + PostGIS | DB + vectors + geo | ~300 MB |
| SeaweedFS (S3-compatible) | Object storage (replaces MinIO — archived Apr 2026) | ~150 MB |
| Apache Hive Metastore | Iceberg catalog for Trino | ~400 MB |
| Trino | Federated SQL query engine | ~1.5 GB |
| DuckDB | Local OLAP (in-process, zero-config) | ~100 MB |
| Apache Iceberg via pyiceberg | Table format (Bronze/Silver/Gold) | library |
| dbt-core + dbt-duckdb | SQL transformations + MetricFlow metrics | CLI |
| Dagster | Asset orchestration + scheduling | ~400 MB |

### ML Layer

| Component | Role | RAM |
|-----------|------|:---:|
| MLflow 3.x | Experiment tracking + model registry | ~300 MB |
| BentoML | Classical model serving | ~200 MB |
| XGBoost + LightGBM + scikit-learn | ML models | library |

### Agent + AI Layer

| Component | Role | RAM |
|-----------|------|:---:|
| deepagents | Agent harness (LangGraph-based) | ~200 MB |
| FastAPI proxy | OpenAI-compatible API → deepagents | ~50 MB |
| Open WebUI | Chat UI (self-hosted) | ~300 MB |
| LiteLLM | Unified LLM gateway (100+ providers) | ~150 MB |
| kotaemon | RAG UI (multi-user, citations, PDF) | ~1-2 GB |
| mem0 | Structured agent memory | ~100 MB |
| ToolUniverse + FastMCP | 1000+ scientific MCP tools | ~50 MB |
| AGT (Microsoft) | Agent governance / policy enforcement | library |
| garak (NVIDIA) | LLM vulnerability scanner (audit-only) | CLI |
| Adala | Data labeling agent | library |

### LLM Layer

| Component | Role | RAM |
|-----------|------|:---:|
| LiteLLM | Unified LLM gateway | ~150 MB |
| llama.cpp / vLLM | Local LLM inference (on-demand, Mac only) | 5-55 GB |
| Groq API | Remote LLM (free tier, VPS fallback) | 0 |

### Observability Layer

| Component | Role | RAM |
|-----------|------|:---:|
| Langfuse | LLM traces + eval + prompt management | ~300 MB |
| Prometheus + node_exporter | System metrics | ~100 MB |
| Alertmanager + Apprise | Alerting to Telegram/Slack/WA | ~50 MB |

### BI / Docs Layer

| Component | Role | RAM |
|-----------|------|:---:|
| Evidence.dev | Primary BI (markdown-first, git-deployable) | ~200 MB |
| nginx portal | Central service hub | ~10 MB |
| Astro Starlight | Docs site | ~200 MB (build) |
| MongoDB 7 | NoSQL store (UCM module 5) | ~300 MB |

## Docker Compose Profiles

| Profile | Services | RAM |
|---------|----------|:---:|
| `core` | PG+pgvector+PostGIS, SeaweedFS, Dagster, Hive, Trino | ~2.8 GB |
| `ml` | core + MLflow, BentoML | ~3.3 GB |
| `agent` | ml + deepagents, Open WebUI, LiteLLM, FastAPI proxy, mem0, kotaemon, ToolUniverse, garak, AGT | ~5.4 GB |
| `observability` | Langfuse, Prometheus, Alertmanager | ~0.45 GB |
| `bi` | Evidence.dev, nginx portal, Astro Starlight | ~0.4 GB |
| **`full`** | core+ml+agent+obs+bi+MongoDB+Adala | **~6.6 GB** |
| `llm-7b` | full + llama.cpp 7B | **~12.6 GB** |
| `llm-70b` | full + vLLM 70B | **~56.6 GB** |
| `+spark` | Spark on-demand add-on | **+4 GB** |

## Commands

```bash
make up              # Start core stack + init SeaweedFS buckets + Iceberg namespaces
make down            # Stop (data preserved under docker/data/)
make pipeline        # Run Dagster full_pipeline_job
make dagster-ui      # Open Dagster UI (http://localhost:3000)
make verify          # Health-check all services
make test            # Unit tests (pytest, no Docker needed)
make lint            # ruff
make typecheck       # mypy on ingestion/, transformations/, ml/, scripts/, dagster/
make clean           # Stop + delete docker/data/ + purge volumes
```

## Project Layout

```
ingestion/
  collectors/         # ENTSOECollector, OpenMeteoCollector (replaces ECB/DAX)
  schema/             # Pydantic v2 models
  quality/            # Bronze-layer quality checks
  bronze_writer.py    # Iceberg append via pyiceberg
  iceberg_io.py       # Core I/O: append_table, overwrite_table, scan_table, get_catalog
  iceberg_schemas.py  # Iceberg Schema + PartitionSpec
  trino_sql.py        # Trino REST utility (ad-hoc queries)

transformations/
  entso_bronze_to_silver.py      # ENTSO-E type cleanup, forward-fill
  weather_bronze_to_silver.py    # Open-Meteo cleanup
  silver_to_gold_features.py     # Join ENTSO-E+weather, build forecast features

ml/
  train_energy_forecast.py       # XGBoost/LightGBM + LSTM with TimeSeriesSplit CV
  evaluate.py                    # MLflow experiment runner

agents/
  deepagents_proxy.py            # FastAPI proxy: OpenAI API -> deepagents
  tools/                         # Custom MCP tools (ENTSO-E queries, Iceberg reads)

docs/
  solodshouse/                   # SoloDShouse docs (our space)
    decisions/                   # SDS-XXX ADRs
    session-memory.md            # Session decisions and context
    tfm-architecture-guide.md    # Full TFM architecture reference
  sololakehouse_legacy_docs/     # Original SoloLakehouse docs (read-only)

tests/                           # Unit tests (mocked I/O)
```

## Architecture Patterns — Follow When Adding Code

### Collector Pattern (ingestion/collectors/)

```python
class ENTSOECollector:
    def __init__(self, catalog: Catalog):
        self.catalog = catalog
        self.bronze_writer = BronzeWriter(catalog)

    def _fetch_data(self, start: date, end: date) -> pd.DataFrame:
        """Pull from ENTSO-E API. Use structlog. Validate response."""

    def _validate_records(self, raw_data) -> tuple[list, list]:
        """Pydantic v2 validation. Returns (valid_dicts, rejected_dicts)."""

    def _already_ingested(self, date: date) -> bool:
        """Check iceberg_io.scan_table for _ingestion_timestamp."""

    def collect(self, ...) -> dict:
        """fetch -> validate -> Bronze append. Returns summary dict."""
```

### Schema Pattern (ingestion/schema/)

```python
from pydantic import BaseModel, field_validator

class ENTSOERecord(BaseModel):
    timestamp: datetime
    country: str
    generation_mw: float

    @field_validator("generation_mw")
    @classmethod
    def non_negative(cls, v):
        if v < 0: raise ValueError("generation cannot be negative")
        return v
```

Use `.model_dump()` not `.dict()` — Pydantic v2.

### Transformation Pattern (transformations/)

```python
# Pure function (testable, no I/O)
def transform_entso_bronze_to_silver(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    # type conversions -> filter -> sort -> derive fields -> dedup
    return df[["col1", "col2", ...]]

# Orchestration (reads Iceberg, calls transform, writes Iceberg)
def run(catalog: Catalog) -> dict[str, object]:
    df = scan_table(catalog, "bronze", "entso_generation")
    silver_df = transform_entso_bronze_to_silver(df)
    overwrite_table(catalog, "silver", "entso_generation_cleaned", silver_df, SILVER_SCHEMA)
    return {"table": "iceberg:silver.entso_generation_cleaned", "row_count": len(silver_df)}
```

### Iceberg I/O Pattern

```python
from ingestion.iceberg_io import append_table, overwrite_table, scan_table, get_catalog

catalog = get_catalog()  # reads HIVE_METASTORE_URI, OBJECT_STORE_ENDPOINT, S3_ACCESS_KEY from env

# Bronze (immutable append)
append_table(catalog, "bronze", "entso_generation", df, BRONZE_SCHEMA, BRONZE_PARTITION)

# Silver / Gold (full overwrite each run)
overwrite_table(catalog, "silver", "entso_generation_cleaned", df, SILVER_SCHEMA)

# Read
df = scan_table(catalog, "gold", "energy_forecast_features")
```

### Logging Pattern

```python
import structlog
logger = structlog.get_logger()
logger.info("entso_data_ingested", rows=1440, country="ES", table="iceberg:bronze.entso_generation")
```

Event names: `snake_case`. Context: key-value pairs. Log at step boundaries.

### Agent Tool Pattern (agents/tools/)

```python
from fastmcp import FastMCP

mcp = FastMCP("solodshouse-tools")

@mcp.tool()
def query_gold_features(country: str, start: str, end: str) -> str:
    """Query energy forecast features from Gold layer via DuckDB."""
    ...
```

## Environment Variables

```python
# Object store (SeaweedFS S3-compatible)
endpoint = os.environ.get("OBJECT_STORE_ENDPOINT", "http://localhost:8333")
access_key = os.environ.get("OBJECT_STORE_ACCESS_KEY", "solodshouse")

# Buckets
data_bucket = os.environ.get("DATA_BUCKET", "solodshouse-data")
mlflow_bucket = os.environ.get("MLFLOW_ARTIFACT_BUCKET", "solodshouse-mlflow")
warehouse_uri = os.environ.get("WAREHOUSE_URI", "s3a://solodshouse-data/warehouse/")
```

Never hardcode credentials. Prefer `OBJECT_STORE_*` over `MINIO_*` for new code.

## Data Flow (Medallion — all Iceberg)

```
ENTSO-E API / Open-Meteo API / Kaggle CSV
    -> Bronze Iceberg (iceberg.bronze.{entso_generation,weather_hourly,...})
        append-only, day-partitioned on _ingestion_timestamp
    -> Silver Iceberg (iceberg.silver.{entso_cleaned,weather_cleaned,...})
        full overwrite; cleaned, typed, deduped, derived fields
    -> Gold Iceberg (iceberg.gold.energy_forecast_features)
        full overwrite; ML-ready feature matrix
        -- queryable via DuckDB (local) or Trino (federated)
    -> MLflow (XGBoost/LightGBM/LSTM with TimeSeriesSplit CV)
    -> deepagents (natural-language queries over Gold via MCP tools)
```

## Key Design Decisions

See `docs/solodshouse/decisions/` for full SDS ADR list. Summary:

| Decision | SoloDShouse stance | Supersedes |
|----------|-------------------|------------|
| DuckDB | Complements Trino for local queries | ADR-002 |
| K8s | Rejected — Docker Compose profiles, local-first | ADR-007 |
| OpenMetadata | Eliminated — dbt docs + MetricFlow + Adala | ADR-014 |
| Spark | On-demand compose profile only | ADR-016 |
| MinIO | Replaced by SeaweedFS (MinIO archived Apr 2026) | ADR-019 |
| Superset | Eliminated — Evidence.dev covers BI | SDS-022 |
| Ollama | Eliminated — llama.cpp/vLLM + LiteLLM | SDS-023 |
| Agent harness | deepagents (LangGraph) | SDS-024 |
| Domain | ENTSO-E energy (not ECB/DAX finance) | SDS-030 |

## Things to Watch Out For

- SeaweedFS replaces MinIO — use `OBJECT_STORE_*` env vars in new code, not `MINIO_*`
- Bronze data immutable — never overwrite, always append
- Trino stays for federated SQL; DuckDB is local/agent query path
- Hive Metastore stays — required by Trino for Iceberg catalog
- VPS (Hetzner CX23 `agent-hub-vps`) has 4 GB RAM + 40 GB disk only — never run LLM inference there
- LLM on VPS: route via LiteLLM -> Groq API (free) or SSH tunnel to Mac
- deepagents does NOT expose OpenAI-compatible API — FastAPI proxy required
- All SoloDShouse decisions document as `SDS-XXX` in `docs/solodshouse/decisions/`
- Original SoloLakehouse ADRs in `docs/sololakehouse_legacy_docs/decisions/` — read-only
- Tests run without Docker — mock `iceberg_io.scan_table` / `iceberg_io.overwrite_table`
- Python: always `uv` + `.venv`, never global pip

## UCM Module Coverage

| # | Module | How |
|:-:|--------|-----|
| 1 | Business Intelligence | Evidence.dev + Open WebUI |
| 2 | SQL | DuckDB + dbt + Trino |
| 3 | Tableau | Tableau Desktop -> DuckDB/PG |
| 4 | Python Programming | Full Python stack |
| 5 | NoSQL | MongoDB + pgvector |
| 6 | Statistics | Time-series stats, hypothesis tests |
| 7 | Data Mining | Anomaly detection, clustering (grid events) |
| 8 | Machine Learning | XGBoost/LightGBM forecasting |
| 9 | Data Visualization | Evidence.dev + Open WebUI |
| 10 | DL / CNN / RNN / LLMs | LSTM forecasting + llama.cpp/vLLM |
| 11 | Spark | PySpark on-demand profile |
| 12 | Big Data | Iceberg + Spark + SeaweedFS |
| 13 | Model Productivization | MLflow -> BentoML -> Langfuse |
| 14 | TFM Context | Energy company use case (IberGrid framing) |
| 15 | Applied Data Science | ENTSO-E -> lakehouse -> ML -> agent |

## Worktrees (Agent Isolation)

Three-agent setup. Each agent owns a zone — never crosses into another's zone.

| Agent | Worktree | Branch | Role |
|-------|----------|--------|------|
| **Claude Code** | `SoloDShouse/` (main) | `main` | Orchestrator — ADRs, task dispatch, PR merges, memory, deployments |
| **OpenCode** | `.superset/worktrees/.../opencode` | `agent/opencode-builder` | Primary builder — implements phases aggressively and autonomously |
| **Pi agent** | `.superset/worktrees/.../pi-qa` | `agent/pi-qa` | Junior QA — tests, reviews, maintains `tests/` and `docs/solodshouse/gotchas/` |

**Rules:**
- OpenCode and Pi agent never push to `main` directly — always PR
- Claude Code reviews and merges PRs, never writes implementation code
- Pi agent scope: `tests/`, `docs/solodshouse/gotchas/` only — no implementation
- Task dispatch: claim tasks in `task.md` before starting, mark `in_progress`

```bash
git worktree list     # See active agent worktrees
```

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

Project indexed by GitNexus as **SoloDShouse** (2637 symbols, 3651 relationships, 70 execution flows). Use GitNexus MCP tools to understand code, assess impact, navigate safely.

> If any GitNexus tool warns index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report blast radius (direct callers, affected processes, risk level) to user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify changes only affect expected symbols and execution flows.
- **MUST warn user** if impact analysis returns HIGH or CRITICAL risk before proceeding.
- Exploring unfamiliar code → use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. Returns process-grouped results ranked by relevance.
- Need full context on specific symbol (callers, callees, execution flows) → use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit function, class, or method without first running `gitnexus_impact`.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/SoloDShouse/context` | Codebase overview, check index freshness |
| `gitnexus://repo/SoloDShouse/clusters` | All functional areas |
| `gitnexus://repo/SoloDShouse/processes` | All execution flows |
| `gitnexus://repo/SoloDShouse/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->