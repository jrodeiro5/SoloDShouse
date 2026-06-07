"""Dagster software-defined assets for SoloDShouse AI energy cost domain."""

from __future__ import annotations

import time
from datetime import date, datetime, timezone
from typing import Any

import pandas as pd
import structlog
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
from resources import IcebergCatalogResource

from ingestion import iceberg_io
from ingestion.collectors.cloud_pricing_collector import CloudPricingCollector
from ingestion.collectors.mlperf_collector import MLPerfCollector
from transformations import mlperf_bronze_to_silver, pricing_bronze_to_silver

logger = structlog.get_logger()


def _emit_metric(step: str, started_at: float) -> None:
    duration_ms = int((time.perf_counter() - started_at) * 1000)
    logger.info("pipeline_metric", metric="pipeline.step.duration_ms", step=step, value=duration_ms)


def _row_count(result: dict[str, Any]) -> int:
    v = result.get("row_count", 0)
    try:
        return int(v)
    except (TypeError, ValueError):
        return 0


# ── Bronze ────────────────────────────────────────────────────────────────────


@asset(group_name="bronze", retry_policy=RetryPolicy(max_retries=3, delay=10))
def mlperf_bronze(
    context,
    iceberg_catalog: IcebergCatalogResource,
) -> dict[str, Any]:
    """Ingest MLCommons MLPerf inference benchmark results → Bronze."""
    started = time.perf_counter()
    result = MLPerfCollector(iceberg_catalog.get_catalog()).collect()
    context.add_output_metadata(
        {
            "round_id": result.get("round_id", ""),
            "valid": result.get("valid", 0),
            "rejected": result.get("rejected", 0),
        }
    )
    _emit_metric("mlperf_bronze", started)
    return result


@asset(group_name="bronze", retry_policy=RetryPolicy(max_retries=3, delay=10))
def cloud_pricing_bronze(
    context,
    iceberg_catalog: IcebergCatalogResource,
) -> dict[str, Any]:
    """Ingest Azure GPU pricing + FRED FX rates → Bronze (two tables)."""
    started = time.perf_counter()
    result = CloudPricingCollector(iceberg_catalog.get_catalog()).collect()
    context.add_output_metadata(
        {
            "azure_valid": result.get("azure_valid", 0),
            "azure_rejected": result.get("azure_rejected", 0),
            "fx_valid": result.get("fx_valid", 0),
            "fx_skipped": str(result.get("fx_skipped", False)),
        }
    )
    _emit_metric("cloud_pricing_bronze", started)
    return result


# NOTE: carbon_intensity_bronze — blocked on ELECTRICITY_MAPS_API_KEY (~June 2026)


# ── Silver ────────────────────────────────────────────────────────────────────


@asset(group_name="silver")
def mlperf_silver(
    context,
    iceberg_catalog: IcebergCatalogResource,
    mlperf_bronze: dict[str, Any],
) -> str:
    """Transform MLPerf Bronze → Silver efficiency table."""
    _ = mlperf_bronze
    started = time.perf_counter()
    result = mlperf_bronze_to_silver.run(iceberg_catalog.get_catalog())
    context.add_output_metadata(
        {"table": result["table"], "row_count": _row_count(result)}
    )
    _emit_metric("mlperf_silver", started)
    return str(result["table"])


@asset(group_name="silver")
def cloud_pricing_silver(
    context,
    iceberg_catalog: IcebergCatalogResource,
    cloud_pricing_bronze: dict[str, Any],
) -> str:
    """Transform cloud GPU pricing Bronze → Silver (USD→EUR, dedup, accelerator map)."""
    _ = cloud_pricing_bronze
    started = time.perf_counter()
    result = pricing_bronze_to_silver.run(iceberg_catalog.get_catalog())
    context.add_output_metadata(
        {"table": result["table"], "row_count": _row_count(result)}
    )
    _emit_metric("cloud_pricing_silver", started)
    return str(result["table"])


# NOTE: carbon_intensity_silver — blocked on carbon_intensity_bronze
# NOTE: ai_inference_gold — blocked on Phase H (dbt Silver→Gold, needs real data)


# ── Sensor ────────────────────────────────────────────────────────────────────


@sensor(job_name="full_pipeline_job", minimum_interval_seconds=3600 * 24)
def mlperf_freshness_sensor(
    iceberg_catalog: IcebergCatalogResource,
):
    """Trigger pipeline if MLPerf Bronze missing or older than 30 days."""
    from pyiceberg.exceptions import NoSuchTableError

    catalog = iceberg_catalog.get_catalog()
    latest: date | None = None

    try:
        df = iceberg_io.scan_table(catalog, "bronze", "mlperf_benchmarks")
        if not df.empty:
            latest = pd.to_datetime(df["_ingestion_timestamp"], utc=True).max().date()
    except NoSuchTableError:
        pass

    if latest is None:
        return RunRequest(
            run_key=f"mlperf-init-{datetime.now(timezone.utc).date().isoformat()}",
            asset_selection=[AssetKey("mlperf_bronze")],
        )

    lag_days = (datetime.now(timezone.utc).date() - latest).days
    if lag_days >= 30:
        return RunRequest(
            run_key=f"mlperf-stale-{latest.isoformat()}",
            asset_selection=[AssetKey("mlperf_bronze")],
        )
    return SkipReason(f"MLPerf data fresh: latest {latest.isoformat()} ({lag_days}d ago)")


# ── Asset checks ──────────────────────────────────────────────────────────────


@asset_check(asset=mlperf_silver, description="mlperf_efficiency must have at least 1 row")
def mlperf_silver_min_rows_check(
    iceberg_catalog: IcebergCatalogResource,
    mlperf_silver: str,
) -> AssetCheckResult:
    _ = mlperf_silver
    df = iceberg_io.scan_table(iceberg_catalog.get_catalog(), "silver", "mlperf_efficiency")
    row_count = len(df)
    passed = row_count >= 1
    return AssetCheckResult(
        passed=passed,
        description=f"mlperf_efficiency has {row_count} rows",
        metadata={"row_count": row_count},
    )


@asset_check(asset=cloud_pricing_silver, description="cloud_gpu_pricing must have at least 1 row")
def cloud_pricing_silver_min_rows_check(
    iceberg_catalog: IcebergCatalogResource,
    cloud_pricing_silver: str,
) -> AssetCheckResult:
    _ = cloud_pricing_silver
    df = iceberg_io.scan_table(iceberg_catalog.get_catalog(), "silver", "cloud_gpu_pricing")
    row_count = len(df)
    passed = row_count >= 1
    return AssetCheckResult(
        passed=passed,
        description=f"cloud_gpu_pricing has {row_count} rows",
        metadata={"row_count": row_count},
    )
