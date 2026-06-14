"""Iceberg schema and partition spec definitions for all medallion layers.

Domain: AI inference energy & cost (SDS-040).
Sources: Electricity Maps, MLCommons MLPerf, Azure/AWS pricing, FRED FX rates.
Status: design-time estimates — see SDS-041 for open questions.
"""

from __future__ import annotations

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
