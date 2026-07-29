---
title: Collector Pattern
summary: The collector plugin system (SDS-043) that makes SoloDShouse domain-agnostic by registering data sources through a decorator-based registry.
topics: [concepts, architecture, ingestion]
---

# Collector Pattern

The collector pattern is SoloDShouse's plugin system for data ingestion. It
makes the platform domain-agnostic: adding a new data source requires only a
collector file and a YAML schema, with zero changes to the orchestration layer
([SDS-043](docs/solodshouse/decisions/SDS-043-domain-agnostic-platform.md)).

The pattern consists of three components: `BaseCollector` (abstract interface),
the registry (decorator-based registration), and `DynamicCollector`
(connection-backed auto-collectors).

## BaseCollector

`BaseCollector` is an abstract base class that defines the interface all
collectors must implement. Each collector receives a PyIceberg `Catalog` in its
constructor and uses it to write data to the Bronze layer
([base.py](ingestion/collectors/base.py)).

```python
class BaseCollector(ABC):
    def __init__(self, catalog: "Catalog"):
        self.catalog = catalog
        self.bronze_writer = BronzeWriter(catalog)

    @abstractmethod
    def collect(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Orchestrate the full ingestion: fetch → validate → write → return summary."""

    @abstractmethod
    def _fetch_data(self, *args: Any, **kwargs: Any) -> Any:
        """Fetch raw data from the upstream source."""

    @abstractmethod
    def _validate_records(self, *args: Any, **kwargs: Any) -> tuple[list[dict], list[dict]]:
        """Validate & normalise raw records."""
```

The `collect()` method orchestrates the full ingestion pipeline: it calls
`_fetch_data()` to pull raw data, `_validate_records()` to split records into
valid and rejected batches, and then delegates to `BronzeWriter` for Iceberg
writes. Subclasses override these methods to implement source-specific logic.

The `_already_ingested()` helper is a no-op by default but can be overridden
when a source provides immutable releases (e.g., MLPerf round IDs) to skip
duplicate ingestion.

## Registry

The registry is a module-level decorator-based plugin system. The
`@register_collector("source_name")` decorator adds a collector class to the
module-level registry, making it available for automatic discovery
([registry.py](ingestion/collectors/registry.py)).

```python
_collectors: dict[str, type["BaseCollector"]] = {}

def register_collector(name: str):
    """Decorator that registers a BaseCollector subclass under *name*."""
    def _decorator(cls: type["BaseCollector"]) -> type["BaseCollector"]:
        _collectors[name] = cls
        return cls
    return _decorator
```

Three public functions expose the registry:

- `list_sources()` returns the sorted list of registered source names.
- `get_collector(name)` returns the registered collector class for a source.
- `register_collector(name)` is the decorator that adds collectors to the
  registry.

Importing `ingestion.collectors` triggers registration of all statically
defined collectors in the package.

## DynamicCollector

`DynamicCollector` bridges the collector pattern (SDS-043) with the connections
layer (SDS-044). It reads `config/connections.yaml` via `ConnectionManager` and
registers one collector per connection entry at import time
([dynamic.py](ingestion/collectors/dynamic.py)).

Each `DynamicCollector` instance fetches data from its configured source using
raw drivers (requests, boto3, psycopg2), validates against its YAML schema, and
writes to Bronze via `BronzeWriter`. The module-level auto-registration
triggers when `ConnectionManager` is available:

```python
if _MGR is not None:
    for _name in _MGR.list_connections():
        _cls = type(f"_Dynamic_{_name}", (DynamicCollector,), {"_source": _name})
        register_collector(_name)(_cls)
```

This means adding a new data connection to `config/connections.yaml`
automatically creates a collector for it—no manual registration required.

## Fetch Helpers

`DynamicCollector` includes fetch helpers for four connection types:

- `_fetch_rest()` — HTTP GET requests with JSON parsing
- `_fetch_s3()` — S3 object listing and reading (Parquet/CSV)
- `_fetch_postgres()` — PostgreSQL queries with LIMIT 1000
- `_fetch_filesystem()` — Local filesystem globbing (Parquet/CSV)

Each helper returns a list of dicts ready for validation and Bronze writes.

## Validation Flow

The `_validate_records()` method loads the source's YAML schema config and
validates records against it. Records that match the schema columns are added
to the valid batch; records that fail validation are added to the rejected
batch with a reason and the original payload as JSON.

## See Also

- [Dynamic Collector](dynamic-collector.md) — connection-backed auto-collector
- [Schema Discovery](schema-discovery.md) — dlt-powered schema inference
- [Medallion Architecture](medallion-architecture.md) — Bronze→Silver→Gold flow
- [Iceberg I/O](iceberg-io.md) — pyiceberg abstraction layer
