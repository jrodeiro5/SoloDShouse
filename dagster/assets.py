"""Dagster software-defined assets — generic factory (SDS-043).

All asset functions are generated at module-import time from the collector
registry.  Adding a new data source = 1 collector file + 1 YAML schema.
No manual Dagster edits needed.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd
import structlog
from resources import IcebergCatalogResource

from dagster import (
    AssetKey,
    RetryPolicy,
    RunRequest,
    SkipReason,
    asset,
    sensor,
)
from ingestion import iceberg_io
from ingestion.collectors.registry import get_collector, list_sources

logger = structlog.get_logger()

def _emit_metric(step: str, started_at: float) -> None:
    duration_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info("pipeline_metric", metric="pipeline.step.duration_ms", step=step, value=duration_ms)


# ── Generic Bronze asset factory ─────────────────────────────────────────────


def _make_bronze_asset(source_name: str):
    collector_cls = get_collector(source_name)
    asset_name = f"{source_name}_bronze"

    @asset(
        name=asset_name,
        group_name="bronze",
        retry_policy=RetryPolicy(max_retries=3, delay=10),
        description=f"Ingest {source_name} -> Bronze.",
    )
    def _impl(
        context,
        iceberg_catalog: IcebergCatalogResource,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        result = collector_cls(iceberg_catalog.get_catalog()).collect()
        context.add_output_metadata(
            {"valid": result.get("valid", 0), "rejected": result.get("rejected", 0)}
        )
        _emit_metric(f"{source_name}_bronze", started)
        return result

    return _impl


def make_bronze_assets() -> list:
    return [_make_bronze_asset(name) for name in list_sources()]


# ── Generic Freshness Sensor ─────────────────────────────────────────────────


def _make_freshness_sensor():
    @sensor(job_name="full_pipeline_job", minimum_interval_seconds=3600 * 24)
    def bronze_freshness_sensor(
        iceberg_catalog: IcebergCatalogResource,
    ):
        from pyiceberg.exceptions import NoSuchTableError

        catalog = iceberg_catalog.get_catalog()
        stale_sources: list[str] = []

        for source_name in list_sources():
            latest: date | None = None
            try:
                df = iceberg_io.scan_table(catalog, "bronze", source_name)
                if not df.empty and "_ingestion_timestamp" in df.columns:
                    latest = pd.to_datetime(df["_ingestion_timestamp"], utc=True).max().date()
            except NoSuchTableError:
                pass

            if latest is None:
                stale_sources.append(source_name)
                continue

            lag_days = (datetime.now(timezone.utc).date() - latest).days
            if lag_days >= 30:
                stale_sources.append(source_name)

        if stale_sources:
            return RunRequest(
                run_key=f"freshness-{datetime.now(timezone.utc).date().isoformat()}",
                asset_selection=[AssetKey(f"{s}_bronze") for s in stale_sources],
            )
        return SkipReason("All bronze sources have fresh data")

    return bronze_freshness_sensor


# ── Module-level generation ──────────────────────────────────────────────────

_bronze_assets = make_bronze_assets()
_bronze_freshness_sensor = _make_freshness_sensor()

bronze_assets = _bronze_assets
all_assets = [*_bronze_assets]
