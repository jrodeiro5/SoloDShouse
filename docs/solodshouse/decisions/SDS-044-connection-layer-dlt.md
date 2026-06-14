# SDS-044: Connection & Schema Discovery Layer (dlt)

**Status**: Accepted  
**Date**: 2026-06-14  
**Supersedes**: None  
**Depends on**: SDS-043 (domain-agnostic collector registry)

## Context

SoloDShouse is now a domain-agnostic platform (SDS-043). All bundled collectors, schemas, and transforms are removed. The platform ships empty.

Users must connect their own data sources. Need:
1. **Connection manager** — S3 buckets, Postgres instances, REST APIs
2. **Schema discovery** — Auto-infer column types from any source
3. **Credential vault** — Encrypt API keys, connection strings
4. **Connector plugins** — Pluggable per source type

Evaluated: OpenMetadata (rejected SDS-014, 2GB+), Cube (overlaps dbt MetricFlow), Supabase (12 containers, Postgres-only), InsForge (competing platform), iii-hq (wrong layer), Nango (overkill), Infisical (future upgrade).

## Decision

Use **dlt (data load tool)** as the connection and schema discovery engine. Two-tier credential approach.

### 1. dlt — Connection + Schema Inference Engine

- **Package**: `dlt` (Python, Apache 2.0)
- **Weight**: 0 MB runtime RAM (in-process library, no daemon)
- **Schema inference**: Auto-detects column types from any source. Tracks schema evolution.
- **Built-in connectors**: S3, Postgres, REST APIs, files, 30+ sources
- **Destinations**: DuckDB, Iceberg, filesystem — all already in SoloDShouse stack

**Pattern**:
```python
import dlt

pipeline = dlt.pipeline(
    pipeline_name="user_source",
    destination="duckdb",
    dataset_name="bronze",
)

# dlt auto-infers schema from source
pipeline.run(source_data, table_name="my_table")
```

### 2. Credential Vault — Two-Tier

| Tier | Tool | When |
|------|------|------|
| **Now** | Python `cryptography` (Fernet) | Encrypted YAML config, single-user, 0 deps |
| **Later** | Infisical (27k ⭐) | Multi-user, team-scoped secrets, audit trails |

Encryption key injected via env var `SOLODSHOUSE_VAULT_KEY`.

### 3. Connection Registry

```yaml
# config/connections.yaml (encrypted at rest)
connections:
  - name: prod_postgres
    type: postgres
    host: ${PG_HOST}
    database: analytics
    schema: public
    
  - name: data_lake
    type: s3
    endpoint: ${S3_ENDPOINT}
    bucket: raw-data
    
  - name: salesforce_api
    type: rest
    base_url: https://api.salesforce.com
    auth: oauth2
```

### 4. Integration with SDS-043 Registry

User flow:
1. Add connection to `config/connections.yaml`
2. dlt auto-discovers schema from source
3. Schema registered in `config/schemas/{source}.yaml`
4. Dagster generic assets (SDS-043) pick it up automatically

Zero manual schema writing. Zero Dagster edits.

## Consequences

**Positive:**
- dlt is 0-infra. No containers, no daemons, no RAM overhead.
- 30+ built-in connectors cover S3, Postgres, REST, files.
- Schema inference eliminates manual Pydantic/Iceberg schema writing.
- Credential vault starts simple, upgradable later.
- Fully aligned with SDS-043 auto-discovery.

**Negative:**
- dlt schema inference may need tuning for edge cases (complex nested JSON).
- Mitigated: dlt allows manual schema overrides via YAML.

## Rejected Alternatives

| Tool | Reason |
|------|--------|
| OpenMetadata | 2GB+, eliminated SDS-014 |
| Supabase | 12 containers, 4GB RAM, Postgres-only |
| Cube | Overlaps dbt MetricFlow |
| Nango | OAuth hub, overkill for connection layer |
| InsForge | Competing platform, not a library |
| iii-hq | Wrong layer (service composition, not data connections) |
