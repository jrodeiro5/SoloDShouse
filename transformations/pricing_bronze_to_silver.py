"""Bronze → Silver transform for cloud GPU pricing and FX rates.

Pure transform function + orchestration run().

Silver output: one row per (provider, instance_type, region) with latest
price_usd converted to EUR, accelerator populated from instance_gpu_map,
valid_from date from captured_at.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import structlog

from ingestion import iceberg_io
from ingestion.iceberg_schemas import SILVER_CLOUD_GPU_PRICING_SCHEMA
from transformations.instance_gpu_map import get_instance_gpu
from transformations.quality_report import run_silver_quality_report

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

logger = structlog.get_logger()

_DEDUP_COLS = ["provider", "instance_type", "region"]


def transform_pricing_bronze_to_silver(
    pricing_df: pd.DataFrame,
    fx_df: pd.DataFrame,
) -> pd.DataFrame:
    """Pure function — no I/O.

    Args:
        pricing_df: Bronze cloud_gpu_pricing rows.
        fx_df: Bronze fx_rates rows (observation_date, eur_usd).

    Returns:
        Silver rows with price_eur_per_hour, accelerator, valid_from.
    """
    if pricing_df.empty:
        return pd.DataFrame(columns=["provider", "instance_type", "region", "accelerator", "price_eur_per_hour", "valid_from"])

    df = pricing_df.copy()
    df["captured_at"] = pd.to_datetime(df["captured_at"], utc=True, errors="coerce")
    df["price_usd_per_hour"] = pd.to_numeric(df["price_usd_per_hour"], errors="coerce")
    df = df.dropna(subset=["price_usd_per_hour", "captured_at"])
    df = df[df["price_usd_per_hour"] > 0]

    # Keep most recent price per (provider, instance_type, region)
    df = (
        df.sort_values("captured_at", ascending=False)
        .groupby(_DEDUP_COLS, as_index=False)
        .first()
    )

    # FX: latest available rate
    eur_usd: float | None = None
    if not fx_df.empty:
        fx = fx_df.copy()
        fx["observation_date"] = pd.to_datetime(fx["observation_date"], errors="coerce")
        fx = fx.dropna(subset=["eur_usd", "observation_date"])
        fx["eur_usd"] = pd.to_numeric(fx["eur_usd"], errors="coerce")
        fx = fx[fx["eur_usd"] > 0]
        if not fx.empty:
            eur_usd = float(fx.sort_values("observation_date", ascending=False).iloc[0]["eur_usd"])

    if eur_usd is None or eur_usd <= 0:
        logger.warning("pricing_no_fx_rate_available_using_fallback")
        eur_usd = 1.0  # 1:1 fallback — downstream dbt handles nulls

    df["price_eur_per_hour"] = df["price_usd_per_hour"] / eur_usd
    df["valid_from"] = df["captured_at"].dt.date

    def _accelerator(sku: str) -> str | None:
        info = get_instance_gpu(sku)
        return info.accelerator if info else None

    df["accelerator"] = df["instance_type"].map(_accelerator)

    return df[["provider", "instance_type", "region", "accelerator", "price_eur_per_hour", "valid_from"]].reset_index(drop=True)


def run(catalog: "Catalog") -> dict:
    pricing_df = iceberg_io.scan_table(catalog, "bronze", "cloud_gpu_pricing")
    try:
        fx_df = iceberg_io.scan_table(catalog, "bronze", "fx_rates")
    except Exception:
        logger.warning("pricing_bronze_to_silver_no_fx_table")
        fx_df = pd.DataFrame()

    silver_df = transform_pricing_bronze_to_silver(pricing_df, fx_df)
    iceberg_io.overwrite_table(
        catalog, "silver", "cloud_gpu_pricing", silver_df, SILVER_CLOUD_GPU_PRICING_SCHEMA
    )
    report = run_silver_quality_report(silver_df, "silver.cloud_gpu_pricing")
    logger.info("pricing_bronze_to_silver_done", **report)
    return {"table": "iceberg:silver.cloud_gpu_pricing", "row_count": len(silver_df)}
