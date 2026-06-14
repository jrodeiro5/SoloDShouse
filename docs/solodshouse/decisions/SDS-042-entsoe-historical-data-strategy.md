# SDS-042 — ENTSO-E Historical Data Ingestion Strategy

**Status:** Accepted  
**Date:** 2026-06-08  
**Deciders:** jrodeiro  
**Supersedes:** —  
**Related:** SDS-030 (ENTSO-E domain), SDS-040 (dataset strategy), SDS-041 (medallion schema)

---

## Context

ENTSO-E Transparency Platform REST API endpoint 16.1.B (Actual Generation per Production Type, `documentType=A75`) has a hard **1-day maximum request window**. A single API call cannot span more than 24 hours.

For SoloDShouse to have enough historical data for ML training (XGBoost/LSTM forecasting), we need at minimum 2 years of hourly generation data for Spain and Portugal — roughly 17,520 hourly records per country per production type.

This creates a conflict:
- **Daily incremental** (steady state): 1 API call/day/country → trivial
- **Historical backfill** (cold start): 2 years = ~730 API calls per country → non-trivial

The ENTSO-E security token was received 2026-06-08.

---

## Options Evaluated

### Option A — Raw REST API with manual day loop

Loop over each day, fire `GET /api?documentType=A75&...&periodStart=<day>&periodEnd=<day+1>`.

- Pro: no extra dependency, full control
- Con: ~730 calls × ~0.5s = ~6 min per country; retry/error handling must be written from scratch; reinvents what `entsoe-py` already does

### Option B — `entsoe-py` EntsoePandasClient (auto-chunking)

`EntsoePandasClient.query_generation()` accepts arbitrary date spans and internally chunks into 1-day windows automatically. Returns a Pandas DataFrame directly.

```python
from entsoe import EntsoePandasClient
import pandas as pd

client = EntsoePandasClient(api_key=os.environ["ENTSOE_API_KEY"])
df = client.query_generation(
    "ES",
    start=pd.Timestamp("20220101", tz="UTC"),
    end=pd.Timestamp("20240101", tz="UTC"),
)
```

- Pro: zero pagination logic; actively maintained (v0.8.0, Apr 2026); MIT license; handles retries
- Con: 730 API calls still fire — just hidden; ~6 min for 2-year Spain backfill; blocks Dagster if run inline

### Option C — ENTSO-E File Library

New bulk system at `https://fms.tp.entsoe.eu` (replaced old SFTP). Pre-packaged CSVs per month per dataset. `entsoe-py` exposes `EntsoeFileClient`.

```python
from entsoe.files import EntsoeFileClient
client = EntsoeFileClient(username=<portal_user>, pwd=<portal_pwd>)
file_list = client.list_folder("ActualGenerationPerProductionType_16.1.B_C")
df = client.download_multiple_files([...up to 100 ids...])
```

- Pro: bulk download, 1 request = 1 month; no 1-day limit
- Con: requires **portal credentials** (separate from API token); not all datasets confirmed available in File Library; adds credential management complexity

---

## Decision

**Hybrid approach (Option B for both paths):**

| Phase | Tool | Scope | When |
|-------|------|-------|------|
| Cold-start backfill | `scripts/backfill_entsoe.py` using `EntsoePandasClient` | 2022-01-01 → yesterday, ES + PT | Run once manually before first Dagster run |
| Daily incremental | `ENTSOECollector` using `EntsoePandasClient` | Yesterday 00:00→23:59 UTC | Dagster `full_pipeline_job` daily at 07:00 UTC |

Both paths use the same `entsoe-py` library and same API token. The backfill script is a one-off CLI tool, not a Dagster asset, so it does not block pipeline operations.

File Library (Option C) deferred — adds credential complexity for marginal gain given backfill runs only once.

---

## Implementation

**Dependencies to add:**
```
entsoe-py>=0.8.0
```

**New files:**
- `ingestion/collectors/entsoe_collector.py` — `ENTSOECollector` wrapping `EntsoePandasClient.query_generation()`
- `scripts/backfill_entsoe.py` — one-off CLI: `--start`, `--end`, `--countries` args, writes to Bronze Iceberg
- `ingestion/iceberg_schemas.py` — add `BRONZE_ENTSO_GENERATION_SCHEMA`
- `dagster/assets.py` — add `entsoe_generation_bronze` asset

**Bronze schema** (`BRONZE_ENTSO_GENERATION_SCHEMA`):

| Field | Type | Notes |
|-------|------|-------|
| `timestamp_utc` | TimestamptzType | start of interval (hourly) |
| `country` | StringType | ISO-2 code: ES, PT |
| `psr_type` | StringType | B01…B25 production type code |
| `psr_type_name` | StringType | Solar, Wind Onshore, Nuclear… |
| `quantity_mw` | DoubleType | generation in MW |
| `resolution` | StringType | PT60M or PT15M |
| `_ingestion_timestamp` | TimestamptzType | |
| `_source` | StringType | `entsoe_transparency_platform` |

**Countries in scope (SDS-030):** ES (Spain), PT (Portugal). FR optional for interconnect analysis.

**Rate limiting:** `EntsoePandasClient` has built-in retry. Backfill script adds 1s sleep between country iterations to stay below any undocumented rate limit.

---

## Consequences

- `entsoe-py` becomes a project dependency — well-maintained, MIT, low risk
- Backfill is a manual one-time step, not automated — acceptable for TFM timeline
- File Library path stays open; can switch if ENTSO-E publishes 16.1.B data there
- `ENTSOE_API_KEY` must be in `.env` before running either path (received 2026-06-08)
