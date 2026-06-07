from __future__ import annotations

import datetime as dt
from unittest.mock import MagicMock, patch

import pytest
import requests

from ingestion.collectors.cloud_pricing_collector import CloudPricingCollector
from ingestion.exceptions import CollectorUnavailableError
from ingestion.schema.pricing_records import CloudPricingRecord, FXRecord


# ── schema unit tests ─────────────────────────────────────────────────────────


class TestCloudPricingRecord:
    def test_valid_record(self) -> None:
        r = CloudPricingRecord(
            provider="azure",
            instance_type="Standard_NC24ads_A100_v4",
            region="westeurope",
            price_usd_per_hour=3.672,
            sku_name="NC24ads A100 v4",
            captured_at=dt.datetime(2026, 6, 7, 12, 0, tzinfo=dt.timezone.utc),
        )
        assert r.provider == "azure"

    def test_rejects_zero_price(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            CloudPricingRecord(
                provider="azure",
                instance_type="Standard_NC24ads_A100_v4",
                region="westeurope",
                price_usd_per_hour=0.0,
                sku_name="NC24ads A100 v4",
                captured_at=dt.datetime.now(dt.timezone.utc),
            )


class TestFXRecord:
    def test_valid_record(self) -> None:
        r = FXRecord(observation_date=dt.date(2026, 6, 7), eur_usd=1.085)
        assert r.eur_usd == 1.085

    def test_rejects_zero_rate(self) -> None:
        with pytest.raises(ValueError, match="positive"):
            FXRecord(observation_date=dt.date(2026, 6, 7), eur_usd=0.0)


# ── collector validation tests ────────────────────────────────────────────────


def _make_catalog() -> MagicMock:
    catalog = MagicMock()
    catalog.load_table.return_value = MagicMock()
    return catalog


_AZURE_ROW = {
    "armSkuName": "Standard_NC24ads_A100_v4",
    "armRegionName": "westeurope",
    "retailPrice": 3.672,
    "skuName": "NC24ads A100 v4",
}

_FX_ROW = {"date": "2026-06-07", "value": "1.0854"}
_FX_ROW_MISSING = {"date": "2026-06-08", "value": "."}  # weekend/holiday


class TestAzureValidation:
    def test_valid_row_accepted(self) -> None:
        collector = CloudPricingCollector(_make_catalog())
        valid, rejected = collector._validate_azure_records([_AZURE_ROW])
        assert len(valid) == 1
        assert valid[0]["provider"] == "azure"
        assert valid[0]["_source"] == "azure_retail_prices"

    def test_zero_price_rejected(self) -> None:
        bad = {**_AZURE_ROW, "retailPrice": 0.0}
        collector = CloudPricingCollector(_make_catalog())
        valid, rejected = collector._validate_azure_records([bad])
        assert len(valid) == 0
        assert len(rejected) == 1

    def test_missing_sku_uses_arm_name(self) -> None:
        row = {k: v for k, v in _AZURE_ROW.items() if k != "skuName"}
        collector = CloudPricingCollector(_make_catalog())
        valid, _ = collector._validate_azure_records([row])
        assert valid[0]["sku_name"] == "Standard_NC24ads_A100_v4"

    def test_ingestion_metadata_added(self) -> None:
        collector = CloudPricingCollector(_make_catalog())
        valid, _ = collector._validate_azure_records([_AZURE_ROW])
        assert "_ingestion_timestamp" in valid[0]


class TestFXValidation:
    def test_valid_row_accepted(self) -> None:
        collector = CloudPricingCollector(_make_catalog())
        valid, rejected = collector._validate_fx_records([_FX_ROW])
        assert len(valid) == 1
        assert valid[0]["eur_usd"] == pytest.approx(1.0854)

    def test_dot_value_skipped_not_rejected(self) -> None:
        collector = CloudPricingCollector(_make_catalog())
        valid, rejected = collector._validate_fx_records([_FX_ROW_MISSING])
        assert len(valid) == 0
        assert len(rejected) == 0  # FRED dot = holiday, not an error


class TestCollectFREDKeyMissing:
    def test_fx_skipped_gracefully_without_api_key(self, monkeypatch) -> None:
        monkeypatch.delenv("FRED_API_KEY", raising=False)
        collector = CloudPricingCollector(_make_catalog())

        with patch.object(collector, "_fetch_azure_gpu_prices", return_value=[_AZURE_ROW]), \
             patch("ingestion.iceberg_io.append_table"):
            result = collector.collect()

        assert result.get("fx_skipped") is True
        assert "azure_valid" in result

    def test_azure_fetch_raises_on_network_error(self) -> None:
        collector = CloudPricingCollector(_make_catalog())
        with patch("ingestion.collectors.cloud_pricing_collector.make_session") as mock_session:
            mock_session.return_value.get.side_effect = requests.ConnectionError("refused")
            with pytest.raises(CollectorUnavailableError, match="Azure Prices API failed"):
                collector._fetch_azure_gpu_prices()
