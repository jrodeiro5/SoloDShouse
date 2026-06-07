from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd

from ingestion.bronze_writer import BronzeWriter


def _make_catalog_mock():
    """Return a mock Iceberg catalog that captures append calls."""
    table_mock = MagicMock()
    catalog = MagicMock()
    catalog.load_table.return_value = table_mock
    catalog.table_exists = MagicMock(return_value=True)
    return catalog, table_mock


class TestBronzeWriter:
    def test_write_returns_iceberg_path_for_carbon_intensity(self) -> None:
        catalog, _table = _make_catalog_mock()
        writer = BronzeWriter(catalog, bucket="solodshouse-data")
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})

        with patch("ingestion.iceberg_io.append_table") as mock_append:
            path = writer.write(df, source="carbon_intensity")

        assert path == "iceberg:bronze.carbon_intensity"
        mock_append.assert_called_once()

    def test_write_returns_iceberg_path_for_mlperf_benchmarks(self) -> None:
        catalog, _ = _make_catalog_mock()
        writer = BronzeWriter(catalog)
        df = pd.DataFrame({"a": [1]})

        with patch("ingestion.iceberg_io.append_table") as mock_append:
            path = writer.write(df, source="mlperf_benchmarks")

        assert path == "iceberg:bronze.mlperf_benchmarks"
        mock_append.assert_called_once()

    def test_write_rejected_returns_iceberg_path(self) -> None:
        catalog, _ = _make_catalog_mock()
        writer = BronzeWriter(catalog)
        records = [{"bad": "record", "rejection_reason": "invalid schema"}]

        with patch("ingestion.iceberg_io.append_table") as mock_append:
            path = writer.write_rejected(records, source="ECB")

        assert path is not None
        assert "iceberg:bronze.rejected_records" in path
        mock_append.assert_called_once()

    def test_write_rejected_returns_none_for_empty_input(self) -> None:
        catalog, _ = _make_catalog_mock()
        writer = BronzeWriter(catalog)

        with patch("ingestion.iceberg_io.append_table") as mock_append:
            path = writer.write_rejected([], source="DAX")

        assert path is None
        mock_append.assert_not_called()

    def test_write_rejected_raises_for_missing_rejection_reason(self) -> None:
        catalog, _ = _make_catalog_mock()
        writer = BronzeWriter(catalog)

        import pytest
        with pytest.raises(ValueError, match="rejection_reason"):
            writer.write_rejected([{"data": "x"}], source="ECB")
