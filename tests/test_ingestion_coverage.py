"""Tests for boosting coverage across ingestion package modules."""

from __future__ import annotations

import io
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pandas as pd
import pyarrow as pa
import pytest

from connections.vault import generate_key
from ingestion.exceptions import CollectorUnavailableError, StepError
from ingestion.http import make_session
from ingestion.iceberg_io import (
    _downcast_ns_timestamps,
    _get_or_create_table,
    append_table,
    ensure_namespace,
    get_catalog,
    overwrite_table,
    scan_table,
)
from ingestion.iceberg_schemas import (
    BRONZE_CARBON_INTENSITY_PARTITION,
    BRONZE_CARBON_INTENSITY_SCHEMA,
    load_schema_config,
    schema_from_config,
)


def test_exceptions() -> None:
    err = CollectorUnavailableError("Source down")
    assert str(err) == "Source down"

    orig = ValueError("bad value")
    step_err = StepError(step_number=1, step_name="extract", original=orig)
    assert step_err.step_number == 1
    assert step_err.step_name == "extract"
    assert step_err.original is orig
    assert "Step 1 (extract) failed: bad value" in str(step_err)


def test_make_session() -> None:
    session = make_session(total=2, backoff_factor=0.1)
    assert session is not None
    assert session.adapters["https://"] is not None
    assert session.adapters["http://"] is not None


class TestIcebergSchemasCoverage:
    def test_schema_from_config_valid(self) -> None:
        cfg = {
            "source": "test_src",
            "columns": [
                {"name": "col1", "type": "string"},
                {"name": "col2", "type": "double"},
                {"name": "ts", "type": "timestamptz"},
            ],
            "partition": {
                "field": "ts",
                "transform": "day",
            },
        }
        schema, spec = schema_from_config(cfg)
        assert len(schema.fields) == 3
        assert len(spec.fields) == 1

    def test_schema_from_config_invalid_type(self) -> None:
        cfg = {
            "source": "test_src",
            "columns": [{"name": "col1", "type": "unknown_type"}],
        }
        with pytest.raises(ValueError, match="Unknown type 'unknown_type'"):
            schema_from_config(cfg)

    def test_schema_from_config_invalid_transform(self) -> None:
        cfg = {
            "source": "test_src",
            "columns": [{"name": "col1", "type": "string"}],
            "partition": {"field": "col1", "transform": "bad_transform"},
        }
        with pytest.raises(ValueError, match="Unknown partition transform"):
            schema_from_config(cfg)

    def test_schema_from_config_missing_partition_field(self) -> None:
        cfg = {
            "source": "test_src",
            "columns": [{"name": "col1", "type": "string"}],
            "partition": {"field": "missing_col", "transform": "day"},
        }
        with pytest.raises(ValueError, match="Partition field 'missing_col' not found"):
            schema_from_config(cfg)

    def test_load_schema_config_not_found(self) -> None:
        with pytest.raises(FileNotFoundError):
            load_schema_config("non_existent_schema_xyz_123")


class TestIcebergIOCoverage:
    def test_downcast_ns_timestamps(self) -> None:
        dt_s = pd.date_range("2026-01-01", periods=2, freq="h")
        df = pd.DataFrame({"ts": dt_s, "val": [1, 2]})
        table = pa.Table.from_pandas(df)
        # Force ns unit
        field_idx = table.schema.get_field_index("ts")
        ns_field = pa.field("ts", pa.timestamp("ns"))
        table = table.set_column(field_idx, ns_field, table.column("ts").cast(pa.timestamp("ns")))

        casted = _downcast_ns_timestamps(table)
        assert casted.schema.field("ts").type.unit == "us"

        # If already non-timestamp / us timestamp, return same
        no_ns_table = _downcast_ns_timestamps(casted)
        assert no_ns_table is casted

    def test_ensure_namespace_handles_existing(self) -> None:
        from pyiceberg.exceptions import NamespaceAlreadyExistsError

        mock_cat = MagicMock()
        mock_cat.create_namespace.side_effect = NamespaceAlreadyExistsError("exists")
        ensure_namespace(mock_cat, "bronze")  # Should not raise

    def test_get_or_create_table(self) -> None:
        from pyiceberg.exceptions import NoSuchTableError

        mock_cat = MagicMock()
        mock_table = MagicMock()
        mock_cat.load_table.side_effect = [NoSuchTableError("no table"), mock_table]
        mock_cat.create_table.return_value = mock_table

        tbl = _get_or_create_table(
            mock_cat,
            "bronze",
            "test_tbl",
            BRONZE_CARBON_INTENSITY_SCHEMA,
            BRONZE_CARBON_INTENSITY_PARTITION,
        )
        assert tbl == mock_table
        mock_cat.create_table.assert_called_once()

    def test_append_and_overwrite_and_scan(self) -> None:
        mock_cat = MagicMock()
        mock_tbl = MagicMock()
        mock_cat.load_table.return_value = mock_tbl
        df = pd.DataFrame({"x": [1, 2]})

        append_table(mock_cat, "bronze", "test", df, BRONZE_CARBON_INTENSITY_SCHEMA)
        mock_tbl.append.assert_called_once()

        overwrite_table(mock_cat, "silver", "test", df, BRONZE_CARBON_INTENSITY_SCHEMA)
        mock_tbl.overwrite.assert_called_once()

        mock_tbl.scan.return_value.to_pandas.return_value = df
        res_df = scan_table(mock_cat, "silver", "test")
        assert len(res_df) == 2

    @patch("pyiceberg.catalog.hive.HiveCatalog.__init__", return_value=None)
    def test_get_catalog(self, mock_hive_init: MagicMock) -> None:
        get_catalog()
        mock_hive_init.assert_called_once()


class TestDynamicCollectorFetchCoverage:
    def test_fetch_rest_dict_key_mapping(self) -> None:
        from connections.manager import RestConfig
        from ingestion.collectors.dynamic import _fetch_rest

        config = RestConfig(base_url="https://example.com", endpoint="")
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"data": [{"id": 10}]}
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            res = _fetch_rest(config)
            assert res == [{"id": 10}]

            mock_resp.json.return_value = {"single": "object"}
            res = _fetch_rest(config)
            assert res == [{"single": "object"}]

            mock_resp.json.return_value = "not_a_dict_or_list"
            res = _fetch_rest(config)
            assert res == []

    def test_fetch_s3_parquet_and_csv(self) -> None:
        from connections.manager import S3Config
        from ingestion.collectors.dynamic import _fetch_s3

        cfg = S3Config(
            endpoint="http://localhost:9000",
            bucket="bkt",
            access_key="ak",
            secret_key="sk",
            prefix="pref",
            file_glob="*.parquet",
        )
        df_parquet = pd.DataFrame({"a": [1, 2]})
        buf = io.BytesIO()
        df_parquet.to_parquet(buf)
        buf.seek(0)

        mock_boto = MagicMock()
        mock_boto.list_objects_v2.return_value = {"Contents": [{"Key": "pref/file.parquet"}]}
        mock_boto.get_object.return_value = {"Body": buf}

        with patch("boto3.client", return_value=mock_boto):
            res = _fetch_s3("src", cfg)
            assert len(res) == 2
            assert res[0]["a"] == 1

        mock_boto.list_objects_v2.return_value = {}
        with patch("boto3.client", return_value=mock_boto):
            res = _fetch_s3("src", cfg)
            assert res == []

    def test_fetch_postgres(self) -> None:
        from connections.manager import PostgresConfig
        from ingestion.collectors.dynamic import _fetch_postgres

        cfg = PostgresConfig(
            host="localhost",
            port=5432,
            database="db",
            user="u",
            password="p",
            schema="s",
            table="t",
        )
        mock_conn = MagicMock()
        mock_cur = MagicMock()
        mock_cur.description = [("col1",), ("col2",)]
        mock_cur.fetchall.return_value = [(1, "a"), (2, "b")]
        mock_conn.cursor.return_value = mock_cur

        with patch("psycopg2.connect", return_value=mock_conn):
            res = _fetch_postgres(cfg)
            assert len(res) == 2
            assert res[0]["col1"] == 1

        cfg_no_table = PostgresConfig(
            host="localhost",
            port=5432,
            database="db",
            user="u",
            password="p",
            schema="",
            table="",
        )
        with patch("psycopg2.connect", return_value=mock_conn):
            res = _fetch_postgres(cfg_no_table)
            assert len(res) == 2

    def test_fetch_filesystem(self) -> None:
        from connections.manager import FilesystemConfig
        from ingestion.collectors.dynamic import _fetch_filesystem

        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir)
            p_file = tmp_path / "data.parquet"
            c_file = tmp_path / "data.csv"
            df = pd.DataFrame({"col": [100]})
            df.to_parquet(p_file)
            df.to_csv(c_file, index=False)

            cfg = FilesystemConfig(path=str(tmpdir), file_glob="*")
            res = _fetch_filesystem(cfg)
            assert len(res) == 2

    def test_validate_records_missing_schema_file(self) -> None:
        from ingestion.collectors.dynamic import DynamicCollector

        collector = DynamicCollector(catalog=MagicMock(), source_name="missing_schema_source")
        raw = [{"a": 1, "b": 2}]
        with patch(
            "ingestion.collectors.dynamic.load_schema_config", side_effect=FileNotFoundError
        ):
            valid, rejected = collector._validate_records(raw)
            assert len(valid) == 1
            assert valid[0] == {"a": 1, "b": 2}

    def test_ensure_connection(self, monkeypatch: pytest.MonkeyPatch) -> None:
        from ingestion.collectors.dynamic import DynamicCollector

        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", generate_key())
        collector = DynamicCollector(catalog=MagicMock(), source_name="api_test")
        mock_conn = MagicMock()
        mock_mgr = MagicMock()
        mock_mgr.get_connection.return_value = mock_conn
        with patch("connections.manager.ConnectionManager", return_value=mock_mgr):
            conn = collector._ensure_connection()
            assert conn is mock_conn
            # Cached
            conn2 = collector._ensure_connection()
            assert conn2 is mock_conn
