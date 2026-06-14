"""Bronze-layer Iceberg writer for SoloDShouse."""

from __future__ import annotations

import datetime as dt
import json
from typing import TYPE_CHECKING, Any

import pandas as pd
import structlog

from ingestion import iceberg_io
from ingestion.iceberg_schemas import (
    BRONZE_CARBON_INTENSITY_PARTITION,
    BRONZE_CARBON_INTENSITY_SCHEMA,
    BRONZE_CLOUD_GPU_PRICING_PARTITION,
    BRONZE_CLOUD_GPU_PRICING_SCHEMA,
    BRONZE_ENTSO_GENERATION_PARTITION,
    BRONZE_ENTSO_GENERATION_SCHEMA,
    BRONZE_FX_RATES_PARTITION,
    BRONZE_FX_RATES_SCHEMA,
    BRONZE_MLPERF_BENCHMARKS_PARTITION,
    BRONZE_MLPERF_BENCHMARKS_SCHEMA,
    BRONZE_REJECTED_SCHEMA,
    load_schema_config,
    schema_from_config,
)
from storage_config import get_data_bucket

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

logger = structlog.get_logger()

# DEPRECATED: hardcoded table metadata — retained for backward compatibility
# during migration to YAML-driven schemas (SDS-043).
# New sources should define their schema in config/schemas/{source}.yaml.
_BRONZE_TABLE_META = {
    "carbon_intensity": (BRONZE_CARBON_INTENSITY_SCHEMA, BRONZE_CARBON_INTENSITY_PARTITION),
    "mlperf_benchmarks": (BRONZE_MLPERF_BENCHMARKS_SCHEMA, BRONZE_MLPERF_BENCHMARKS_PARTITION),
    "cloud_gpu_pricing": (BRONZE_CLOUD_GPU_PRICING_SCHEMA, BRONZE_CLOUD_GPU_PRICING_PARTITION),
    "fx_rates": (BRONZE_FX_RATES_SCHEMA, BRONZE_FX_RATES_PARTITION),
    "entso_generation": (BRONZE_ENTSO_GENERATION_SCHEMA, BRONZE_ENTSO_GENERATION_PARTITION),
}


def _resolve_schema(source: str) -> tuple[Any, Any]:
    """Resolve Iceberg (schema, partition_spec) for *source*.

    Priority: YAML config → hardcoded fallback → default.
    """
    try:
        config = load_schema_config(source)
        return schema_from_config(config)
    except FileNotFoundError:
        pass
    return _BRONZE_TABLE_META.get(source, (BRONZE_CARBON_INTENSITY_SCHEMA, None))


class BronzeWriter:
    def __init__(self, catalog: "Catalog", bucket: str | None = None):
        self.catalog = catalog
        self.bucket = bucket or get_data_bucket()  # kept for observability logging

    def write(self, df: pd.DataFrame, source: str) -> str:
        """Append *df* to the Bronze Iceberg table for *source* and return a logical path."""
        schema, partition_spec = _resolve_schema(source)

        iceberg_io.append_table(
            self.catalog,
            namespace="bronze",
            table_name=source,
            df=df,
            schema=schema,
            partition_spec=partition_spec,
        )
        path = f"iceberg:bronze.{source}"
        logger.info("bronze_written", source=source, rows=len(df), path=path)
        return path

    def write_rejected(
        self,
        records: list[dict[str, Any]],
        source: str,
    ) -> str | None:
        """Append rejected records to the Bronze rejected Iceberg table."""
        if not records:
            return None

        for record in records:
            reason = record.get("rejection_reason")
            if not isinstance(reason, str) or not reason.strip():
                raise ValueError("Each rejected record must include a non-empty rejection_reason")

        now = dt.datetime.now(dt.UTC)
        rows = []
        for rec in records:
            payload_dict = {k: v for k, v in rec.items() if k != "rejection_reason"}
            rows.append(
                {
                    "source": source,
                    "rejection_reason": rec["rejection_reason"],
                    "payload": json.dumps(payload_dict, default=str),
                    "_ingested_at": now,
                }
            )
        rejected_df = pd.DataFrame(rows)

        iceberg_io.append_table(
            self.catalog,
            namespace="bronze",
            table_name="rejected_records",
            df=rejected_df,
            schema=BRONZE_REJECTED_SCHEMA,
        )
        path = f"iceberg:bronze.rejected_records[source={source}]"
        logger.info("bronze_rejected_written", source=source, count=len(records))
        return path
