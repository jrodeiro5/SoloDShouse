# SoloDShouse

<h3 align="center">Solo Data Science House</h3>

<p align="center">
  A local-first data science + AI agent platform for energy analytics.<br>
  Built as a TFM at Universidad Complutense de Madrid.
</p>

<p align="center">
  DuckDB · Iceberg · Dagster · MLflow · deepagents · LiteLLM · Evidence.dev
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.13%2B-blue.svg" alt="Python 3.13+">
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License">
  <img src="https://img.shields.io/badge/runtime-Docker%20Compose-2496ED.svg" alt="Docker Compose">
  <img src="https://img.shields.io/badge/table%20format-Iceberg-5C7CFA.svg" alt="Apache Iceberg">
  <img src="https://img.shields.io/badge/TFM-UCM%20Madrid-red.svg" alt="TFM UCM">
</p>

---

> **Fork of [SoloLakehouse v2.5](https://github.com/Jiahong-Que-9527/SoloLakehouse).**
> Original docs preserved in [`docs/sololakehouse_legacy_docs/`](docs/sololakehouse_legacy_docs/).
> SoloDShouse ADRs and docs live in [`docs/solodshouse/`](docs/solodshouse/).

---

## What Is This

SoloDShouse is a **local-first data science and AI agent platform** for European energy data analytics.

It extends the SoloLakehouse v2.5 lakehouse baseline with:
- An **ML layer** for renewable forecasting, price prediction, and anomaly detection
- An **AI agent layer** (deepagents + Open WebUI) for natural-language data queries
- A **local LLM layer** (llama.cpp / vLLM / Groq) routed through LiteLLM

Everything runs on a Mac Studio M4 Max (64 GB) for development and a EUR 5/month Hetzner VPS for staging. No cloud dependency, no surprise bills.

**This is a TFM** — it must demonstrate all 15 modules of the UCM Master in Big Data, Data Science & AI. The platform covers all 15.

## Architecture

```
+-------------------------------------------------------------------+
|  Layer 3: AI Agent                                                |
|  deepagents (LangGraph) + Open WebUI + ToolUniverse (MCP)        |
|  "Ask the AI about the energy data"                               |
+-------------------------------------------------------------------+
|  Layer 2: ML & Analytics                                          |
|  MLflow + BentoML + Evidence.dev + LSTM/XGBoost forecasting       |
+-------------------------------------------------------------------+
|  Layer 1: Lakehouse                                               |
|  DuckDB + dbt + Iceberg + SeaweedFS + Dagster + Trino             |
|  Medallion: Bronze -> Silver -> Gold (all Iceberg)                |
+-------------------------------------------------------------------+
```

## Domain: European Energy Data

| Source | Data | Access |
|--------|------|--------|
| ENTSO-E Transparency Platform | Generation, consumption, cross-border flows, day-ahead prices | Free API (entsoe-py), registration required |
| Open-Meteo | Historical + forecast weather (temperature, wind, solar) | Free, no key needed |
| Kaggle: Hourly Energy Spain | Demand/generation/prices 2015-2018 | CC0, CSV |

**Why energy?** UCM Madrid is the natural context for ENTSO-E (European grid). Real-world complexity: time-series + spatial (grid nodes) + weather joins + regulatory relevance. Public API, no keys needed for demo.

## Tech Stack

| Layer | Component | Note |
|-------|-----------|------|
| Object Storage | SeaweedFS | Replaces MinIO (archived Apr 2026) |
| Metadata DB | PostgreSQL 17 + pgvector + PostGIS | Vectors + geo |
| Table Format | Apache Iceberg | All layers via pyiceberg |
| Query Engine | Trino + DuckDB | Trino: federated; DuckDB: local/agent |
| Transformations | dbt-core + dbt-duckdb | MetricFlow for metrics |
| Orchestration | Dagster | Assets, schedules, sensors |
| ML Tracking | MLflow 3.x | Experiment registry |
| ML Serving | BentoML | Classical models |
| Agent Harness | deepagents (LangGraph) | + FastAPI proxy |
| Chat UI | Open WebUI | Self-hosted |
| LLM Gateway | LiteLLM | Routes to llama.cpp / vLLM / Groq |
| RAG | kotaemon + LlamaIndex | Multi-user, PDF, citations |
| Agent Memory | mem0 | Structured memory |
| MCP Tools | ToolUniverse + FastMCP | 1000+ scientific tools |
| LLM Audit | garak (NVIDIA) | Vulnerability scanner |
| Agent Governance | AGT (Microsoft) | Policy enforcement |
| Data Labeling | Adala | Quality assurance |
| Observability | Langfuse + Prometheus + Alertmanager | LLM traces + metrics + alerts |
| BI | Evidence.dev | Markdown-first, git-deployable |
| NoSQL | MongoDB 7 | UCM module 5 |
| Docs | Astro Starlight | Static docs site |

## Deployment

```
DEV (Mac Studio M4 Max, 64 GB, local)
  docker compose --profile full up
  LLM: llama.cpp / vLLM local

CI (GitHub Actions)
  build -> ghcr.io/jrodeiro5/solodshouse-*
  test -> pytest + ruff + mypy

STAGING (Hetzner CPX21, 4 GB, ~EUR 5/mo)
  docker compose --profile core --profile agent up -d
  LLM: Groq API (free) or SSH tunnel to Mac
```

## Quick Start

```bash
git clone https://github.com/jrodeiro5/SoloDShouse.git
cd SoloDShouse
make setup
make verify
make demo
```

Key UIs after `make up`:

| UI | URL |
|----|-----|
| Dagster | http://localhost:3000 |
| Open WebUI | http://localhost:3001 |
| Evidence.dev | http://localhost:3002 |
| MLflow | http://localhost:5000 |
| Trino | http://localhost:8080 |
| SeaweedFS | http://localhost:9333 |
| Portal | http://localhost:8090 |

## Monthly Cost

| Item | Cost |
|------|:----:|
| Mac Studio M4 Max | owned |
| Hetzner CPX21 VPS | EUR 5.01 |
| Groq API (LLM on VPS) | EUR 0 (free tier) |
| ENTSO-E API | EUR 0 |
| Open-Meteo API | EUR 0 |
| **Total** | **~EUR 5-25/mo** |

## UCM Module Coverage

| # | Module | How |
|:-:|--------|-----|
| 1 | Business Intelligence | Evidence.dev + Open WebUI |
| 2 | SQL | DuckDB + dbt + Trino |
| 3 | Tableau | Tableau Desktop -> DuckDB/PG |
| 4 | Python Programming | Full Python stack |
| 5 | NoSQL Databases | MongoDB + pgvector |
| 6 | Statistics | Time-series stats, hypothesis tests |
| 7 | Data Mining | Anomaly detection, clustering (grid events) |
| 8 | Machine Learning | XGBoost/LightGBM energy forecasting |
| 9 | Data Visualization | Evidence.dev + Open WebUI charts |
| 10 | Deep Learning / CNN / RNN / LLMs | LSTM forecasting + llama.cpp/vLLM agent |
| 11 | Spark | PySpark on-demand profile |
| 12 | Big Data Technologies | Iceberg + Spark + SeaweedFS |
| 13 | Model Productivization | MLflow -> BentoML -> Langfuse monitoring |
| 14 | TFM Context | Energy utility use case (IberGrid framing) |
| 15 | Applied Data Science | ENTSO-E -> lakehouse -> ML -> agent |

## Documentation

- [TFM Architecture Guide](docs/solodshouse/tfm-architecture-guide.md)
- [Session Memory & Decisions](docs/solodshouse/session-memory.md)
- [SoloDShouse ADRs](docs/solodshouse/decisions/README.md) (SDS-XXX)
- [SoloLakehouse Legacy Docs](docs/sololakehouse_legacy_docs/README.md) (read-only)

## Origin

SoloDShouse is a fork of [SoloLakehouse](https://github.com/Jiahong-Que-9527/SoloLakehouse) v2.5.

Key divergences from upstream: domain pivot (ECB/DAX -> ENTSO-E), AI agent layer (deepagents), local LLM (llama.cpp/vLLM), SeaweedFS replaces MinIO, DuckDB added, OpenMetadata + Superset eliminated, Spark on-demand only, Evidence.dev as BI.

See [SDS ADRs](docs/solodshouse/decisions/README.md) for all fork decisions.

## License

[MIT](LICENSE)
