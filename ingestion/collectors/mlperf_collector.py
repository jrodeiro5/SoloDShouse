"""MLPerfCollector — ingests MLCommons MLPerf inference benchmark results.

Data source: public CSV from MLCommons GitHub (no API key required).
Configure URL via MLPERF_RESULTS_URL env var or pass csv_url to collect().

Expected CSV columns (configurable via MLPERF_COLUMN_MAP env var as JSON):
  - round_id: benchmark round, e.g. "v4.1"
  - model_name: model benchmark name
  - accelerator: GPU/accelerator name
  - submitter: submitting organization
  - scenario: "Offline", "Server", etc.
  - tokens_per_sec: throughput (LLM models only; skip non-LLM rows)
"""

from __future__ import annotations

import datetime as dt
import json
import os
from io import StringIO
from typing import TYPE_CHECKING

import pandas as pd
import requests
import structlog

from ingestion.bronze_writer import BronzeWriter
from ingestion.collectors.base import BaseCollector
from ingestion.collectors.registry import register_collector
from ingestion.exceptions import CollectorUnavailableError
from ingestion.http import make_session
from ingestion.schema.mlperf_records import MLPerfRecord

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

logger = structlog.get_logger()

# Default CSV URL — MLCommons v4.1 closed datacenter aggregate results.
# Override with MLPERF_RESULTS_URL if format differs.
_DEFAULT_CSV_URL = os.environ.get(
    "MLPERF_RESULTS_URL",
    "https://raw.githubusercontent.com/mlcommons/inference_results_v4.1/main/closed/results.csv",
)

# Column mapping: our field name → CSV column name.
# Override the entire map by setting MLPERF_COLUMN_MAP as a JSON env var.
_DEFAULT_COLUMN_MAP: dict[str, str] = {
    "round_id": "round_id",
    "model_name": "model_benchmark",
    "accelerator": "accelerator",
    "submitter": "submitter",
    "scenario": "scenario",
    "tokens_per_sec": "result_tokens_per_second",
}

# LLM model names that produce tokens/sec throughput in MLPerf inference.
_LLM_MODELS = {"llama2-70b", "llama2-7b", "mixtral-8x7b", "gpt-j-6b", "llama3-70b", "llama3-8b"}


@register_collector("mlperf_benchmarks")
class MLPerfCollector(BaseCollector):
    def __init__(self, catalog: "Catalog"):
        super().__init__(catalog)
        self.bronze_writer = BronzeWriter(catalog)

    def _fetch_data(self, csv_url: str) -> pd.DataFrame:
        try:
            resp = make_session().get(csv_url, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise CollectorUnavailableError(f"MLPerf CSV fetch failed: {exc}") from exc
        return pd.read_csv(StringIO(resp.text))

    def _validate_records(self, df: pd.DataFrame, round_id: str) -> tuple[list[dict], list[dict]]:
        col_map_raw = os.environ.get("MLPERF_COLUMN_MAP")
        col_map = json.loads(col_map_raw) if col_map_raw else _DEFAULT_COLUMN_MAP

        # Rename CSV columns to our schema names where they differ
        rename = {v: k for k, v in col_map.items() if v in df.columns and v != k}
        df = df.rename(columns=rename)

        # Filter to LLM models only (tokens_per_sec is meaningful there)
        if "model_name" in df.columns:
            df = df[df["model_name"].str.lower().isin(_LLM_MODELS)]

        # Inject round_id if not in CSV
        if "round_id" not in df.columns:
            df = df.copy()
            df["round_id"] = round_id

        valid, rejected = [], []
        now = dt.datetime.now(dt.UTC)

        for row in df.to_dict(orient="records"):
            try:
                record = MLPerfRecord(
                    round_id=str(row.get("round_id", round_id)),
                    model_name=str(row.get("model_name", "")),
                    accelerator=str(row.get("accelerator", "")),
                    submitter=str(row["submitter"]) if "submitter" in row else None,
                    scenario=str(row["scenario"]) if "scenario" in row else None,
                    tokens_per_sec=float(row.get("tokens_per_sec", 0)),
                )
                d = record.model_dump()
                d["_ingestion_timestamp"] = now
                d["_source"] = "mlcommons_mlperf"
                valid.append(d)
            except (ValueError, KeyError, TypeError) as exc:
                rejected.append({**row, "rejection_reason": str(exc)})

        return valid, rejected

    def collect(self, round_id: str = "v4.1", csv_url: str | None = None) -> dict:
        url = csv_url or _DEFAULT_CSV_URL
        logger.info("mlperf_collect_start", round_id=round_id, url=url)

        raw_df = self._fetch_data(url)
        valid, rejected = self._validate_records(raw_df, round_id)

        if not valid:
            logger.warning("mlperf_no_valid_records", round_id=round_id, rejected=len(rejected))
        else:
            valid_df = pd.DataFrame(valid)
            self.bronze_writer.write(valid_df, source="mlperf_benchmarks")

        if rejected:
            self.bronze_writer.write_rejected(rejected, source="mlperf_benchmarks")

        logger.info(
            "mlperf_collect_done",
            round_id=round_id, valid=len(valid), rejected=len(rejected),
        )
        return {"round_id": round_id, "valid": len(valid), "rejected": len(rejected)}
