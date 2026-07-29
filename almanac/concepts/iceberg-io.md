---
title: Iceberg I/O
summary: PyIceberg abstraction layer providing catalog management, append/overwrite operations, and table scanning for the medallion architecture.
topics: [concepts, architecture, ingestion, data-model]
---

# Iceberg I/O

The Iceberg I/O module provides a thin abstraction layer over PyIceberg,
offering catalog management, table operations (append/overwrite/scan), and
type conversion utilities for SoloDShouse's medallion architecture.

This module centralizes all Iceberg interactions, ensuring consistent behavior
across collectors, transformations, and ML pipelines while handling
environment-specific configuration through environment variables.

## Catalog Management

The `get_catalog()` function creates a HiveCatalog backed by Hive Metastore
and SeaweedFS (S3-compatible object store). All parameters fall back to
environment variables, enabling both Docker and local development environments
to work without extra configuration.

```python
def get_catalog(
    name: str = "hive",
    uri: str | None = None,
    warehouse: str | None = None,
    s3_endpoint: str | None = None,
    access_key: str | None = None,
    secret_key: str | None = None,
) -> "Catalog":
```

The function reads storage configuration from `storage_config.get_storage_config()`
and constructs the HiveCatalog with the following properties:

- `uri`: Hive Metastore endpoint (default: `thrift://localhost:9083`)
- `warehouse`: S3 warehouse URI (converts `s3a://` to `s3://` for PyIceberg)
- `s3.endpoint`: SeaweedFS S3 endpoint (default: `http://localhost:8333`)
- `s3.access-key-id`: S3 access key (default: `solodshouse`)
- `s3.secret-access-key`: S3 secret key (default: `solodshouse123`)
- `s3.path-style-access`: `true` (required for SeaweedFS)

## Namespace Management

The `ensure_namespace()` function creates Iceberg namespaces idempotently,
logging creation events and silently ignoring `NamespaceAlreadyExistsError`
exceptions.

```python
def ensure_namespace(catalog: "Catalog", namespace: str) -> None:
    """Create namespace if it does not already exist (idempotent)."""
    try:
        catalog.create_namespace(namespace)
        logger.info("iceberg_namespace_created", namespace=namespace)
    except NamespaceAlreadyExistsError:
        pass
```

## Table Operations

### Append Table

The `append_table()` function adds records to an Iceberg table, creating it
if it doesn't exist. This is the primary write operation for Bronze layer
data, preserving historical records for audit and reprocessing.

```python
def append_table(
    catalog: "Catalog",
    namespace: str,
    table_name: str,
    df: pd.DataFrame,
    schema: "Schema",
    partition_spec: "PartitionSpec | None" = None,
) -> None:
```

The function:
1. Loads or creates the target table with the specified schema and partition spec
2. Converts the pandas DataFrame to an Arrow table
3. Downcasts nanosecond timestamps to microseconds (Iceberg compatibility)
4. Appends the records to the table
5. Logs the operation with table name and row count

### Overwrite Table

The `overwrite_table()` function replaces all records in an Iceberg table,
used for Silver and Gold layer updates where full table replacement is
preferred over incremental updates.

```python
def overwrite_table(
    catalog: "Catalog",
    namespace: str,
    table_name: str,
    df: pd.DataFrame,
    schema: "Schema",
    partition_spec: "PartitionSpec | None" = None,
) -> None:
```

The function follows the same steps as `append_table()` but calls
`tbl.overwrite(arrow_table)` instead of `tbl.append(arrow_table)`.

### Scan Table

The `scan_table()` function reads all records from an Iceberg table and
returns them as a pandas DataFrame, used by transformations and freshness
checks.

```python
def scan_table(
    catalog: "Catalog",
    namespace: str,
    table_name: str,
) -> pd.DataFrame:
```

## Timestamp Handling

Iceberg v1/v2 only supports microsecond (us) timestamp precision, but Python
3.11+ returns nanosecond-precision timestamps via pandas. The
`_downcast_ns_timestamps()` function handles this conversion:

```python
def _downcast_ns_timestamps(table: pa.Table) -> pa.Table:
    """Cast nanosecond-precision timestamp columns to microseconds."""
    new_fields = []
    needs_cast = False
    for field in table.schema:
        if pa.types.is_timestamp(field.type) and field.type.unit == "ns":
            new_fields.append(field.with_type(pa.timestamp("us", tz=field.type.tz)))
            needs_cast = True
        else:
            new_fields.append(field)
    if not needs_cast:
        return table
    return table.cast(pa.schema(new_fields))
```

This function iterates through all timestamp fields, checking if they use
nanosecond precision, and converts them to microsecond precision while
preserving timezone information.

## Internal Helpers

The `_get_or_create_table()` function handles table loading with automatic
namespace creation:

```python
def _get_or_create_table(
    catalog: "Catalog",
    namespace: str,
    table_name: str,
    schema: "Schema",
    partition_spec: "PartitionSpec | None",
) -> Any:
```

It attempts to load the table, and if it doesn't exist (`NoSuchTableError`),
it ensures the namespace exists and creates the table with the specified
schema and partition spec.

## Error Handling

The module handles several error scenarios:

- `NamespaceAlreadyExistsError`: Silently ignored during namespace creation
- `NoSuchTableError`: Triggers table creation with specified schema
- `InvalidToken`: Not directly handled (propagated from Fernet operations)
- Type conversion errors: Caught by PyIceberg and reported with table context

## See Also

- [Medallion Architecture](medallion-architecture.md) — Bronze→Silver→Gold flow
- [Iceberg Schemas](../reference/iceberg-schemas.md) — schema definitions
- [Ingestion Pipeline](../architecture/ingestion-pipeline.md) — data flow
- [Dagster Orchestration](../architecture/dagster-orchestration.md) — pipeline orchestration
