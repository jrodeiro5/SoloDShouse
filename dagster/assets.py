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
    AssetCheckResult,
    AssetKey,
    RetryPolicy,
    RunRequest,
    SkipReason,
    asset,
    asset_check,
    sensor,
)
from ingestion import iceberg_io
from ingestion.collectors.registry import get_collector, list_sources

logger = structlog.get_logger()

_SILVER_TRANSFORMS: dict[str, Any] = {}


def _emit_metric(step: str, started_at: float) -> None:
    duration_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info("pipeline_metric", metric="pipeline.step.duration_ms", step=step, value=duration_ms)


def _row_count(result: dict[str, Any]) -> int:
    v = result.get("row_count", 0)
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


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


# ── Generic Silver asset factory ─────────────────────────────────────────────


def _make_silver_asset(source_name: str):
    transform = _SILVER_TRANSFORMS.get(source_name)
    if transform is None:
        return None

    asset_name = f"{source_name}_silver"
    bronze_dep = f"{source_name}_bronze"

    @asset(
        name=asset_name,
        group_name="silver",
        description=f"Transform {source_name} Bronze -> Silver.",
    )
    def _impl(
        context,
        iceberg_catalog: IcebergCatalogResource,
        **kwargs: dict[str, Any],
    ) -> str:
        _ = kwargs.get(bronze_dep)
        started = time.perf_counter()
        result = transform.run(iceberg_catalog.get_catalog())
        context.add_output_metadata(
            {"table": result["table"], "row_count": _row_count(result)}
        )
        _emit_metric(f"{source_name}_silver", started)
        return str(result["table"])

    return _impl


def make_silver_assets() -> list:
    assets: list = []
    for name in list_sources():
        fn = _make_silver_asset(name)
        if fn is not None:
            assets.append(fn)
    return assets


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


# ── Generic Silver Asset Checks ──────────────────────────────────────────────


def make_silver_checks() -> list:
    checks: list = []

    for source_name in _SILVER_TRANSFORMS:
        silver_asset_name = f"{source_name}_silver"

        def _make_check(src: str, asset_n: str):
            @asset_check(
                asset=asset_n,
                description=f"{src} Silver has at least 1 row",
            )
            def _check(
                iceberg_catalog: IcebergCatalogResource,
                **kwargs: Any,
            ) -> AssetCheckResult:
                _ = kwargs
                df = iceberg_io.scan_table(iceberg_catalog.get_catalog(), "silver", src)
                row_count = len(df)
                passed = row_count >= 1
                return AssetCheckResult(
                    passed=passed,
                    description=f"{src} Silver has {row_count} rows",
                    metadata={"row_count": row_count},
                )

            return _check

        checks.append(_make_check(source_name, silver_asset_name))

    return checks


# ── Module-level generation ──────────────────────────────────────────────────

_bronze_assets = make_bronze_assets()
_silver_assets = make_silver_assets()
_bronze_freshness_sensor = _make_freshness_sensor()
_silver_checks = make_silver_checks()

bronze_assets = _bronze_assets
silver_assets = _silver_assets
all_assets = [*_bronze_assets, *_silver_assets]
mlperf_freshness_sensor = _bronze_freshness_sensor
