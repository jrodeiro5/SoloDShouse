# SDS-043: Domain-Agnostic Platform Pivot

**Status**: Accepted  
**Date**: 2026-06-14  
**Supersedes**: SDS-030, SDS-040 (domain decisions, not architecture)

## Context

SoloDShouse was designed as an ENTSO-E energy + AI inference cost analytics platform. After extracting UCM course materials and evaluating the architecture, the project is pivoting to a **domain-agnostic Databricks-like platform** — a plug-and-play data science and AI system that works with any data source, not just energy.

The core infrastructure (Iceberg I/O, SeaweedFS, Trino, DuckDB, Docker profiles) is already fully agnostic. The problem is in the **registration layer**: collectors, schemas, and Dagster assets are hardcoded per source.

## Decision

Restructure the ingestion and orchestration layers into a **generic, config-driven pipeline** with three pillars:

### 1. Collector Registry (Decorator Pattern)

```
@register_collector("mlperf_benchmarks")
class MLPerfCollector(BaseCollector): ...
```

- `ingestion/collectors/base.py` — Abstract `BaseCollector` with `collect()`, `_fetch_data()`, `_validate_records()`
- `ingestion/collectors/registry.py` — Decorator `@register_collector(name)` + `list_sources()` + `get_collector(name)`
- Each collector self-registers at import time. Adding a source = adding a file.

### 2. Config-Driven Schemas

Schemas defined in YAML under `config/schemas/{source_name}.yaml`:

```yaml
source: mlperf_benchmarks
bronze_table: mlperf_benchmarks
namespace: bronze
columns:
  - name: round_id
    type: string
  - name: tokens_per_sec
    type: double
partition:
  field: _ingestion_timestamp
  transform: day
```

- `ingestion/iceberg_schemas.py` gains `schema_from_config(dict) -> Schema`
- Existing hardcoded schemas remain as migration path, marked deprecated.
- New sources define schema in YAML only — no code changes needed.

### 3. Generic Dagster Asset Factory

```python
def make_bronze_assets():
    return [_bronze_asset(source) for source in registry.list_sources()]

def _bronze_asset(source_name: str):
    @asset(name=source_name, group_name="bronze", ...)
    def _impl(context, iceberg_catalog):
        collector_cls = registry.get_collector(source_name)
        return collector_cls(iceberg_catalog.get_catalog()).collect()
    return _impl
```

- `dagster/assets.py` rewritten as factory — zero per-source functions
- `dagster/definitions.py` auto-discovers from registry
- Sensors and asset checks become generic (e.g., freshness check on any bronze table)

### 4. Cleanup

| Action | File | Reason |
|--------|------|--------|
| Delete | `ml/evaluate.py` | Dead legacy financial domain code |
| Delete | `ingestion/schema/entsoe_records.py` | Scaffold, unused, domain-specific |
| Remove | `entsoe-py` from pyproject.toml | No longer needed |
| Rename | `runtime_identity.py` default domain | `"energy_ai_cost"` → `"default"` |
| KEEP | All existing iceberg schemas | They ARE the current sources, just registry-backed now |

## Consequences

**Positive:**
- Adding a new data source = 1 collector file + 1 YAML config. No Dagster edits.
- Schemas live in version-controlled YAML, not buried in Python.
- Registry enables auto-documentation: `list_sources()` → generate docs.
- Same platform can handle ENTSO-E, finance, weather, or any tabular data.

**Negative:**
- Schema validation moves from compile-time (Pydantic) to runtime. Mitigated by YAML schema validation and Iceberg's type enforcement.
- Existing hardcoded schemas need migration code for backward compat. Low risk — only 2 active sources.

## Rejected Alternatives

- **Plugin system with setuptools entry points**: Overengineered for local-first platform. Simple decorator pattern suffices.
- **Full dynamic inference (pyiceberg schema from pandas)**: Loses explicit schema control. YAML gives visibility with less ceremony than Python.
- **Keep hardcoded registration**: Locks platform to known sources. Violates plug-and-play goal.
