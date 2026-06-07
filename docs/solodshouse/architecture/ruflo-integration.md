# Ruflo Integration Plan

[Ruflo](https://github.com/ruvnet/ruflo) (formerly claude-flow) is a multi-agent harness for Claude Code: swarm coordination, self-learning memory, Graph RAG, and federated agent communication. Several plugins map directly to SoloDShouse capabilities.

## What Ruflo Provides

- **98 specialized agents** routed automatically via hooks
- **Swarm coordination** — multiple agents collaborate on a single task
- **Self-learning memory** — RuVector graph DB captures successful patterns; agents improve over time
- **Federation** — agents on Mac (dev) and Hetzner VPS (staging) communicate securely without leaking data
- **33 plugins** — install only what you need

Two install paths: Claude Code Plugin (slash commands only, zero files) vs full CLI (`npx ruflo init` — MCP server + hooks + 98 agents). SoloDShouse currently has `ruflo-core` as a Claude Code plugin.

## Plugin Priority

```mermaid
quadrantChart
    title Ruflo Plugin Priority for SoloDShouse
    x-axis "Low Effort" --> "High Effort"
    y-axis "Low Impact" --> "High Impact"

    ruflo-cost-tracker: [0.15, 0.90]
    ruflo-rag-memory: [0.30, 0.85]
    ruflo-intelligence: [0.45, 0.80]
    ruflo-observability: [0.20, 0.70]
    ruflo-federation: [0.70, 0.75]
    ruflo-agentdb: [0.40, 0.65]
    ruflo-security-audit: [0.30, 0.55]
    ruflo-swarm: [0.55, 0.60]
    ruflo-testgen: [0.35, 0.50]
    ruflo-adr: [0.10, 0.40]
    ruflo-sparc: [0.25, 0.35]
    ruflo-docs: [0.20, 0.30]
```

## Plugin Mapping

| Plugin | SoloDShouse Use Case | Priority |
|--------|---------------------|:--------:|
| **ruflo-cost-tracker** | Track LLM token costs — the platform studies AI inference cost; it should also instrument its own | 🔴 High |
| **ruflo-rag-memory** | Graph RAG over energy data (hybrid search + graph hops) vs flat mem0 — GPU→benchmark→pricing→carbon chain | 🔴 High |
| **ruflo-intelligence** | Self-learning from past agent queries; routing and query plans improve after ~10 interactions | 🔴 High |
| **ruflo-observability** | Structured traces + metrics complementing Langfuse — single surface across Dagster + agents | 🟡 Medium |
| **ruflo-federation** | Mac (dev) ↔ Hetzner VPS (staging) agent federation without raw data leakage | 🟡 Medium |
| **ruflo-agentdb** | RuVector fast vector DB for agent memory; graph-aware retrieval vs flat mem0 | 🟡 Medium |
| **ruflo-security-audit** | CVE scan on ingestion/collectors/ + agents/ before each release | 🟡 Medium |
| **ruflo-swarm** | Coordinate parallel Dagster + deepagents tasks; useful for multi-country ENTSO-E ingestion | 🟡 Medium |
| **ruflo-testgen** | Auto-generate missing tests for Phase F transforms + Phase H dbt models | 🟢 Low |
| **ruflo-adr** | Automate SDS-XXX ADR scaffolding (currently manual) | 🟢 Low |

## Integration Architecture

```mermaid
flowchart TD
    subgraph ruflo["Ruflo Plugins (to add)"]
        RT["ruflo-cost-tracker\nLLM budget tracking + alerts"]
        RI["ruflo-intelligence\nSelf-learning query routing"]
        RR["ruflo-rag-memory\nGraph RAG over Iceberg data"]
        RF["ruflo-federation\nMac to VPS secure comms"]
        RO["ruflo-observability\nStructured trace extension"]
    end

    subgraph current["Current Agent Layer"]
        DA["deepagents\n(LangGraph)"]
        MEM["mem0\nFlat memory"]
        LF["Langfuse\nLLM traces"]
        LI["LiteLLM\nGateway"]
    end

    subgraph data["Iceberg Data Layer"]
        GOLD["Gold — ai_inference_cost"]
        SILVER["Silver — mlperf_efficiency\ncloud_gpu_pricing"]
    end

    RT -->|wraps| LI
    RR -->|augments| MEM
    RI -->|improves routing in| DA
    RO -->|extends| LF
    RF -->|federates| DA

    DA --> LI
    DA --> MEM
    DA --> GOLD
    DA --> SILVER

    style ruflo fill:#f5f0ff,stroke:#7b5cfe
    style current fill:#e8f4f8,stroke:#4a90d9
    style data fill:#ffd700,color:#000,stroke:#b8860b
```

## Quickest Wins

### 1. ruflo-cost-tracker (do first)

Wraps LiteLLM — intercepts every LLM call, tracks tokens + cost, alerts when over budget. Directly relevant: the platform studies AI inference cost, should track its own.

```bash
/plugin install ruflo-cost-tracker@ruflo
```

### 2. ruflo-rag-memory

Replaces flat mem0 with Graph RAG. Agents traverse entity relationships (GPU model → benchmark round → pricing → carbon) rather than doing flat vector search.

```bash
/plugin install ruflo-rag-memory@ruflo
```

### 3. ruflo-intelligence

Agents learn from past successful queries automatically via hooks. No code change after install.

```bash
/plugin install ruflo-intelligence@ruflo
```

## Full CLI Install (Path B — production)

For the full loop — MCP server, hooks, all 98 agents:

```bash
cd /Users/jrodeiro/dev/master_ucm/SoloDShouse
npx ruflo init
```

> ⚠️ **CLAUDE.md merge warning**: Review the merge carefully before accepting. SoloDShouse has custom GateGuard + worktree rules that must survive the merge. Backup first: `cp CLAUDE.md CLAUDE.md.backup`

## Next Steps

1. Install `ruflo-cost-tracker` + `ruflo-rag-memory` + `ruflo-intelligence` via Plugin path
2. Monitor cost tracking output for 1 week — baseline LLM spend
3. Decide: stay on Plugin path or do full `npx ruflo init`
4. If full init: document as SDS-XXX ADR
