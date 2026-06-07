# SDS-040: Dataset Strategy — AI Energy & Carbon Cost

**Status:** Accepted  
**Date:** 2026-06-07  
**Deciders:** jrodeiro  
**Supersedes:** —  
**Related:** SDS-038 (LLM gateway), SDS-039 (Presidio), SDS-037 (VPS gateway)

---

## Context

SoloDShouse is a platform TFM, not a dataset TFM. The dataset exists to demonstrate the platform in action — Bronze ingestion, Silver cleaning, Gold feature engineering, ML forecasting, anomaly detection, and AI agent queries. The dataset must satisfy three constraints:

1. **Not recognizable** — teachers must not find published Kaggle notebooks or student solutions using the same data
2. **Novel angle** — the combination of sources and the research question should be original
3. **Academically defensible** — citable public sources, reproducible collection methodology

The initial domain (ENTSO-E European energy grid) was deprioritized after confirming that the famous nicholasjhana Kaggle dataset (Spain 2015-2018) covers the same source. While alternative country+period combinations are technically safe, the domain itself is overexposed in academic ML literature (BDI forecasting alone has 15+ peer-reviewed papers with XGBoost/LSTM).

---

## Research Question

**What does running AI cost — in watts, in carbon, in euros — and when is the cheapest and greenest moment to run an inference workload?**

This question is:
- Unanswered as a packaged ML dataset on Kaggle or GitHub (verified June 2026)
- Highly current: EU AI Act (2025), IEA datacenter electricity report (2026), AI sustainability discourse
- Technically original: requires joining sources nobody has joined for a student project
- Intrinsically connected to SoloDShouse itself — the platform *is* an AI workload

---

## Decision

Build a novel dataset from three public API sources, joined on `(country, hour)`:

### Source 1 — Electricity Maps (carbon intensity)
- **URL:** `https://api.electricitymap.org/v3/carbon-intensity/history`
- **Data:** hourly gCO₂eq/kWh per country, based on live grid mix
- **Countries:** DE, FR, ES, PT, PL (different grid carbon profiles)
- **Period:** 2022-01-01 to present
- **Free tier:** 1 year historical per country, no credit card
- **Key signal:** France (nuclear, ~50 gCO₂/kWh) vs Poland (coal, ~700 gCO₂/kWh)

### Source 2 — MLCommons MLPerf Inference benchmarks
- **URL:** `https://mlcommons.org/benchmarks/inference-datacenter/`
- **Data:** tokens/second and joules/token per GPU model per benchmark suite
- **Models covered:** Llama 2/3, Mistral, GPT-J, ResNet, BERT
- **Format:** public CSV releases per round (Round 4.1 = latest as of June 2026)
- **Derived feature:** `watts_per_token = (TDP_watts / tokens_per_second)`

### Source 3 — Cloud provider pricing (spot/on-demand GPU)
- **AWS:** `https://aws.amazon.com/ec2/pricing/on-demand/` (scraped, stable format)
- **Azure:** Azure Retail Prices API (`https://prices.azure.com/api/retail/prices`)
- **Data:** $/hour per GPU instance type (A100, H100, L40S)
- **Derived feature:** `cost_per_million_tokens = ($/hour / tokens_per_hour) × 1e6`

### Joined Gold feature: `ai_inference_cost`

```
(country, hour, model, gpu_instance)
→ gco2_per_million_tokens   = carbon_intensity × wh_per_million_tokens / 1000
→ eur_per_million_tokens    = spot_price_usd × fx_eurusd / tokens_per_hour × 1e6
→ greenest_hour_flag        = carbon_intensity < country_daily_p25
→ cheapest_hour_flag        = spot_price < instance_daily_p25
```

---

## ML Tasks (UCM module coverage)

| UCM Module | Task | Dataset feature |
|:----------:|------|----------------|
| 8 | Forecast carbon intensity 24h ahead (XGBoost + LightGBM) | `carbon_intensity` time series |
| 10 | LSTM multi-step forecast of inference cost | `eur_per_million_tokens` |
| 7 | Anomaly detection on carbon spikes (grid events, outages) | `gco2_per_million_tokens` |
| 6 | Hypothesis test: is France inference significantly greener than Germany? | country comparison |
| 9 | Evidence.dev dashboard: real-time "green AI score" by country | Gold table |
| 13 | BentoML API: given (model, country, time), return predicted cost | MLflow → BentoML |

---

## Why Not Alternatives

| Option | Rejected because |
|--------|-----------------|
| ENTSO-E Spain 2015-2018 | Exact match to nicholasjhana Kaggle dataset (4k+ notebooks) |
| Baltic Dry Index | 15+ peer-reviewed ML papers, academically overexposed |
| Red Sea / Freightos FBX | Clean but domain (shipping) disconnected from platform purpose |
| Google sustainability report | Annual aggregate numbers — not ML-usable time series |
| Self-generated (Langfuse traces) | Requires weeks of platform operation before data exists; chicken-and-egg |
| LLM energy Kaggle dataset (nitishkumar2k01) | Synthetic, small, exists on Kaggle |

---

## Novel Contribution Statement

> *"We construct a novel multi-source dataset joining hourly grid carbon intensity (Electricity Maps), GPU inference efficiency benchmarks (MLCommons MLPerf), and cloud spot pricing (AWS/Azure APIs) to quantify the financial and environmental cost of LLM inference across five European countries. No prior student or practitioner dataset covers this combination."*

This is citable as dataset construction methodology — a legitimate academic contribution independent of the ML models applied to it.

---

## Feasibility

| Risk | Assessment |
|------|-----------|
| Electricity Maps free tier limits | 1 year per country = 5 countries × 8760 rows = 43,800 rows. Sufficient. |
| MLPerf data format changes | CSV releases are versioned and archived. Round 3.x still downloadable. |
| Azure Prices API stability | Public, documented, used by cost calculators. Stable. |
| FX rates for EUR/USD conversion | FRED API (free, St. Louis Fed). |

Total dataset size: ~500K rows in Gold after joins. Sufficient for all ML modules.

---

## Collector Architecture (fits existing patterns)

```python
class ElectricityMapsCollector:
    """Replaces ENTSOECollector. Same BronzeWriter interface."""
    def collect(self, country: str, start: date, end: date) -> dict: ...

class MLPerfCollector:
    """One-shot CSV ingest from MLCommons releases."""
    def collect(self, round_id: str) -> dict: ...

class CloudPricingCollector:
    """Scrapes Azure Retail Prices API + AWS pricing JSON."""
    def collect(self, instance_families: list[str]) -> dict: ...
```

No stack changes required. Same Bronze → Silver → Gold → DuckDB → deepagents path.

---

## IberGrid Framing — Retired

The fictional "IberGrid" company name was created when the domain was Iberian energy grid. With this dataset, no fictional company name is needed. The framing is the platform itself: **SoloDShouse demonstrates how a local-first DS/ML platform answers sustainability questions about AI workloads that cloud vendors do not surface for you.**

UCM Module 14 (TFM Context) framing: any AI-adopting team needs to understand the true cost — financial and environmental — of their LLM usage. SoloDShouse is that team's local platform.

---

## Related

- SDS-038: LLM gateway (Groq via LiteLLM) — the platform itself generates inference data
- SDS-039: Presidio — any production extension would process real queries
- `ingestion/collectors/` — collector implementations for all three sources
- `docs/solodshouse/decisions/` — full ADR index
