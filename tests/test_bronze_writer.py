from __future__ import annotations

import json
import tempfile

import pandas as pd
import pytest
from pyiceberg.catalog import load_in_memory

from ingestion.bronze_writer import BronzeWriter
from ingestion.iceberg_io import scan_table


@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield tmp_dir


@pytest.fixture
def catalog(temp_dir):
    return load_in_memory("test_catalog", {"warehouse": f"file://{temp_dir}"})


class TestBronzeWriter:
    def test_write_returns_iceberg_path_for_carbon_intensity(self, catalog) -> None:
        writer = BronzeWriter(catalog, bucket="solodshouse-data")
        now = pd.Timestamp.now(tz="UTC")
        df = pd.DataFrame({
            "timestamp_utc": [now, now],
            "country": ["ES", "FR"],
            "carbon_intensity_gco2_kwh": [150.0, 80.0],
            "_ingestion_timestamp": [now, now],
            "_source": ["Electricity Maps", "Electricity Maps"]
        })

        path = writer.write(df, source="carbon_intensity")

        assert path == "iceberg:bronze.carbon_intensity"
        
        scanned_df = scan_table(catalog, "bronze", "carbon_intensity")
        assert len(scanned_df) == 2
        assert list(scanned_df["country"]) == ["ES", "FR"]
        assert list(scanned_df["carbon_intensity_gco2_kwh"]) == [150.0, 80.0]
        assert isinstance(scanned_df["timestamp_utc"].dtype, pd.DatetimeTZDtype)
        assert pd.api.types.is_numeric_dtype(scanned_df["carbon_intensity_gco2_kwh"])

    def test_write_returns_iceberg_path_for_mlperf_benchmarks(self, catalog) -> None:
        writer = BronzeWriter(catalog)
        now = pd.Timestamp.now(tz="UTC")
        df = pd.DataFrame({
            "round_id": ["v4.0"],
            "model_name": ["llama3-70b"],
            "accelerator": ["H100"],
            "submitter": ["NVIDIA"],
            "scenario": ["Offline"],
            "tokens_per_sec": [1234.5],
            "_ingestion_timestamp": [now],
            "_source": ["MLCommons"]
        })

        path = writer.write(df, source="mlperf_benchmarks")

        assert path == "iceberg:bronze.mlperf_benchmarks"

        scanned_df = scan_table(catalog, "bronze", "mlperf_benchmarks")
        assert len(scanned_df) == 1
        assert scanned_df.loc[0, "model_name"] == "llama3-70b"
        assert scanned_df.loc[0, "tokens_per_sec"] == 1234.5
        assert isinstance(scanned_df["_ingestion_timestamp"].dtype, pd.DatetimeTZDtype)

    def test_write_rejected_returns_iceberg_path(self, catalog) -> None:
        writer = BronzeWriter(catalog)
        records = [{"bad": "record", "rejection_reason": "invalid schema"}]

        path = writer.write_rejected(records, source="ECB")

        assert path is not None
        assert "iceberg:bronze.rejected_records" in path

        scanned_df = scan_table(catalog, "bronze", "rejected_records")
        assert len(scanned_df) == 1
        assert scanned_df.loc[0, "source"] == "ECB"
        assert scanned_df.loc[0, "rejection_reason"] == "invalid schema"
        
        payload = json.loads(scanned_df.loc[0, "payload"])
        assert payload == {"bad": "record"}
        assert isinstance(scanned_df["_ingested_at"].dtype, pd.DatetimeTZDtype)

    def test_write_rejected_returns_none_for_empty_input(self, catalog) -> None:
        writer = BronzeWriter(catalog)

        path = writer.write_rejected([], source="DAX")

        assert path is None
        from pyiceberg.exceptions import NoSuchTableError
        with pytest.raises(NoSuchTableError):
            scan_table(catalog, "bronze", "rejected_records")

    def test_write_rejected_raises_for_missing_rejection_reason(self, catalog) -> None:
        writer = BronzeWriter(catalog)

        with pytest.raises(ValueError, match="rejection_reason"):
            writer.write_rejected([{"data": "x"}], source="ECB")
