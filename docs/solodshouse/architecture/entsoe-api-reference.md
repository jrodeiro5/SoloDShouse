# ENTSO-E Transparency Platform — REST API Reference

Source: https://transparencyplatform.zendesk.com/hc/en-us/articles/15692855254548  
Postman collection: https://documenter.getpostman.com/view/7009892/2s93JtP3F6  
Last verified: 2026-06-08

---

## Base URL

```
https://web-api.tp.entsoe.eu/api
```

## Authentication

Two methods (equivalent):

**Query parameter (preferred for simplicity):**
```
GET /api?securityToken=<UUID>&documentType=...
```

**Header:**
```
SECURITY_TOKEN: <UUID>
```

Token format: UUID, e.g. `b44b53ed-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

---

## Request Format

All requests are `GET` with query parameters:

| Parameter | Format | Description |
|-----------|--------|-------------|
| `documentType` | `A##` code | Data item type (see table below) |
| `processType` | `A##` code | Process type (A16=Realised, A33=Year ahead) |
| `in_Domain` | EIC code | Control area / bidding zone (generation source) |
| `out_Domain` | EIC code | Control area / bidding zone (load destination) |
| `outBiddingZone_Domain` | EIC code | Bidding zone for load queries |
| `periodStart` | `yyyyMMddHHmm` UTC | Window start, e.g. `202308152200` |
| `periodEnd` | `yyyyMMddHHmm` UTC | Window end |
| `PsrType` | `B##` code | Optional: filter by production type |

---

## Response Format

XML. Root elements:
- `GL_MarketDocument` — generation and load data
- `Publication_MarketDocument` — market data (congestion, allocation)

Key structure:
```xml
<GL_MarketDocument>
  <TimeSeries>
    <MktPSRType>
      <psrType>B16</psrType>         <!-- production type -->
    </MktPSRType>
    <inBiddingZone_Domain.mRID>10YES-REE------0</inBiddingZone_Domain.mRID>
    <Period>
      <timeInterval>
        <start>2023-08-15T22:00Z</start>
        <end>2023-08-16T22:00Z</end>
      </timeInterval>
      <resolution>PT60M</resolution>  <!-- PT15M or PT60M -->
      <Point>
        <position>1</position>
        <quantity>4217</quantity>     <!-- MW -->
      </Point>
    </Period>
  </TimeSeries>
</GL_MarketDocument>
```

**Note:** `inBiddingZone_Domain` = generation; `outBiddingZone_Domain` = consumption within same TimeSeries.

Max 100 TimeSeries per response.

---

## Key Endpoints

### 16.1.B — Actual Generation per Production Type

```
GET /api?documentType=A75&processType=A16&in_Domain=<EIC>&periodStart=<ts>&periodEnd=<ts>
```

- **Request window limit:** 1 day max
- `PsrType` optional — omit to get all production types
- Primary endpoint for SoloDShouse energy mix data

Example (Spain, one day):
```bash
curl "https://web-api.tp.entsoe.eu/api?securityToken=<TOKEN>&documentType=A75&processType=A16&in_Domain=10YES-REE------0&periodStart=202308152200&periodEnd=202308162200"
```

---

### 6.1.A — Actual Total Load

```
GET /api?documentType=A65&processType=A16&outBiddingZone_Domain=<EIC>&periodStart=<ts>&periodEnd=<ts>
```

- **Request window limit:** 1 year max

---

### 14.1.A — Installed Capacity per Production Type

```
GET /api?documentType=A68&processType=A33&in_Domain=<EIC>&periodStart=<ts>&periodEnd=<ts>
```

- **Request window limit:** 1 year max

---

## Production Type Codes (PsrType)

| Code | Type |
|------|------|
| B01 | Biomass |
| B02 | Fossil Brown coal/Lignite |
| B04 | Fossil Gas |
| B05 | Fossil Hard coal |
| B06 | Fossil Oil |
| B09 | Geothermal |
| B10 | Hydro Pumped Storage |
| B11 | Hydro Run-of-river |
| B12 | Hydro Water Reservoir |
| B14 | Nuclear |
| B15 | Other renewable |
| B16 | Solar |
| B17 | Waste |
| B18 | Wind Offshore |
| B19 | Wind Onshore |
| B20 | Other |
| B25 | Energy storage |

---

## EIC Codes — Iberian Peninsula (SoloDShouse domain)

| Country | Bidding Zone EIC |
|---------|-----------------|
| Spain | `10YES-REE------0` |
| Portugal | `10YPT-REN------W` |
| France | `10YFR-RTE------C` |
| Morocco (interconnect) | `10YMA-ONED----0` |

---

## Rate Limits & Constraints

- Max 100 TimeSeries per XML response
- Generation endpoints (A75): max **1 day** per request — loop day-by-day for backfill
- Load / capacity endpoints: max **1 year** per request
- No explicit rate limit published; use 1 req/s as safe default

---

## Error Handling

HTTP 400 with XML body on bad parameters. Common errors:
- `URI_FORMAT_ERROR` — malformed URL or parameters
- `No matching data found` — valid request, no data for period/area

---

## Usage in SoloDShouse

`ENTSOECollector` uses endpoint 16.1.B (A75/A16) to ingest hourly generation mix for Spain and Portugal into `bronze.entso_generation`. This feeds the carbon intensity proxy in Silver and the `ai_inference_gold` feature table.

- Schema: `BRONZE_ENTSO_GENERATION_SCHEMA` in `ingestion/iceberg_schemas.py`
- Collector: `ingestion/collectors/entsoe_collector.py`
- Dagster asset: `entsoe_generation_bronze` in `dagster/assets.py`
