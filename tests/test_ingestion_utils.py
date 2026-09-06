from unittest.mock import MagicMock, patch

import pandas as pd
import pyarrow as pa

from ingestion.exceptions import CollectorUnavailableError, StepError
from ingestion.http import make_session
from ingestion.iceberg_io import (
    _downcast_ns_timestamps,
    append_table,
    ensure_namespace,
    get_catalog,
    overwrite_table,
    scan_table,
)


def test_exceptions():
    err = CollectorUnavailableError("source down")
    assert str(err) == "source down"

    orig = ValueError("something went wrong")
    step_err = StepError(1, "test_step", orig)
    assert step_err.step_number == 1
    assert step_err.step_name == "test_step"
    assert step_err.original is orig
    assert "Step 1 (test_step) failed: something went wrong" in str(step_err)


def test_make_session():
    session = make_session(total=2, backoff_factor=0.1)
    assert session is not None
    assert "https://" in session.adapters
    assert "http://" in session.adapters


def test_downcast_ns_timestamps():
    # Table with ns timestamp and non-timestamp
    schema_ns = pa.schema([
        ("ts", pa.timestamp("ns", tz="UTC")),
        ("val", pa.int64()),
    ])
    df = pd.DataFrame({
        "ts": [pd.Timestamp("2026-01-01 00:00:00", tz="UTC")],
        "val": [10],
    })
    arrow_table = pa.Table.from_pandas(df, schema=schema_ns)
    downcasted = _downcast_ns_timestamps(arrow_table)
    assert downcasted.schema.field("ts").type.unit == "us"

    # Table already in us timestamp
    schema_us = pa.schema([
        ("ts", pa.timestamp("us", tz="UTC")),
        ("val", pa.int64()),
    ])
    arrow_table_us = pa.Table.from_pandas(df, schema=schema_us)
    same_table = _downcast_ns_timestamps(arrow_table_us)
    assert same_table.schema.field("ts").type.unit == "us"


@patch.dict("os.environ", {
    "OBJECT_STORE_ENDPOINT": "http://minio:9000",
    "HIVE_METASTORE_URI": "thrift://metastore:9083",
    "S3_ACCESS_KEY": "test_key",
    "S3_SECRET_KEY": "test_secret",
})
@patch("pyiceberg.catalog.hive.HiveCatalog")
def test_get_catalog(mock_hive_catalog):
    get_catalog(name="test_cat")
    mock_hive_catalog.assert_called_once()
    args, kwargs = mock_hive_catalog.call_args
    assert args[0] == "test_cat"
    assert kwargs["uri"] == "thrift://metastore:9083"
    assert kwargs["s3.endpoint"] == "http://minio:9000"
    assert kwargs["s3.access-key-id"] == "test_key"
    assert kwargs["s3.secret-access-key"] == "test_secret"


def test_ensure_namespace_and_io_helpers():
    from pyiceberg.exceptions import NamespaceAlreadyExistsError, NoSuchTableError

    mock_catalog = MagicMock()
    # ensure_namespace handles NamespaceAlreadyExistsError
    mock_catalog.create_namespace.side_effect = NamespaceAlreadyExistsError("already exists")
    ensure_namespace(mock_catalog, "test_ns")
    mock_catalog.create_namespace.assert_called_once_with("test_ns")

    # test append_table when table does not exist
    mock_catalog_table = MagicMock()
    mock_catalog.load_table.side_effect = [NoSuchTableError("no table"), mock_catalog_table]
    mock_catalog.create_table.return_value = mock_catalog_table

    mock_schema = MagicMock()
    df = pd.DataFrame({"a": [1, 2]})

    append_table(mock_catalog, "ns", "tbl", df, mock_schema)
    mock_catalog.create_table.assert_called_once()
    mock_catalog_table.append.assert_called_once()

    # test overwrite_table when table exists
    mock_catalog.reset_mock()
    mock_catalog.load_table.side_effect = None
    mock_catalog.load_table.return_value = mock_catalog_table

    overwrite_table(mock_catalog, "ns", "tbl", df, mock_schema)
    mock_catalog_table.overwrite.assert_called_once()

    # test scan_table
    scan_table(mock_catalog, "ns", "tbl")
    mock_catalog.load_table.assert_called_with(("ns", "tbl"))
