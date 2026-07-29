---
title: Iceberg Schemas
summary: Reference for all Iceberg schema definitions (Bronze/Silver), YAML-driven schema format, and partition specs used in SoloDShouse's medallion architecture.
topics: [reference, data-model, schemas]
---

# Iceberg Schemas

This reference documents all Iceberg schema definitions used in SoloDShouse's
medallion architecture. Schemas are defined in two ways: hardcoded constants
in `ingestion/iceberg_schemas.py` (legacy) and YAML-driven schemas in
`config/schemas/` (preferred for new sources).

## Schema Definition Format

### Hardcoded Schemas (Legacy)

Hardcoded schemas are defined as PyIceberg `Schema` and `PartitionSpec`
objects in `ingestion/iceberg_schemas.py`. These are retained for backward
compatibility during migration to YAML-driven schemas (SDS-043).

#### Bronze Layer Schemas

All Bronze tables follow the same pattern: append-only, partitioned by day
on `_ingestion_timestamp`.

**Carbon Intensity**

```python
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
```

**MLPerf Benchmarks**

```python
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
```

**Cloud GPU Pricing**

```python
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
```

**FX Rates**

```python
BRONZE_FX_RATES_SCHEMA = Schema(
    NestedField(1, "observation_date", DateType(), required=False),
    NestedField(2, "eur_usd", DoubleType(), required=False),
    NestedField(3, "_ingestion_timestamp", TimestamptzType(), required=False),
    NestedField(4, "_source", StringType(), required=False),
)
```

**ENTSO-E Generation**

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
```

**Rejected Records**

```python
BRONZE_REJECTED_SCHEMA = Schema(
    NestedField(1, "source", StringType(), required=False),
    NestedField(2, "rejection_reason", StringType(), required=False),
    NestedField(3, "payload", StringType(), required=False),
    NestedField(4, "_ingested_at", TimestamptzType(), required=False),
)
```

#### Silver Layer Schemas

Silver tables use full overwrite per pipeline run with no partitioning.

**Carbon Intensity (Silver)**

```python
SILVER_CARBON_INTENSITY_SCHEMA = Schema(
    NestedField(1, "timestamp_hour", TimestamptzType(), required=False),
    NestedField(2, "country", StringType(), required=False),
    NestedField(3, "carbon_intensity_gco2_kwh", DoubleType(), required=False),
)
```

**MLPerf Efficiency (Silver)**

```python
SILVER_MLPERF_EFFICIENCY_SCHEMA = Schema(
    NestedField(1, "round_id", StringType(), required=False),
    NestedField(2, "model_name", StringType(), required=False),
    NestedField(3, "accelerator", StringType(), required=False),
    NestedField(4, "tokens_per_sec", DoubleType(), required=False),
    NestedField(5, "tdp_watts", DoubleType(), required=False),
    NestedField(6, "wh_per_million_tokens", DoubleType(), required=False),
)
```

**Cloud GPU Pricing (Silver)**

```python
SILVER_CLOUD_GPU_PRICING_SCHEMA = Schema(
    NestedField(1, "provider", StringType(), required=False),
    NestedField(2, "instance_type", StringType(), required=False),
    NestedField(3, "region", StringType(), required=False),
    NestedField(4, "accelerator", StringType(), required=False),
    NestedField(5, "price_eur_per_hour", DoubleType(), required=False),
    NestedField(6, "valid_from", DateType(), required=False),
)
```

## YAML-Driven Schema Format

New sources should use YAML-driven schemas in `config/schemas/{source_name}.yaml`:

```yaml
source: my_source
connection_type: rest
columns:
  - name: timestamp
    type: timestamptz
  - name: value
    type: double
  - name: category
    type: string
partition:
  field: _ingestion_timestamp
  transform: day
```

The YAML format is processed by `schema_from_config()` in `ingestion/iceberg_schemas.py`:

```python
def schema_from_config(config: dict[str, Any]) -> tuple[Schema, PartitionSpec]:
    """Build pyiceberg Schema + PartitionSpec from a YAML config dict."""
    fields = []
    for idx, col in enumerate(config["columns"], start=1):
        type_name = col["type"]
        pyiceberg_type = _TYPE_MAP.get(type_name)
        if pyiceberg_type is None:
            raise ValueError(...)
        fields.append(NestedField(idx, col["name"], pyiceberg_type(), required=False))

    schema = Schema(*fields)

    partition_spec = PartitionSpec()
    partition_cfg = config.get("partition")
    if partition_cfg:
        field_name = partition_cfg["field"]
        transform_name = partition_cfg["transform"]
        transform_cls = _TRANSFORM_MAP.get(transform_name)
        # ... create partition field
```

### Supported Types

| YAML type | PyIceberg type |
|-----------|----------------|
| `string` | `StringType` |
| `double` | `DoubleType` |
| `date` | `DateType` |
| `timestamptz` | `TimestamptzType` |
| `long` | `LongType` |
| `int` | `IntType` |
| `boolean` | `BooleanType` |
| `float` | `FloatType` |
| `timestamp` | `TimestampType` |
| `decimal(38,18)` | `DecimalType(38, 18)` |

### Supported Partition Transforms

| YAML transform | PyIceberg transform |
|----------------|---------------------|
| `day` | `DayTransform` |

## Partition Specification

All Bronze tables use day partitioning on `_ingestion_timestamp`:

```python
PartitionSpec(
    PartitionField(
        source_id=field_id,  # ID of the _ingestion_timestamp field
        field_id=1000,       # Fixed partition field ID
        transform=DayTransform(),
        name="ingestion_day",
    ),
)
```

This enables efficient time-range queries and incremental processing.

## Schema Resolution

The `BronzeWriter._resolve_schema()` function resolves schemas with priority:

1. **YAML config**: `load_schema_config(source)` → `schema_from_config(config)`
2. **Hardcoded fallback**: `_BRONZE_TABLE_META.get(source, ...)`
3. **Default**: `BRONZE_CARBON_INTENSITY_SCHEMA` (if no match)

```python
def _resolve_schema(source: str) -> tuple[Any, Any]:
    try:
        config = load_schema_config(source)
        return schema_from_config(config)
    except FileNotFoundError:
        pass
    return _BRONZE_TABLE_META.get(source, (BRONZE_CARBON_INTENSITY_SCHEMA, None))
```

## See Also

- [Medallion Architecture](../concepts/medallion-architecture.md) — Bronze→Silver→Gold
- [Iceberg I/O](../concepts/iceberg-io.md) — pyiceberg abstraction
- [Ingestion Pipeline](../architecture/ingestion-pipeline.md) — full data flow
- [Environment Variables](environment-variables.md) — all env vars
