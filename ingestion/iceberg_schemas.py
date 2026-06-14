"""Iceberg schema and partition spec definitions for all medallion layers.

Domain: AI inference energy & cost (SDS-040).
Sources: Electricity Maps, MLCommons MLPerf, Azure/AWS pricing, FRED FX rates.

The hardcoded schemas below are **deprecated** in favour of YAML-driven schemas
(see ``config/schemas/``).  Use ``schema_from_config()`` for new sources.
Existing schemas kept for backward compatibility during migration (SDS-043).
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pyiceberg.partitioning import PartitionField, PartitionSpec
from pyiceberg.schema import Schema
from pyiceberg.transforms import DayTransform
from pyiceberg.types import (
    DateType,
    DoubleType,
    NestedField,
    StringType,
    TimestamptzType,
)

# YAML type string → pyiceberg type constructor
_TYPE_MAP: dict[str, Any] = {
    "string": StringType,
    "double": DoubleType,
    "date": DateType,
    "timestamptz": TimestamptzType,
}

# Partition transform string → pyiceberg transform class
_TRANSFORM_MAP: dict[str, Any] = {
    "day": DayTransform,
}

_PROJECT_ROOT = Path(__file__).resolve().parents[1]
_SCHEMAS_DIR = _PROJECT_ROOT / "config" / "schemas"


def schema_from_config(config: dict[str, Any]) -> tuple[Schema, PartitionSpec]:
    """Build pyiceberg Schema + PartitionSpec from a YAML config dict.

    Config format (see ``config/schemas/`` for examples)::

        source: mlperf_benchmarks
        columns:
          - name: round_id
            type: string
          - name: tokens_per_sec
            type: double
        partition:
          field: _ingestion_timestamp
          transform: day

    Returns ``(Schema, PartitionSpec)``.  If no ``partition`` key is present
    the partition spec is empty.
    """
    fields = []
    for idx, col in enumerate(config["columns"], start=1):
        type_name = col["type"]
        pyiceberg_type = _TYPE_MAP.get(type_name)
        if pyiceberg_type is None:
            raise ValueError(
                f"Unknown type '{type_name}' for column '{col['name']}' "
                f"in source '{config.get('source', '?')}'. Known types: {list(_TYPE_MAP)}"
            )
        fields.append(NestedField(idx, col["name"], pyiceberg_type(), required=False))

    schema = Schema(*fields)

    partition_spec = PartitionSpec()
    partition_cfg = config.get("partition")
    if partition_cfg:
        field_name = partition_cfg["field"]
        transform_name = partition_cfg["transform"]
        transform_cls = _TRANSFORM_MAP.get(transform_name)
        if transform_cls is None:
            raise ValueError(
                f"Unknown partition transform '{transform_name}'. "
                f"Known transforms: {list(_TRANSFORM_MAP)}"
            )
        source_id = None
        for field in fields:
            if field.name == field_name:
                source_id = field.field_id
                break
        if source_id is None:
            raise ValueError(
                f"Partition field '{field_name}' not found in columns "
                f"for source '{config.get('source', '?')}'"
            )
        partition_spec = PartitionSpec(
            PartitionField(
                source_id=source_id, field_id=1000,
                transform=transform_cls(), name="ingestion_day",
            ),
        )

    return schema, partition_spec


def load_schema_config(source_name: str) -> dict[str, Any]:
    """Load a YAML schema config file for *source_name*.

    Looks for ``config/schemas/{source_name}.yaml``.
    """
    path = _SCHEMAS_DIR / f"{source_name}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"Schema config not found: {path}")
    with open(path) as f:
        return yaml.safe_load(f)

# ── Bronze ───────────────────────────────────────────────────────────────────
# All Bronze tables: append-only, partitioned on _ingestion_timestamp by day.

BRONZE_CARBON_INTENSITY_SCHEMA = Schema(
    NestedField(1, "timestamp_utc", TimestamptzType(), required=False),
    NestedField(2, "country", StringType(), required=False),
    NestedField(3, "carbon_intensity_gco2_kwh", DoubleType(), required=False),
    NestedField(4, "_ingestion_timestamp", TimestamptzType(), required=False),
    NestedField(5, "_source", StringType(), required=False),
)

BRONZE_CARBON_INTENSITY_PARTITION = PartitionSpec(
    PartitionField(source_id=4, field_id=1000, transform=DayTransform(), name="ingestion_day"),
)

BRONZE_MLPERF_BENCHMARKS_SCHEMA = Schema(
    NestedField(1, "round_id", StringType(), required=False),
    NestedField(2, "model_name", StringType(), required=False),
    NestedField(3, "accelerator", StringType(), required=False),
    NestedField(4, "submitter", StringType(), required=False),
    NestedField(5, "scenario", StringType(), required=False),
    NestedField(6, "tokens_per_sec", DoubleType(), required=False),
    NestedField(7, "_ingestion_timestamp", TimestamptzType(), required=False),
    NestedField(8, "_source", StringType(), required=False),
)

BRONZE_MLPERF_BENCHMARKS_PARTITION = PartitionSpec(
    PartitionField(source_id=7, field_id=1000, transform=DayTransform(), name="ingestion_day"),
)

BRONZE_CLOUD_GPU_PRICING_SCHEMA = Schema(
    NestedField(1, "provider", StringType(), required=False),
    NestedField(2, "instance_type", StringType(), required=False),
    NestedField(3, "region", StringType(), required=False),
    NestedField(4, "price_usd_per_hour", DoubleType(), required=False),
    NestedField(5, "sku_name", StringType(), required=False),
    NestedField(6, "captured_at", TimestamptzType(), required=False),
    NestedField(7, "_ingestion_timestamp", TimestamptzType(), required=False),
    NestedField(8, "_source", StringType(), required=False),
)

BRONZE_CLOUD_GPU_PRICING_PARTITION = PartitionSpec(
    PartitionField(source_id=7, field_id=1000, transform=DayTransform(), name="ingestion_day"),
)

BRONZE_FX_RATES_SCHEMA = Schema(
    NestedField(1, "observation_date", DateType(), required=False),
    NestedField(2, "eur_usd", DoubleType(), required=False),
    NestedField(3, "_ingestion_timestamp", TimestamptzType(), required=False),
    NestedField(4, "_source", StringType(), required=False),
)

BRONZE_FX_RATES_PARTITION = PartitionSpec(
    PartitionField(source_id=3, field_id=1000, transform=DayTransform(), name="ingestion_day"),
)

BRONZE_ENTSO_GENERATION_SCHEMA = Schema(
    NestedField(1, "timestamp_utc", TimestamptzType(), required=False),
    NestedField(2, "country", StringType(), required=False),
    NestedField(3, "psr_type", StringType(), required=False),
    NestedField(4, "psr_type_name", StringType(), required=False),
    NestedField(5, "quantity_mw", DoubleType(), required=False),
    NestedField(6, "resolution", StringType(), required=False),
    NestedField(7, "_ingestion_timestamp", TimestamptzType(), required=False),
    NestedField(8, "_source", StringType(), required=False),
)

BRONZE_ENTSO_GENERATION_PARTITION = PartitionSpec(
    PartitionField(source_id=7, field_id=1000, transform=DayTransform(), name="ingestion_day"),
)

# Rejected records — narrow fixed schema, original fields as JSON in `payload`.
BRONZE_REJECTED_SCHEMA = Schema(
    NestedField(1, "source", StringType(), required=False),
    NestedField(2, "rejection_reason", StringType(), required=False),
    NestedField(3, "payload", StringType(), required=False),
    NestedField(4, "_ingested_at", TimestamptzType(), required=False),
)

# ── Silver ───────────────────────────────────────────────────────────────────
# All Silver tables: full overwrite per pipeline run, no partition.

SILVER_CARBON_INTENSITY_SCHEMA = Schema(
    NestedField(1, "timestamp_hour", TimestamptzType(), required=False),
    NestedField(2, "country", StringType(), required=False),
    NestedField(3, "carbon_intensity_gco2_kwh", DoubleType(), required=False),
)

SILVER_MLPERF_EFFICIENCY_SCHEMA = Schema(
    NestedField(1, "round_id", StringType(), required=False),
    NestedField(2, "model_name", StringType(), required=False),
    NestedField(3, "accelerator", StringType(), required=False),
    NestedField(4, "tokens_per_sec", DoubleType(), required=False),
    NestedField(5, "tdp_watts", DoubleType(), required=False),
    NestedField(6, "wh_per_million_tokens", DoubleType(), required=False),
)

SILVER_CLOUD_GPU_PRICING_SCHEMA = Schema(
    NestedField(1, "provider", StringType(), required=False),
    NestedField(2, "instance_type", StringType(), required=False),
    NestedField(3, "region", StringType(), required=False),
    NestedField(4, "accelerator", StringType(), required=False),
    NestedField(5, "price_eur_per_hour", DoubleType(), required=False),
    NestedField(6, "valid_from", DateType(), required=False),
)
