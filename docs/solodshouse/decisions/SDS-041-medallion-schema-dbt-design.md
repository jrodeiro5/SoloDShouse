# SDS-041: Medallion Schema Design and dbt Project Structure

**Status:** Draft — pending data validation  
**Date:** 2026-06-07  
**Deciders:** jrodeiro  
**Supersedes:** task.md Phase 1.4 (informal notes)  
**Related:** SDS-040 (dataset strategy), SDS-016 (dbt-duckdb), SDS-002 (DuckDB complements Trino)

---

## Context

SDS-040 defined the research question and three data sources (ENTSO-E generation mix, MLCommons MLPerf benchmarks, Azure/AWS cloud pricing). This ADR defines the physical schema for each medallion layer and the dbt project structure that transforms Silver into Gold.

**Critical caveat:** ENTSO-E API key not yet received (email sent 2026-06-07, expected ~2026-06-12). MLPerf CSV format and Azure Retail Prices API response structure have not been ingested into a live environment. All schemas in this ADR are **design-time estimates** based on:

- ENTSO-E Transparency Platform API documentation
- MLCommons MLPerf public CSV releases (Round 5.1, June 2026)
- Azure Retail Prices REST API documentation (`https://prices.azure.com/api/retail/prices`)
- FRED API documentation for EUR/USD series

**This ADR must be revised after first successful ingestion run.** Column names, data types, and cardinalities may change. The dbt models must not be written until at least one Bronze table has been populated and `dbt show` has been run against real data.

---

## Decision

### Layer responsibility

| Layer | Tool | Responsibility |
|-------|------|----------------|
| Bronze | pyiceberg (append) | Raw ingest, immutable, day-partitioned |
| Silver | pyiceberg (overwrite) | Typed, cleaned, deduped, derived fields |
| Gold | dbt-duckdb (overwrite) | ML-ready joins, flags, semantic layer |

dbt does **Silver → Gold only**. Python collectors + pyiceberg own Bronze → Silver. DuckDB reads Silver Iceberg tables via pyiceberg scan and exposes them as DuckDB relations that dbt sources reference.

---

## Proposed Bronze Schemas (subject to change)

All Bronze tables: append-only, partitioned on `_ingestion_timestamp` via `DayTransform()`.

### `bronze.entsoe_generation`

Hourly electricity generation by country and fuel type. One row per (timestamp, country, fuel_type) per API call.

| Field | Type | Notes |
|-------|------|-------|
| `timestamp_utc` | TimestamptzType | Start of hour |
| `country` | StringType | ISO 2-letter (DE, FR, ES, PT, PL) |
| `fuel_type` | StringType | ENTSO-E psr_type code (e.g. B01=Biomass) |
| `generation_mw` | DoubleType | Actual generation in MW |
| `_ingestion_timestamp` | TimestamptzType | Partition key |
| `_source` | StringType | "entsoe-py" |

**Unknowns:** ENTSO-E uses `psr_type` codes (B01–B20). Must map codes to fuel names at Silver. Null generation values are common (fuel absent in grid mix) — Bronze stores nulls as-is.

### `bronze.mlperf_benchmarks`

One row per (model, accelerator, submitter) per MLPerf round. Ingested from public CSV.

| Field | Type | Notes |
|-------|------|-------|
| `round_id` | StringType | e.g. "v5.1" |
| `model_name` | StringType | e.g. "llama-3-70b" |
| `accelerator` | StringType | e.g. "H100-SXM-80GB" |
| `submitter` | StringType | Organisation name |
| `scenario` | StringType | "Offline" / "Server" |
| `tokens_per_sec` | DoubleType | Performance result |
| `tdp_watts` | DoubleType | From accelerator spec sheet (joined at Silver) |
| `_ingestion_timestamp` | TimestamptzType | Partition key |
| `_source` | StringType | "mlcommons-csv" |

**Unknowns:** TDP values are NOT in the MLPerf CSV — they require a separate GPU spec lookup (manual or scraped). This join is the most fragile part of the pipeline. `tdp_watts` may not exist at Bronze; it may need to be a Silver-only derived field from a static lookup table. Decision deferred until CSV is inspected.

### `bronze.cloud_gpu_pricing`

One row per (provider, instance_type, region) per collection run.

| Field | Type | Notes |
|-------|------|-------|
| `provider` | StringType | "azure" or "aws" |
| `instance_type` | StringType | e.g. "Standard_NC96ads_A100_v4" |
| `region` | StringType | e.g. "westeurope" |
| `price_usd_per_hour` | DoubleType | On-demand list price |
| `sku_name` | StringType | Raw SKU identifier |
| `captured_at` | TimestamptzType | When price was queried |
| `_ingestion_timestamp` | TimestamptzType | Partition key |
| `_source` | StringType | "azure-retail-api" / "aws-pricing-api" |

**Unknowns:** Azure Retail Prices API returns many SKU variants per instance (spot, reserved, dev/test). Filtering logic for "on-demand GPU" rows is unknown until API is called live. AWS pricing uses a different JSON structure. Both collectors may need separate Bronze tables if schemas diverge significantly.

### `bronze.fx_rates`

Daily EUR/USD exchange rate from FRED (series DEXUSEU).

| Field | Type | Notes |
|-------|------|-------|
| `observation_date` | DateType | |
| `eur_usd` | DoubleType | USD per 1 EUR |
| `_ingestion_timestamp` | TimestamptzType | Partition key |
| `_source` | StringType | "fred-api" |

**Unknowns:** None significant. FRED DEXUSEU is a well-known stable series. Only risk: weekends/holidays have null values — Silver must forward-fill.

---

## Proposed Silver Schemas (subject to change)

All Silver tables: full overwrite per pipeline run, no partition.

### `silver.grid_carbon_intensity`

Derived from Bronze ENTSO-E generation mix × emission factors. One row per (timestamp_hour, country).

| Field | Type | Notes |
|-------|------|-------|
| `timestamp_hour` | TimestamptzType | Truncated to hour |
| `country` | StringType | |
| `carbon_intensity_gco2_kwh` | DoubleType | gCO₂eq/kWh |
| `generation_mix_json` | StringType | Fuel breakdown as JSON (optional, for audit) |

**Unknowns:** Emission factor table (gCO₂/MWh per fuel type) must be sourced. Standard reference: IPCC AR6 lifecycle emission factors. These are static constants — stored as a Python dict in `transformations/emission_factors.py`, not in Iceberg. If ENTSO-E changes psr_type codes between years (it has historically), mapping breaks silently.

### `silver.mlperf_efficiency`

One row per (round_id, model_name, accelerator). Adds `wh_per_million_tokens`.

| Field | Type | Notes |
|-------|------|-------|
| `round_id` | StringType | |
| `model_name` | StringType | Normalised name |
| `accelerator` | StringType | Normalised name |
| `tokens_per_sec` | DoubleType | Best result for scenario=Offline |
| `tdp_watts` | DoubleType | From lookup table (if Bronze lacks it) |
| `wh_per_million_tokens` | DoubleType | `(tdp_watts / tokens_per_sec) / 3600 * 1e6` |

**Unknowns:** Multiple submitters report the same (model, accelerator) with different scores. Silver takes `MAX(tokens_per_sec)` per (model, accelerator, round) — best-case efficiency. This is a deliberate bias; document in dbt model description.

### `silver.cloud_gpu_pricing`

One row per (provider, instance_type, region, valid_from). EUR converted.

| Field | Type | Notes |
|-------|------|-------|
| `provider` | StringType | |
| `instance_type` | StringType | |
| `region` | StringType | |
| `price_eur_per_hour` | DoubleType | `price_usd * eur_usd` from fx_rates |
| `accelerator` | StringType | Mapped from instance_type (lookup table) |
| `valid_from` | DateType | Date of capture |

**Unknowns:** Instance type → GPU model mapping (e.g. `Standard_NC96ads_A100_v4` → `A100`) requires a static lookup table. This table must be created manually the first time; no API provides it directly.

---

## Proposed dbt Project Structure

```
transformations/dbt/
  dbt_project.yml
  profiles.yml            # DuckDB profile, reads from pyiceberg-exported parquet
  packages.yml            # dbt-utils >= 1.3
  models/
    staging/
      sources.yml         # Silver tables declared as dbt sources
      stg_grid_carbon.sql
      stg_mlperf.sql
      stg_cloud_pricing.sql
    intermediate/
      int_inference_cost_hourly.sql   # join on (country, hour, model, accelerator)
    marts/
      mart_ai_inference_cost.sql      # Gold, ML-ready
      mart_country_comparison.sql     # country-level aggregates
      mart_efficiency_over_time.sql   # round-over-round MLPerf trend
      mart_ai_inference_cost.yml      # MetricFlow semantic model + metrics
```

**dbt version:** Core 1.12+ (latest MetricFlow spec). `dbt-duckdb` adapter.

### Gold grain

`mart_ai_inference_cost` grain: **(country, timestamp_hour, model_name, accelerator)**. Estimate: 5 countries × 38,000 hours × 5 models × 3 accelerators = ~2.85M rows. Within DuckDB RAM budget on Mac Studio (64 GB). Estimate may change once row counts from real ENTSO-E data are known (see Q6 below).

### Key derived columns in Gold

```sql
tokens_per_hour         = tokens_per_sec * 3600
eur_per_million_tokens  = (price_eur_per_hour / tokens_per_hour) * 1e6
gco2_per_million_tokens = carbon_intensity_gco2_kwh * wh_per_million_tokens / 1000
greenest_hour_flag      = carbon_intensity_gco2_kwh < PERCENTILE_CONT(0.25)
                          OVER (PARTITION BY country, DATE_TRUNC('day', timestamp_hour))
cheapest_hour_flag      = price_eur_per_hour < PERCENTILE_CONT(0.25)
                          OVER (PARTITION BY provider, instance_type, DATE_TRUNC('day', timestamp_hour))
```

### MetricFlow semantic model (latest spec, dbt Core 1.12+)

```yaml
models:
  - name: mart_ai_inference_cost
    semantic_model:
      agg_time_dimension: timestamp_hour
      entities:
        - name: inference_event
          type: primary
          expr: "country || '|' || CAST(timestamp_hour AS VARCHAR) || '|' || model_name || '|' || accelerator"
        - name: country
          type: foreign
          expr: country
      dimensions:
        - name: timestamp_hour
          type: time
          type_params:
            time_granularity: hour
        - name: country
          type: categorical
        - name: model_name
          type: categorical
        - name: accelerator
          type: categorical
        - name: greenest_hour_flag
          type: categorical
        - name: cheapest_hour_flag
          type: categorical
      measures:
        - name: avg_carbon_per_million_tokens
          agg: average
          expr: gco2_per_million_tokens
        - name: avg_cost_per_million_tokens
          agg: average
          expr: eur_per_million_tokens
        - name: inference_event_count
          agg: count
    metrics:
      - name: mean_inference_cost_eur
        type: simple
        label: "Avg cost per 1M tokens (EUR)"
        type_params:
          measure: avg_cost_per_million_tokens
      - name: mean_inference_carbon_gco2
        type: simple
        label: "Avg CO₂ per 1M tokens (gCO₂)"
        type_params:
          measure: avg_carbon_per_million_tokens
```

---

## Known Open Questions (must resolve before implementation)

| # | Question | Blocks |
|---|----------|--------|
| 1 | Do MLPerf CSVs include TDP or must it be a separate lookup? | `bronze.mlperf_benchmarks`, `silver.mlperf_efficiency` |
| 2 | Azure Retail API: which filter expression isolates on-demand GPU SKUs? | `bronze.cloud_gpu_pricing` collector |
| 3 | Does AWS pricing API require separate Bronze table or can it share schema with Azure? | Phase 1.4 collector scope |
| 4 | What is the exact ENTSO-E psr_type → fuel_name mapping for target countries? | `silver.grid_carbon_intensity` emission factor join |
| 5 | Does `entsoe-py` return null rows for fuel types with zero generation, or omit them? | Bronze schema field cardinality |
| 6 | What is the actual row count per country per year from ENTSO-E? | Gold partitioning strategy |
| 7 | Can DuckDB read pyiceberg-scanned Arrow tables directly as sources, or must we export to parquet first? | `profiles.yml` and `sources.yml` design |

---

## Constraints

- **Bronze is immutable** — never overwrite, always append. Rejected rows go to `bronze.rejected` (fixed schema, JSON payload).
- **Silver is idempotent** — full overwrite on each run. Running twice produces same result.
- **dbt models must not be written until Q7 is answered** — DuckDB ↔ pyiceberg bridge pattern must be validated with a proof-of-concept first.
- **Static lookup tables** (emission factors, GPU TDP, instance→GPU mapping) stored as Python dicts in `transformations/`, not Iceberg. They are small and change rarely.
- **No Trino in dbt execution path** — dbt-duckdb adapter only. Trino remains for ad-hoc cross-source queries.

---

## Consequences

### Positive
- Medallion layers cleanly separated by tool (Python/pyiceberg for raw ingest, dbt/DuckDB for analytics)
- dbt semantic layer enables deepagents natural-language queries over Gold without custom SQL
- Schema designed for UCM ML modules: each module has a clear input column or aggregation in Gold
- Bronze captures raw source values — no decisions baked in until Silver

### Negative
- Two static lookup tables (emission factors, GPU TDP) live outside version-controlled data — must be maintained manually
- Gold size (~2.85M rows) is an estimate; could be 5× larger if all MLPerf rounds (v3.0–v5.1) are included
- DuckDB ↔ pyiceberg integration pattern (Q7) not yet proven in this project

### Risks
- ENTSO-E API key delayed → Bronze ingestion blocked → all schema assumptions unvalidated
- MLPerf TDP lookup is manual → new GPU generation causes silent nulls in `wh_per_million_tokens`
- Azure pricing API SKU naming changes → `silver.cloud_gpu_pricing` accelerator mapping breaks

---

## Implementation Gates

**Phase 1.4a** (rewrite `ingestion/iceberg_schemas.py`): can start once ENTSO-E API key arrives and first raw response is inspected.

**Phase 1.4b** (scaffold `transformations/dbt/`): blocked until:
- At least one Bronze table has real rows
- Q7 (DuckDB ↔ pyiceberg bridge) answered with working proof-of-concept
- This ADR promoted from Draft to Accepted

**Do not assign Phase 1.4b to OpenCode until this ADR is Accepted.**

---

## Related

- `ingestion/iceberg_schemas.py` — pyiceberg Schema objects (Phase 1.4a)
- `transformations/dbt/` — dbt project (Phase 1.4b, blocked)
- `transformations/emission_factors.py` — static IPCC AR6 constants (to be created)
- SDS-040 — dataset strategy and source selection
- SDS-016 — dbt-core + dbt-duckdb decision
- `task.md` Phase 1.4 — implementation checklist
