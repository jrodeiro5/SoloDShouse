# SDS-038: LLM Gateway Model Selection — Tool Use and GDPR Posture

**Status:** Accepted  
**Date:** 2026-06-07  
**Deciders:** jrodeiro  
**Context:** VPS gateway role (SDS-037), Agent layer design (SDS-024)

---

## Context

SoloDShouse agents (deepagents + FastAPI proxy) require LLM inference on the Hetzner CX23 VPS (2 vCPU / 4 GB RAM). The VPS cannot run local inference — no GPU, insufficient RAM for any model beyond ~3B. Remote LLM API required.

Key constraints:
- Must support **tool use / function calling** — agents call MCP tools (Dagster status, MLflow registry, Gold Iceberg layer queries)
- Must be **free or near-free** — project budget is VPS cost only (~€4.83/mo)
- GDPR posture: preferred EU-resident infra, but TFM academic context reduces legal exposure; no real user PII, domain data (ENTSO-E grid) is public
- Already in stack: **LiteLLM** as unified gateway — model selection is a config change, not a code change

---

## Decision

**Primary model:** `llama-3-groq-70b-tool-use` via Groq API, routed through LiteLLM.

**Fallback model:** `llama3-70b-8192` (Groq, same infra) when tool-use fine-tune not needed.

**Local inference (Mac only, dev/heavy tasks):** `llama.cpp` or `vLLM` — never on VPS.

---

## Rationale

### Why Groq

| Factor | Assessment |
|--------|-----------|
| Tool use | `llama-3-groq-70b-tool-use` fine-tuned for function calling; parallel tool calls supported |
| Speed | Groq LPU inference — fastest available at free tier |
| Cost | Free tier sufficient for TFM workload |
| LiteLLM integration | Native Groq provider; zero extra code |
| Parallel tool calls | Supported — critical for agentic workflows hitting multiple MCP tools |

### Why not Mistral API

Mistral operates EU-resident infrastructure (better GDPR posture) but:
- Free tier limited and less generous than Groq
- Tool use quality lower than Llama-3-70B-Tool-Use at equivalent size
- For TFM context with public domain data, EU-resident infra is not required

### GDPR assessment

Groq is a US company. Data crosses Atlantic. Mitigations:
- Groq has DPA, SOC 2, EU/UK representatives, Data Privacy Framework certification
- Project data: ENTSO-E grid generation (public) + Open-Meteo weather (public) — no PII
- TFM academic context: not a commercial product, no real end users
- **Risk level: Low** for this context

If project transitions to commercial or processes real user data, revisit in favor of Mistral or a self-hosted alternative.

---

## Implementation

LiteLLM config (`litellm_config.yaml`):

```yaml
model_list:
  - model_name: agent-primary
    litellm_params:
      model: groq/llama-3-groq-70b-tool-use
      api_key: os.environ/GROQ_API_KEY

  - model_name: agent-fallback
    litellm_params:
      model: groq/llama3-70b-8192
      api_key: os.environ/GROQ_API_KEY

router_settings:
  fallbacks:
    - agent-primary: [agent-fallback]
```

deepagents / FastAPI proxy points to LiteLLM endpoint — no model reference in agent code.

---

## Alternatives Considered

| Option | Rejected because |
|--------|-----------------|
| Mistral API | Lower tool-use quality, stricter free tier |
| NVIDIA llm-router | Redundant — LiteLLM already handles routing |
| Local inference on VPS | VPS has 4 GB RAM, no GPU — infeasible |
| OpenAI API | Costs money; no free tier for production use |

---

## Consequences

- VPS agents call Groq via LiteLLM — single API key to manage (`GROQ_API_KEY` in VPS env)
- Groq free tier rate limits apply — Langfuse traces will surface if limits hit
- If Groq raises prices or kills free tier, swap to Mistral via LiteLLM config change only
- Revisit if TFM evolves to real users or non-public data

---

## Related

- SDS-024: Agent harness (deepagents / LangGraph)
- SDS-037: VPS gateway role
- SDS-039: PII detection layer (Presidio)
