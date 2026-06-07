# Deployment Architecture

> How SoloDShouse runs across Mac (dev) and Hetzner VPS (staging).

```mermaid
C4Deployment
  title SoloDShouse — Deployment

  Deployment_Node(mac, "Mac Studio M4 Max", "macOS 26.4 / Apple Silicon / 64 GB RAM") {
    Deployment_Node(orbstack, "OrbStack", "Docker runtime (Apple Silicon native)") {
      Deployment_Node(core_p, "Profile: core") {
        Container(dagster_d, "Dagster", "Python")
        Container(trino_d, "Trino", "Java / 1.5 GB")
        Container(hive_d, "Hive Metastore", "Java / 400 MB")
        Container(pg_d, "PostgreSQL 17 + pgvector", "300 MB")
        Container(sweed_d, "SeaweedFS", "S3 / 150 MB")
      }
      Deployment_Node(ml_p, "Profile: ml (adds)") {
        Container(mlflow_d, "MLflow 3.x", "300 MB")
        Container(bento_d, "BentoML", "200 MB")
      }
      Deployment_Node(agent_p, "Profile: agent (adds)") {
        Container(deepag_d, "deepagents (LangGraph)", "200 MB")
        Container(owui_d, "Open WebUI", "300 MB")
        Container(litellm_d, "LiteLLM", "150 MB")
        Container(kotae_d, "kotaemon + RAG", "1-2 GB")
        Container(mem0_d, "mem0", "100 MB")
      }
      Deployment_Node(llm_p, "Profile: llm-7b / llm-70b (on-demand)") {
        Container(llamacpp_d, "llama.cpp", "5-55 GB depending on model")
      }
    }
  }

  Deployment_Node(vps, "Hetzner CPX21 VPS", "Ubuntu / 4 GB RAM / 40 GB disk / ~5 EUR/mo") {
    Deployment_Node(compose_vps, "Docker Compose") {
      Deployment_Node(core_vps, "Profile: core") {
        Container(dagster_v, "Dagster (core only)", "Python")
        Container(pg_v, "PostgreSQL 17", "300 MB")
        Container(sweed_v, "SeaweedFS", "150 MB")
      }
      Deployment_Node(agent_vps, "Profile: agent") {
        Container(fastapi_v, "FastAPI Proxy", "50 MB")
        Container(litellm_v, "LiteLLM to Groq API", "150 MB")
        Container(owui_v, "Open WebUI", "300 MB")
      }
    }
  }

  Deployment_Node(ext, "External Services") {
    Container(groq_ext, "Groq API", "Free LLM tier")
    Container(entsoe_ext, "ENTSO-E API", "Energy data")
    Container(gh_ext, "GitHub Actions", "CI: pytest + ruff + mypy")
  }

  Rel(litellm_v, groq_ext, "LLM calls (VPS has no local GPU)", "HTTPS")
  Rel(litellm_d, llamacpp_d, "LLM calls (Mac has GPU)", "HTTP")
  Rel(dagster_d, entsoe_ext, "Data ingestion", "HTTPS")
  Rel(dagster_v, entsoe_ext, "Data ingestion", "HTTPS")
  Rel(gh_ext, mac, "CI pushes image to ghcr.io", "HTTPS")
```

## Resource Budget

| Profile | Mac RAM | VPS RAM | Notes |
|---------|:-------:|:-------:|-------|
| `core` | ~2.8 GB | ~2.8 GB | Safe on VPS |
| `ml` | ~3.3 GB | — | Mac only |
| `agent` | ~5.4 GB | ~3.5 GB | VPS: no kotaemon/mem0 |
| `full` | ~6.6 GB | — | Mac only |
| `llm-7b` | ~12.6 GB | — | Mac only |
| `llm-70b` | ~56.6 GB | — | Mac only (64 GB RAM needed) |

> VPS hard limit: 4 GB RAM. Never run LLM inference there — route via LiteLLM to Groq API.
