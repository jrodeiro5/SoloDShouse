# SoloDShouse — TFM Architecture Guide

> **Master's Thesis (TFM) — Universidad Complutense de Madrid**
> **Domain**: Energy data analytics (ENTSO-E) + ML/AI agents
> **Stack**: Python-first, local-first, LangChain ecosystem
> **Date**: June 2026
> **Repo**: `github.com/jrodeiro5/SoloDShouse`

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Domain & Data](#2-domain--data)
3. [Complete Tech Stack](#3-complete-tech-stack)
4. [Architecture Decisions](#4-architecture-decisions)
5. [Deployment Architecture](#5-deployment-architecture)
6. [UCM Module Coverage](#6-ucm-module-coverage)
7. [References](#7-references)

---

## 1. Project Overview

### 1.1 What Is SoloDShouse

SoloDShouse is a **local-first data lakehouse + AI agent platform** for energy data analytics, built as a TFM at UCM. It evolves the SoloLakehouse v2.5 reference implementation from financial data (ECB/DAX) into an energy-focused platform with a natural-language analytics agent powered by the LangChain ecosystem.

Three layers:

```
┌─────────────────────────────────────────────────────┐
│  Layer 3: AI Agent Layer                            │
│  deepagents + Open WebUI + ToolUniverse             │
│  "Pregunta a la IA sobre los datos"                 │
├─────────────────────────────────────────────────────┤
│  Layer 2: ML & Analytics Layer                      │
│  MLflow + BentoML + Evidence.dev + Spark            │
├─────────────────────────────────────────────────────┤
│  Layer 1: Lakehouse Layer                           │
│  DuckDB + dbt + Iceberg + SeaweedFS + Dagster       │
│  Medallion (Bronze → Silver → Gold)                 │
└─────────────────────────────────────────────────────┘
```

### 1.2 Why Energy Data

| Factor | Rationale |
|--------|-----------|
| **UCM location** | Madrid, Spain → ENTSO-E (European grid) is the natural data domain |
| **Real API** | ENTSO-E Transparency Platform, free registration, `entsoe-py` client |
| **Rich structure** | Time-series + spatial (grid nodes) + weather (Open-Meteo) → complex joins, realistic ML |
| **Public relevance** | Energy transition, renewable forecasting, grid analytics — high-impact topic |
| **No API keys needed for demo** | ENTSO-E data is EU-mandated public; Open-Meteo is free |

### 1.3 Design Constraints

| Constraint | Implication |
|------------|-------------|
| **Local-first** | Entire stack runs on Mac Studio M4 Max (64GB). No cloud dependency for development |
| **Python-first** | All core components are Python. Non-Python services (SeaweedFS/Go, Qdrant/Rust) are infrastructure only |
| **Single-machine deployable** | Docker Compose, not Kubernetes |
| **Self-hosted** | No vendor lock-in. Everything open-source or source-available |
| **TFM-gradable** | Must demonstrate all 15 UCM modules, not just a subset |

---

## 2. Domain & Data

### 2.1 Data Sources

| Source | Data | Access | Coverage |
|--------|------|--------|----------|
| **ENTSO-E Transparency Platform** | Generation, consumption, cross-border flows, day-ahead prices | Free API, `entsoe-py` client, registration required | EU + UK, 38 TSOs, 15min/1h resolution |
| **Open-Meteo** | Historical & forecast weather (temp, wind, solar) | Free API, no key needed | Global, 1h-3h resolution |
| **Kaggle: Hourly Energy Spain** | Demand/generation/prices/weather | CC0, CSV | Spain, 2015-2018, 35K rows |

### 2.2 Medallion Architecture

```
ENTSO-E API  ──► Bronze (raw append, Iceberg) ──► Silver (cleaned, typed) ──► Gold (features, joins)
Open-Meteo   ──► Bronze (raw append, Iceberg) ──► Silver (cleaned, typed) ──► Gold (features, joins)
Kaggle CSV   ──► Bronze (raw ingest, Iceberg) ──►                            (weather + generation features)

Gold features: time-series with targets for ML:
  - Generation forecast (next 24h per fuel type)
  - Price prediction (day-ahead, intraday)
  - Anomaly detection (grid events)
  - Cross-border flow classification
```

### 2.3 Key ML Use Cases

| Use Case | Type | UCM Module |
|----------|------|------------|
| Renewable generation forecasting (solar + wind) | Time-series regression | ML + DL (LSTM) |
| Day-ahead price prediction | Regression + feature engineering | ML + stats |
| Grid event anomaly detection | Unsupervised (isolation forest, autoencoder) | Data mining + DL |
| Cross-border flow classification | Supervised classification | ML |
| Natural-language data queries via agent | LLM + RAG + SQL | AI / LLMs |

---

## 3. Complete Tech Stack

### 3.1 Inventory

| Layer | Component | Role | RAM | Language |
|-------|-----------|------|:---:|:--------:|
| Object Storage | SeaweedFS | S3-compatible storage (replaces MinIO) | ~200MB | Go |
| Metadata DB | PostgreSQL 17 | App state, Hive Metastore, MLflow | ~200MB | — |
| Document DB | MongoDB 7 | Metadata, UCM module 5 | ~500MB | C++ |
| Vector DB | Qdrant | RAG embeddings, agent memory | ~300MB | Rust |
| Table Format | Apache Iceberg | Medallion storage format | — | library |
| SQL Engine | DuckDB | Local OLAP query engine | ~100MB | C++ |
| Transformations | dbt-core | SQL transformations, lineage | ~50MB | Python |
| Orchestration | Dagster | Asset pipeline, scheduling | ~500MB | Python |
| ML Tracking | MLflow 3.x | Experiment tracking, model registry | ~300MB | Python |
| ML Serving | BentoML | Classical model serving | ~200MB | Python |
| LLM Dev | Ollama | Local LLM (7B models) | ~5GB | Go |
| LLM Prod | vLLM | Production LLM serving | ~5-8GB | Python |
| LLM Gateway | LiteLLM | Unified API for 100+ LLM providers | ~200MB | Python |
| Agent Harness | deepagents | LangChain batteries-included agent framework | ~500MB | Python |
| MCP Tools | ToolUniverse | 1000+ scientific ML tools via MCP | ~200MB | Python |
| RAG | LlamaIndex | Document indexing + retrieval | ~200MB | library |
| Agent Memory | mem0 | Structured agent memory layer | ~200MB | Python |
| LLM Eval | Opik | LLM evaluation metrics | ~300MB | Python |
| Chat UI | Open WebUI | Self-hosted chat interface | ~300MB | Python |
| BI | Evidence.dev | dbt-native BI, git-deployable reports | ~200MB | Node |
| Spatial | PostGIS | Geospatial queries (grid nodes) | +50MB | extension |
| Compute | Spark | Big data processing (UCM mod 11) | ~4GB | JVM |
| Observability | Grafana + Prometheus + Loki | Metrics, logs, dashboards | ~1GB | Go |
| Reverse Proxy | nginx | TLS, routing, rate limiting | ~50MB | C |

### 3.2 Python Libraries (in-process)

| Library | Role |
|---------|------|
| langchain-core | Base abstractions |
| langgraph | Agent graph runtime |
| deepagents | Agent harness (subagents, skills, context mgmt) |
| llama-index | RAG, document indexing |
| langchain-community | DuckDB SQL tool, integrations |
| langchain-mcp-adapters | MCP tool integration (ToolUniverse) |
| langsmith-sdk | Tracing, evaluation |
| entsoe-py | ENTSO-E API client |
| openmeteo-requests | Open-Meteo API client |
| pyiceberg | Iceberg table operations |
| dbt-duckdb | dbt + DuckDB adapter |
| dagster | Pipeline orchestration |
| mlflow | Experiment tracking |
| bentoml | Model serving |
| mem0 | Agent memory |
| opik | LLM evaluation |
| pydantic | Data validation |
| structlog | Structured logging |
| pytest | Testing |
| ruff | Linting |
| mypy | Type checking |

---

## 4. Architecture Decisions

### ADR-001: Local-First Over Cloud

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | TFM must demonstrate local capability. Mac Studio M4 Max (64GB) is powerful enough. Avoid cloud costs. |
| **Decision** | All components run on a single machine via Docker Compose. Cloud is only for CI/CD and optional VPS deployment. |
| **Alternatives** | **AWS/GCP** — rejected for cost and reproducibility. **Hetzner VPS only** — rejected: 4GB RAM can't run LLM locally. |

### ADR-002: SeaweedFS Over MinIO

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | MinIO CE **archived April 25, 2026** (repo banner: "NO LONGER MAINTAINED", last release `RELEASE.2025-10-15`). SoloDShouse needs an actively maintained S3-compatible store. |
| **Decision** | Replace MinIO with SeaweedFS. Apache 2.0, actively maintained, S3-compatible API, single binary. |
| **Alternatives** | **Keep MinIO** — rejected: archived, no security patches. **Rook/Ceph** — rejected: overkill for single-node. **Local filesystem** — rejected: no S3 API for Iceberg/MLflow. |
| **Reference** | [ADR-019](decisions/ADR-019-minio-seaweedfs-deferral.md) deferred this; MinIO archiving makes it mandatory now. |

### ADR-003: Deep Agents (LangChain Suite) Over Raw LangGraph

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | Building an analytics agent requires filesystem access, subagent delegation, context management, skills, planning, and MCP integration. Raw LangGraph requires wiring all of this manually. |
| **Decision** | Use `deepagents` (`create_deep_agent`) as the agent harness on top of LangGraph. Provides subagents, skills, filesystem, planning, MCP, and streaming out of the box. All in Python. |
| **Alternatives** | **Raw LangGraph** — more plumbing, no pre-built subagent/skills/context management. **CrewAI** — role-based agents, less flexible, no LangChain ecosystem. **AutoGen** — multi-agent conversation focus, not analytics. **Claude Agent SDK** — Anthropic-only, not Python-first. |
| **Reference** | `https://github.com/langchain-ai/deepagents` (24k★, MIT, Python) |

### ADR-004: Open WebUI + FastAPI Proxy Over NAO Chat

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | Need a self-hosted chat UI that connects to a custom LangChain agent backend. NAO is a complete analytics agent platform with its own backend (TypeScript/Fastify), making it harder to replace the agent layer. |
| **Decision** | Use Open WebUI (140k★) as the chat interface. Build a thin FastAPI proxy (~50 LOC) that translates OpenAI-compatible requests to deepagents calls. Open WebUI handles auth, multi-user, chat history, RAG, and admin panel. |
| **Alternatives** | **NAO directly** — TypeScript backend, harder to integrate with Python agent. **Streamlit** — not a chat UI, would need to build from scratch. **Custom Svelte/React UI** — reinventing the wheel. |
| **Reference** | `https://github.com/open-webui/open-webui` (140k★, Python, MIT) |

### ADR-005: ToolUniverse as MCP Tool Layer

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | The analytics agent needs domain-specific tools: weather queries, ENTSO-E API, academic search, time-series analysis. Building each from scratch is expensive. |
| **Decision** | Integrate ToolUniverse (mims-harvard, 1.4k★) as the MCP tools layer. Provides 1000+ scientific ML tools. LangChain's `langchain-mcp-adapters` loads them into deepagents natively. Custom ENTSO-E tools registered alongside. |
| **Alternatives** | **Build custom tools only** — slower, less scope. **No MCP layer** — tools would be ad-hoc, not reusable. |
| **Reference** | `https://github.com/mims-harvard/ToolUniverse` (1.4k★, Python, Apache 2.0) |

### ADR-006: DuckDB + dbt Over Trino for Local Queries

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | Existing SoloLakehouse uses Trino (1.5GB JVM) + Hive Metastore for SQL queries. For the energy domain, we need lighter, Python-native querying for the agent. |
| **Decision** | Add DuckDB + dbt-duckdb as the primary local query engine. Keep Iceberg as storage format. DuckDB is in-process (~100MB), zero-config, and directly queryable from Python. Trino remains available as an alternative for UCM module 2 (SQL). |
| **Alternatives** | **Trino only** — 1.5GB JVM, overkill for local. **SQLite** — no Iceberg, no columnar. **Polars** — no SQL interface for non-Python users. |
| **Reference** | `https://duckdb.org/`, dbt-duckdb adapter, pyiceberg |

### ADR-007: LiteLLM as LLM Gateway

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | The agent needs to switch between local Ollama, vLLM, and external APIs (OpenAI, Anthropic). A unified interface prevents vendor lock-in. |
| **Decision** | Use LiteLLM as the LLM proxy layer. Exposes OpenAI-compatible API. Routes to Ollama (Mac), vLLM (Mac), or external APIs. Costs ~200MB. |
| **Alternatives** | **Direct Ollama API** — can't route to external APIs. **Portkey** — SaaS, not self-hosted. **Custom router** — reinventing. |
| **Reference** | `https://github.com/BerriAI/litellm` — user starred |

### ADR-008: VPS + Mac Hybrid Deployment

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | The €5/month Hetzner VPS (CPX21: 3 vCPU, 4GB RAM, 80GB SSD) cannot run LLM inference locally. But it can run services. |
| **Decision** | Split deployment: **VPS** runs always-on services (PG, DuckDB, SeaweedFS, Open WebUI, deepagents, LiteLLM, Qdrant, Grafana, nginx) at ~2.5GB. **Mac Studio** runs LLM inference (Ollama/vLLM), Spark, and heavy compute. CI/CD via GitHub Actions → GHCR → VPS SSH deploy. |
| **Alternatives** | **VPS only** — 4GB can't run LLM + services. **Cloud LLM API only** — recurring cost, less control. |
| **Reference** | Hetzner CPX21 (€4.51/mo, 3vCPU/4GB/80GB + €0.50 IPv4) |

### ADR-009: Grafana + Loki + Prometheus for Observability

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | Need system metrics (CPU, RAM, disk, network), LLM call traces, and application logs. LangSmith handles agent traces; system monitoring is separate. |
| **Decision** | Use Grafana + Prometheus (metrics) + Loki (logs) + Promtail (log collector). Total ~1GB. |
| **Alternatives** | **SigNoz** — OpenTelemetry-native, heavier for 4GB VPS. **Netdata** — single-node only, no centralized logging. **Dozzle** — Docker logs only, no metrics. **Datadog/Grafana Cloud** — SaaS cost. |

### ADR-010: Evidence.dev Over Superset for BI

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | Existing SoloLakehouse uses Apache Superset (heavy, Python). For the TFM, a lighter, git-deployable BI is better. |
| **Decision** | Add Evidence.dev for structured BI reports (git-versioned, dbt-native markdown). Keep Superset optionally available. Open WebUI agent handles ad-hoc queries. |
| **Alternatives** | **Superset only** — heavy (~500MB), not git-native. **Metabase** — Java, overkill. **Streamlit dashboards** — accepted for custom viz. |

### ADR-011: Opik + LangSmith for LLM Evaluation

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | TFM requires quantitative evaluation. LLM-generated SQL queries need accuracy metrics beyond "looks correct." |
| **Decision** | LangSmith for agent trace observability (free tier). Opik for LLM evaluation metrics (correctness, hallucination, latency). YAML test suite: prompt → expected SQL → pass/fail. |
| **Alternatives** | **Only LangSmith** — no evaluation metrics. **Only Opik** — no trace observability. **Custom eval harness** — slower to build. |

### ADR-012: Qdrant + LlamaIndex for RAG

| | |
|---|----------|
| **Status** | ✅ Accepted |
| **Context** | The agent needs to retrieve context from documentation (ENTSO-E API docs, dbt docs, business rules) and past query patterns. |
| **Decision** | Qdrant as vector store (lightweight, Rust, 300MB). LlamaIndex as RAG orchestration layer. Embeddings via Ollama. Open WebUI's document RAG for user-facing chat; LlamaIndex for agent-internal retrieval. |
| **Alternatives** | **ChromaDB** — slower at scale. **PGVector** — adds load to PostgreSQL. **Pinecone** — SaaS. **FAISS** — in-memory only. |

---

## 5. Deployment Architecture

### 5.1 Environments

```
DEV (Mac Studio, local)
  Full stack + Ollama/vLLM
  docker compose -f docker-compose.mac.yml up
  make dev
  LLM: local Ollama 7B
         │ git push
         ▼
CI (GitHub Actions)
  Build multi-arch Docker images → ghcr.io/jrodeiro5/solodshouse-*
  Run tests (pytest) + lint (ruff) + typecheck (mypy)
         │ SSH deploy
         ▼
STAGING (Hetzner CPX21, 4GB RAM)
  Always-on: PG + DuckDB + SeaweedFS + Open WebUI + deepagents
             + LiteLLM + Qdrant + Grafana/Loki + nginx
  LLM: external API (Groq free / OpenAI) or tunnel to Mac
  docker compose -f docker-compose.vps.yml up -d
  URL: https://solodshouse.example.com
```

### 5.2 Docker Compose Profiles

| Profile | Services | RAM | Use Case |
|---------|----------|:---:|----------|
| `core` | PG + DuckDB + SeaweedFS + Dagster | ~1.5GB | Data pipeline only |
| `ml` | core + MLflow + Qdrant + Opik | ~3GB | ML experiments |
| `agent` | ml + deepagents + Open WebUI + LiteLLM + ToolUniverse | ~4.5GB | Chat + agent |
| `full` | agent + Grafana + Loki + MongoDB | ~6GB | Everything except LLM |
| `llm-7b` | full + Ollama (7B) | ~11GB | With local LLM |
| `llm-70b` | full + vLLM (70B) | ~55GB | Production-grade LLM |

### 5.3 CI/CD Pipeline

```yaml
# .github/workflows/build-and-deploy.yml
on: push to main

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - buildx build --platform linux/amd64 -t ghcr.io/.../solodshouse-deepagents
      - push to ghcr.io
  deploy:
    needs: build
    steps:
      - ssh hetzner "cd /opt/solodshouse && docker compose pull && up -d"
```

### 5.4 LLM Routing

```
deepagents → LiteLLM (litellm:4000)
               ├── Ollama (Mac, tailscale:11434) ─── dev
               ├── vLLM (Mac, tailscale:8000) ─────── large models
               ├── Groq API (free tier) ───────────── fallback
               └── OpenAI API (paid) ──────────────── production
```

---

## 6. UCM Module Coverage

| # | Module | How SoloDShouse Covers It | Status |
|:-:|--------|---------------------------|:------:|
| 1 | Business Intelligence | Evidence.dev dashboards + Open WebUI queries | ✅ |
| 2 | SQL | DuckDB SQL, dbt transformations, Trino alternative | ✅ |
| 3 | Tableau | Tableau Desktop connected to DuckDB/PostgreSQL | ⚠️ External tool |
| 4 | Python Programming | Full Python stack (ingestion → agent) | ✅ |
| 5 | NoSQL Databases | MongoDB (metadata) + Qdrant (vectors) | ✅ |
| 6 | Statistics | Time-series stats, profiling, hypothesis tests | ✅ |
| 7 | Data Mining | Anomaly detection, clustering (grid events) | ✅ |
| 8 | Machine Learning | XGBoost/LightGBM forecasts, scikit-learn | ✅ |
| 9 | Data Visualization | Evidence.dev dashboards + Open WebUI charts | ✅ |
| 10 | Deep Learning / CNN / RNN / LLMs | LSTM forecasting + Ollama/vLLM for agent | ✅ |
| 11 | Spark | PySpark batch processing alongside DuckDB | ✅ |
| 12 | Big Data Technologies | HDFS via Spark, Iceberg table format | ✅ |
| 13 | Model Productivization | MLflow → BentoML serving → monitoring | ✅ |
| 14 | Master's Thesis Context | Energy company use case | ⚠️ Need context |
| 15 | Applied Data Science | End-to-end: ENTSO-E → lakehouse → ML → agent | ✅ |

**Gaps**: Mod 3 (Tableau) — connect Tableau Desktop to DuckDB directly. Mod 14 — frame around a fictional or real energy utility ("IberGrid").

---

## 7. References

### Repositories Evaluated

| Repo | Stars | License | Verdict |
|------|:-----:|:-------:|:-------:|
| [SoloLakehouse](https://github.com/Jiahong-Que-9527/SoloLakehouse) | — | — | **Base** — original reference |
| [deepagents](https://github.com/langchain-ai/deepagents) | 24k | MIT | ✅ **Use** — agent harness |
| [langgraph](https://github.com/langchain-ai/langgraph) | 34k | MIT | ✅ **Use** — graph runtime |
| [langchain](https://github.com/langchain-ai/langchain) | 138k | MIT | ✅ **Use** — framework |
| [Open WebUI](https://github.com/open-webui/open-webui) | 140k | MIT | ✅ **Use** — chat UI |
| [ToolUniverse](https://github.com/mims-harvard/ToolUniverse) | 1.4k | Apache 2.0 | ✅ **Use** — MCP tools |
| [SeaweedFS](https://github.com/seaweedfs/seaweedfs) | — | Apache 2.0 | ✅ **Use** — object store |
| [litellm](https://github.com/BerriAI/litellm) | — | MIT | ✅ **Use** — LLM gateway |
| [llama-index](https://github.com/run-llama/llama_index) | — | MIT | ✅ **Use** — RAG |
| [mem0](https://github.com/mem0ai/mem0) | — | Apache 2.0 | ✅ **Use** — memory |
| [opik](https://github.com/comet-ml/opik) | — | Apache 2.0 | ✅ **Use** — eval |
| [NAO](https://github.com/getnao/nao) | 1.2k | — | ❌ **Rejected** — TS backend |
| [kubetorch](https://github.com/run-house/kubetorch) | 1.2k | Apache 2.0 | ❌ **Rejected** — K8s dependency |
| [AutoScientists](https://github.com/mims-harvard/AutoScientists) | 548 | — | ❌ **Rejected** — 1 commit, biomedical |
| [mini-swe-agent](https://github.com/SWE-agent/mini-swe-agent) | 5k | MIT | ❌ **Rejected** — SWE-bench focus |
| [autoswagger](https://github.com/intruder-io/autoswagger) | 1.9k | BSD-3 | ❌ **Rejected** — API security |
| [autodistill](https://github.com/autodistill/autodistill) | 2.7k | Apache 2.0 | ❌ **Rejected** — CV, abandoned |
| [MinIO](https://github.com/minio/minio) | — | AGPL 3.0 | ❌ **Archived Apr 2026** |

### Tools & Services

| Tool | Role | URL |
|------|------|-----|
| ENTSO-E | Energy data API | transparency.entsoe.eu |
| Open-Meteo | Weather data | open-meteo.com |
| DuckDB | OLAP engine | duckdb.org |
| dbt | SQL transformations | getdbt.com |
| pyiceberg | Iceberg Python client | py.iceberg.apache.org |
| Qdrant | Vector database | qdrant.tech |
| Evidence.dev | BI framework | evidence.dev |
| Ollama | Local LLM | ollama.com |
| vLLM | LLM serving | github.com/vllm-project/vllm |
| LangSmith | LLM observability | smith.langchain.com |
| Grafana + Loki | Observability | grafana.com |
| Hetzner Cloud | VPS | hetzner.com/cloud |
| GHCR | Docker registry | ghcr.io |

### Existing ADRs (SoloLakehouse v2.5)

20 ADRs in `docs/decisions/` covering Trino, Iceberg, Dagster, MinIO deferral, OpenMetadata, v3 governance, and more. This guide builds on those decisions.

---

*Generated: 2026-06-06*
*Status: Active architecture guide for SoloDShouse TFM direction*
