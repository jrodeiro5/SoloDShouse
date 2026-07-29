---
title: Add New Source
summary: "How to add a new data source to SoloDShouse: create a collector file, define a YAML schema, and optionally configure a connection entry."
topics: [guides, ingestion, configuration]
---

# Add New Source

This guide explains how to add a new data source to SoloDShouse. The process
involves creating a collector file, defining a YAML schema, and optionally
configuring a connection entry for dynamic collection.

The process follows the collector pattern (SDS-043) and connections layer
(SDS-044), enabling domain-agnostic data ingestion with zero orchestration
changes.

## Prerequisites

Before starting, ensure you have:

- A data source you want to ingest (API, database, file, etc.)
- Understanding of the source's data format and access method
- Access to modify `ingestion/collectors/` and `config/schemas/`

## Step 1: Define the Schema

Create a YAML schema file in `config/schemas/{source_name}.yaml`:

```yaml
source: my_source
connection_type: rest
columns:
  - name: timestamp
    type: timestamptz
  - name: value
    type: double
  - name: category
    type: string
partition:
  field: _ingestion_timestamp
  transform: day
```

The schema defines:
- **source**: Source identifier (matches the collector name)
- **connection_type**: Connection type (postgres, s3, rest, filesystem)
- **columns**: List of column definitions with names and Iceberg types
- **partition**: Optional partition configuration (field + transform)

Supported Iceberg types: `string`, `double`, `date`, `timestamptz`, `long`,
`int`, `boolean`, `float`, `timestamp`, `decimal(38,18)`.

### Auto-Discovery (Optional)

For connected sources, use `SchemaDiscovery` to auto-infer the schema:

```python
from connections.discovery import SchemaDiscovery
from connections.manager import ConnectionManager

discovery = SchemaDiscovery()
connection = ConnectionManager().get_connection("my_source")
schema = discovery.discover("my_source", connection)
```

This probes the source using dlt and writes the schema to
`config/schemas/my_source.yaml`.

## Step 2: Create the Collector

Create a new file in `ingestion/collectors/` (e.g., `my_source_collector.py`):

```python
"""Collector for my_source (SDS-043)."""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Any

import pandas as pd
import structlog

from ingestion.collectors.base import BaseCollector
from ingestion.collectors.registry import register_collector

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

logger = structlog.get_logger()


@register_collector("my_source")
class MySourceCollector(BaseCollector):
    """Collector for my_source data."""

    def _fetch_data(self, *args: Any, **kwargs: Any) -> Any:
        """Fetch raw data from my_source API."""
        # Implement source-specific data fetching
        # Return DataFrame, list[dict], or other source-specific format
        import requests
        resp = requests.get("https://api.example.com/data", timeout=30)
        resp.raise_for_status()
        return resp.json()

    def _validate_records(self, raw_data: Any, *args: Any, **kwargs: Any) -> tuple[list[dict], list[dict]]:
        """Validate and normalize raw records."""
        # Convert raw_data to list of dicts
        records = raw_data if isinstance(raw_data, list) else [raw_data]

        valid: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []

        for record in records:
            try:
                # Validate against schema (optional)
                valid.append(record)
            except Exception as exc:
                rejected.append({
                    "rejection_reason": str(exc),
                    "payload": str(record)[:500]
                })

        return valid, rejected

    def collect(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Orchestrate the full ingestion."""
        raw = self._fetch_data(*args, **kwargs)
        valid, rejected = self._validate_records(raw, *args, **kwargs)

        if valid:
            df = pd.DataFrame(valid)
            df["_ingestion_timestamp"] = pd.Timestamp.now(tz="UTC")
            df["_source"] = "my_source"
            self.bronze_writer.write(df, "my_source")

        if rejected:
            self.bronze_writer.write_rejected(rejected, "my_source")

        return {"valid": len(valid), "rejected": len(rejected)}
```

Key requirements:
- Decorate with `@register_collector("my_source")` to register the collector
- Implement `_fetch_data()` to fetch raw data
- Implement `_validate_records()` to split valid/rejected records
- Implement `collect()` to orchestrate the full pipeline

## Step 3: Register the Collector

Import the collector module in `ingestion/collectors/__init__.py`:

```python
from ingestion.collectors.my_source_collector import MySourceCollector  # noqa: F401
```

This triggers the `@register_collector` decorator at import time, making the
collector available to the registry.

## Step 4: (Optional) Configure Connection

For dynamic collection, add an entry to `config/connections.yaml`:

```yaml
connections:
  - name: my_source
    type: rest
    roles:
      - reader
    base_url: https://api.example.com
    endpoint: /data
```

This automatically registers a `DynamicCollector` for `my_source` at import
time, enabling connection-backed ingestion without manual collector files.

## Step 5: Verify

Run the pipeline to verify the new source:

```bash
make pipeline DAGSTER_JOB=my_source_bronze
```

Or trigger manually via Dagster UI (http://localhost:3000).

Check logs for:
- `bronze_written`: Source, row count, Iceberg path
- `bronze_rejected_written`: Source, rejection count (if any)

## Error Handling

Common issues and solutions:

- **Collector not found**: Ensure `@register_collector("my_source")` matches
  the source name in the schema file
- **Schema not found**: Ensure `config/schemas/my_source.yaml` exists
- **Fetch errors**: Check network connectivity and API credentials
- **Validation failures**: Check schema column names and types match source data

## See Also

- [Collector Pattern](../concepts/collector-pattern.md) — plugin system
- [Dynamic Collector](../concepts/dynamic-collector.md) — connection-backed collectors
- [Schema Discovery](../concepts/schema-discovery.md) — dlt-powered schema inference
- [Medallion Architecture](../concepts/medallion-architecture.md) — Bronze→Silver→Gold
- [Ingestion Pipeline](../architecture/ingestion-pipeline.md) — full data flow
- [Dagster Orchestration](../architecture/dagster-orchestration.md) — pipeline orchestration
