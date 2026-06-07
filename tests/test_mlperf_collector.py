from __future__ import annotations

from unittest.mock import MagicMock, patch

import pandas as pd
import pytest
import requests

from ingestion.collectors.mlperf_collector import MLPerfCollector
from ingestion.exceptions import CollectorUnavailableError
from ingestion.schema.mlperf_records import MLPerfRecord


# ── schema unit tests ─────────────────────────────────────────────────────────


class TestMLPerfRecord:
    def test_valid_record(self) -> None:
        r = MLPerfRecord(
            round_id="v4.1",
            model_name="llama2-70b",
            accelerator="NVIDIA H100",
            submitter="NVIDIA",
            scenario="Offline",
            tokens_per_sec=1500.0,
        )
        assert r.tokens_per_sec == 1500.0

    def test_rejects_zero_tokens_per_sec(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            MLPerfRecord(round_id="v4.1", model_name="llama2-70b", accelerator="H100", tokens_per_sec=0.0)

    def test_rejects_negative_tokens_per_sec(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            MLPerfRecord(round_id="v4.1", model_name="llama2-70b", accelerator="H100", tokens_per_sec=-1.0)

    def test_rejects_empty_model_name(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            MLPerfRecord(round_id="v4.1", model_name="  ", accelerator="H100", tokens_per_sec=100.0)

    def test_rejects_empty_accelerator(self) -> None:
        with pytest.raises(ValueError, match="empty"):
            MLPerfRecord(round_id="v4.1", model_name="llama2-70b", accelerator="", tokens_per_sec=100.0)

    def test_optional_fields_default_none(self) -> None:
        r = MLPerfRecord(round_id="v4.1", model_name="llama2-70b", accelerator="H100", tokens_per_sec=100.0)
        assert r.submitter is None
        assert r.scenario is None


# ── collector validation tests ────────────────────────────────────────────────


def _make_catalog() -> MagicMock:
    catalog = MagicMock()
    catalog.load_table.return_value = MagicMock()
    return catalog


_LLM_ROW = {
    "round_id": "v4.1",
    "model_name": "llama2-70b",
    "accelerator": "NVIDIA H100 SXM5 80GB",
    "submitter": "NVIDIA",
    "scenario": "Offline",
    "tokens_per_sec": 1500.0,
}

_NON_LLM_ROW = {
    "round_id": "v4.1",
    "model_name": "resnet50",
    "accelerator": "NVIDIA H100",
    "submitter": "NVIDIA",
    "scenario": "Offline",
    "tokens_per_sec": 9000.0,
}


class TestMLPerfCollectorValidation:
    def test_valid_llm_row_accepted(self) -> None:
        collector = MLPerfCollector(_make_catalog())
        df = pd.DataFrame([_LLM_ROW])
        valid, rejected = collector._validate_records(df, "v4.1")
        assert len(valid) == 1
        assert len(rejected) == 0
        assert valid[0]["model_name"] == "llama2-70b"

    def test_non_llm_model_filtered_out(self) -> None:
        collector = MLPerfCollector(_make_catalog())
        df = pd.DataFrame([_NON_LLM_ROW])
        valid, rejected = collector._validate_records(df, "v4.1")
        assert len(valid) == 0
        assert len(rejected) == 0  # filtered, not rejected

    def test_negative_tokens_per_sec_rejected(self) -> None:
        bad_row = {**_LLM_ROW, "tokens_per_sec": -1.0}
        collector = MLPerfCollector(_make_catalog())
        df = pd.DataFrame([bad_row])
        valid, rejected = collector._validate_records(df, "v4.1")
        assert len(valid) == 0
        assert len(rejected) == 1
        assert "rejection_reason" in rejected[0]

    def test_ingestion_metadata_added(self) -> None:
        collector = MLPerfCollector(_make_catalog())
        df = pd.DataFrame([_LLM_ROW])
        valid, _ = collector._validate_records(df, "v4.1")
        assert "_ingestion_timestamp" in valid[0]
        assert valid[0]["_source"] == "mlcommons_mlperf"

    def test_round_id_injected_when_missing_from_csv(self) -> None:
        row_no_round = {k: v for k, v in _LLM_ROW.items() if k != "round_id"}
        collector = MLPerfCollector(_make_catalog())
        df = pd.DataFrame([row_no_round])
        valid, _ = collector._validate_records(df, "v4.1")
        assert valid[0]["round_id"] == "v4.1"


class TestMLPerfCollectorFetch:
    def test_fetch_raises_collector_unavailable_on_network_error(self) -> None:
        collector = MLPerfCollector(_make_catalog())
        with patch("ingestion.collectors.mlperf_collector.make_session") as mock_session:
            mock_session.return_value.get.side_effect = requests.ConnectionError("refused")
            with pytest.raises(CollectorUnavailableError, match="MLPerf CSV fetch failed"):
                collector._fetch_data("https://example.com/results.csv")

    def test_fetch_raises_on_non_200(self) -> None:
        collector = MLPerfCollector(_make_catalog())
        with patch("ingestion.collectors.mlperf_collector.make_session") as mock_session:
            mock_resp = MagicMock()
            mock_resp.raise_for_status.side_effect = requests.HTTPError("404")
            mock_session.return_value.get.return_value = mock_resp
            with pytest.raises(CollectorUnavailableError):
                collector._fetch_data("https://example.com/missing.csv")


class TestMLPerfCollectorCollect:
    def test_collect_writes_valid_rows_to_bronze(self) -> None:
        collector = MLPerfCollector(_make_catalog())
        df = pd.DataFrame([_LLM_ROW])

        with patch.object(collector, "_fetch_data", return_value=df), \
             patch("ingestion.iceberg_io.append_table") as mock_append:
            result = collector.collect(round_id="v4.1")

        assert result["valid"] == 1
        assert result["rejected"] == 0
        mock_append.assert_called_once()

    def test_collect_skips_bronze_write_when_no_valid_rows(self) -> None:
        collector = MLPerfCollector(_make_catalog())
        df = pd.DataFrame([_NON_LLM_ROW])  # filtered, not LLM

        with patch.object(collector, "_fetch_data", return_value=df), \
             patch("ingestion.iceberg_io.append_table") as mock_append:
            result = collector.collect(round_id="v4.1")

        assert result["valid"] == 0
        mock_append.assert_not_called()
