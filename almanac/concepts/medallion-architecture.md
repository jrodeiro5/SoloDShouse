---
title: Medallion Architecture
summary: Bronze→Silver→Gold medallion architecture using Apache Iceberg with append-only Bronze, full-overwrite Silver/Gold, and day-partitioned data.
topics: [concepts, architecture, ingestion, data-model]
---

# Medallion Architecture

SoloDShouse implements a medallion architecture using Apache Iceberg tables,
organizing data into three layers: Bronze (raw immutable records), Silver
(cleaned, typed, deduplicated data), and Gold (ML-ready feature matrices).

The architecture follows a clear data flow: collectors write raw data to Bronze
tables (append-only, day-partitioned), transformations produce Silver tables
(full overwrite per pipeline run), and feature engineering creates Gold tables
for machine learning consumption.

## Bronze Layer

Bronze tables store raw, immutable records from external sources. Each record
includes an `_ingestion_timestamp` field and is partitioned by day on this
field, enabling efficient time-range queries and incremental processing.

```python
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
```

Bronze writes use `append_table()` to add records without modifying existing
data. A separate `rejected_records` table tracks validation failures with
source, rejection reason, and original payload as JSON.

## Silver Layer

Silver tables contain cleaned, typed, and deduplicated data. Each pipeline run
performs a full overwrite of Silver tables, replacing all previous data with
the latest cleaned version.

```python
SILVER_CARBON_INTENSITY_SCHEMA = Schema(
    NestedField(1, "timestamp_hour", TimestamptzType(), required=False),
    NestedField(2, "country", StringType(), required=False),
    NestedField(3, "carbon_intensity_gco2_kwh", DoubleType(), required=False),
)
```

Silver transformations apply source-specific cleaning logic: type conversions,
null handling, deduplication, and derived field calculations. The Silver layer
serves as the foundation for Gold feature engineering.

## Gold Layer

Gold tables contain ML-ready feature matrices optimized for machine learning
workflows. Like Silver, Gold tables use full overwrite per pipeline run.

The Gold layer joins data from multiple Silver sources and applies feature
engineering to create prediction-ready datasets. These tables are consumed by
ML training pipelines and queryable via DuckDB (local) or Trino (federated).

## Data Flow

The complete data flow follows this pattern:

1. **Collectors** fetch raw data from external sources (APIs, databases, files)
2. **Bronze Writer** appends records to Bronze Iceberg tables with day partitioning
3. **Transformations** clean and type-cast Bronze data into Silver tables
4. **Feature Engineering** joins Silver sources and creates Gold feature matrices
5. **ML Pipelines** consume Gold tables for training and inference

```
External Sources → Collectors → Bronze (append) → Silver (overwrite) → Gold (overwrite) → ML
```

## Partitioning Strategy

All Bronze tables use day partitioning on `_ingestion_timestamp`, enabling
efficient time-range queries and incremental processing. The partition field
uses `DayTransform()` to group records by calendar day.

```python
PartitionSpec(
    PartitionField(
        source_id=field_id,
        field_id=1000,
        transform=DayTransform(),
        name="ingestion_day",
    ),
)
```

Silver and Gold tables do not use partitioning, as they are fully overwritten
per pipeline run and queries typically access the complete dataset.

## Schema Management

Schemas are defined in two ways:

1. **Hardcoded schemas** in `ingestion/iceberg_schemas.py` for backward
   compatibility during migration (SDS-043)
2. **YAML-driven schemas** in `config/schemas/` for new sources, enabling
   schema discovery and automatic collector registration

The `schema_from_config()` function converts YAML schema definitions to
PyIceberg `Schema` and `PartitionSpec` objects, supporting string, double,
date, timestamptz, and other Iceberg types.

## Timestamp Handling

Iceberg v1/v2 only supports microsecond (us) timestamp precision, but Python
3.11+ returns nanosecond-precision timestamps via pandas. The `_downcast_ns_timestamps()`
function in `iceberg_io.py` casts nanosecond timestamps to microseconds before
writing to Iceberg tables, ensuring compatibility.

## See Also

- [Iceberg I/O](iceberg-io.md) — pyiceberg abstraction layer
- [Collector Pattern](collector-pattern.md) — data ingestion plugin system
- [Ingestion Pipeline](../architecture/ingestion-pipeline.md) — full data flow
- [Dagster Orchestration](../architecture/dagster-orchestration.md) — pipeline orchestration
