"""Bronze → Silver transform for MLPerf inference benchmark data.

Pure transform function + orchestration run().

Silver output: one row per (model_name, accelerator, scenario) with best
tokens_per_sec across all submitters and rounds, plus wh_per_million_tokens
derived from static TDP lookup.

Wh/M-tokens = TDP_watts * 1_000_000 / (tokens_per_sec * 3600)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pandas as pd
import structlog

from ingestion import iceberg_io
from ingestion.iceberg_schemas import SILVER_MLPERF_EFFICIENCY_SCHEMA
from transformations.gpu_tdp_lookup import get_tdp
from transformations.quality_report import run_silver_quality_report

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

logger = structlog.get_logger()

_GROUP_COLS = ["model_name", "accelerator", "scenario"]


def transform_mlperf_bronze_to_silver(df: pd.DataFrame) -> pd.DataFrame:
    """Pure function — no I/O.

    Input: Bronze mlperf_benchmarks rows (may have multiple rounds/submitters).
    Output: best tokens_per_sec per (model_name, accelerator, scenario) + efficiency.
    """
    if df.empty:
        return pd.DataFrame(columns=["round_id"] + _GROUP_COLS + ["tokens_per_sec", "tdp_watts", "wh_per_million_tokens"])

    df = df.copy()
    df["tokens_per_sec"] = pd.to_numeric(df["tokens_per_sec"], errors="coerce")
    df = df.dropna(subset=["tokens_per_sec", "model_name", "accelerator"])
    df = df[df["tokens_per_sec"] > 0]

    # Keep best result per group across all rounds
    best = (
        df.sort_values("tokens_per_sec", ascending=False)
        .groupby(_GROUP_COLS, as_index=False)
        .first()[["round_id"] + _GROUP_COLS + ["tokens_per_sec"]]
    )

    best["tdp_watts"] = best["accelerator"].map(get_tdp)
    # wh_per_million_tokens: NaN where TDP unknown — downstream dbt handles nulls
    best["wh_per_million_tokens"] = (
        best["tdp_watts"] * 1_000_000 / (best["tokens_per_sec"] * 3600)
    )

    return best.reset_index(drop=True)


def run(catalog: "Catalog") -> dict:
    df = iceberg_io.scan_table(catalog, "bronze", "mlperf_benchmarks")
    silver_df = transform_mlperf_bronze_to_silver(df)
    iceberg_io.overwrite_table(
        catalog, "silver", "mlperf_efficiency", silver_df, SILVER_MLPERF_EFFICIENCY_SCHEMA
    )
    report = run_silver_quality_report(silver_df, "silver.mlperf_efficiency")
    logger.info("mlperf_bronze_to_silver_done", **report)
    return {"table": "iceberg:silver.mlperf_efficiency", "row_count": len(silver_df)}
