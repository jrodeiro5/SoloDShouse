"""CloudPricingCollector — ingests Azure GPU instance pricing and EUR/USD FX rates.

Sources:
  - Azure Retail Prices API (no auth required)
  - FRED API for DEXUSEU series (requires FRED_API_KEY env var; free registration)

Writes two Bronze tables: cloud_gpu_pricing, fx_rates.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import TYPE_CHECKING

import pandas as pd
import requests
import structlog

from ingestion.bronze_writer import BronzeWriter
from ingestion.exceptions import CollectorUnavailableError
from ingestion.schema.pricing_records import CloudPricingRecord, FXRecord

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

logger = structlog.get_logger()

_AZURE_PRICES_URL = "https://prices.azure.com/api/retail/prices"
_FRED_URL = "https://api.stlouisfed.org/fred/series/observations"

# Azure VM families that contain GPU accelerators relevant to AI inference.
_GPU_SKU_KEYWORDS = ("NC", "ND", "NV", "NG", "Standard_N")


class CloudPricingCollector:
    def __init__(self, catalog: "Catalog"):
        self.catalog = catalog
        self.bronze_writer = BronzeWriter(catalog)

    # ── Azure ─────────────────────────────────────────────────────────────────

    def _fetch_azure_gpu_prices(self, region: str = "westeurope") -> list[dict]:
        """Fetch GPU VM pricing from Azure Retail Prices API (paginated)."""
        filter_expr = (
            f"serviceName eq 'Virtual Machines' and armRegionName eq '{region}' "
            f"and priceType eq 'Consumption'"
        )
        params: dict = {"$filter": filter_expr, "api-version": "2023-01-01-preview"}
        rows: list[dict] = []

        url: str | None = _AZURE_PRICES_URL
        while url:
            try:
                resp = requests.get(url, params=params, timeout=30)
                resp.raise_for_status()
            except requests.RequestException as exc:
                raise CollectorUnavailableError(f"Azure Prices API failed: {exc}") from exc

            data = resp.json()
            rows.extend(data.get("Items", []))
            url = data.get("NextPageLink")
            params = {}  # NextPageLink already encodes params

        # Filter to GPU SKUs only
        return [r for r in rows if any(kw in r.get("armSkuName", "") for kw in _GPU_SKU_KEYWORDS)]

    def _validate_azure_records(self, raw: list[dict]) -> tuple[list[dict], list[dict]]:
        now = dt.datetime.now(dt.UTC)
        valid, rejected = [], []
        for row in raw:
            try:
                record = CloudPricingRecord(
                    provider="azure",
                    instance_type=row["armSkuName"],
                    region=row["armRegionName"],
                    price_usd_per_hour=float(row["retailPrice"]),
                    sku_name=row.get("skuName", row["armSkuName"]),
                    captured_at=now,
                )
                d = record.model_dump()
                d["_ingestion_timestamp"] = now
                d["_source"] = "azure_retail_prices"
                valid.append(d)
            except (ValueError, KeyError, TypeError) as exc:
                rejected.append({**row, "rejection_reason": str(exc)})
        return valid, rejected

    # ── FRED FX ───────────────────────────────────────────────────────────────

    def _fetch_fx_rates(self, observation_start: str = "2024-01-01") -> list[dict]:
        """Fetch EUR/USD daily rates from FRED (series DEXUSEU)."""
        api_key = os.environ.get("FRED_API_KEY", "")
        if not api_key:
            raise CollectorUnavailableError(
                "FRED_API_KEY env var not set — register free at https://fred.stlouisfed.org/docs/api/api_key.html"
            )
        params = {
            "series_id": "DEXUSEU",
            "api_key": api_key,
            "file_type": "json",
            "observation_start": observation_start,
            "sort_order": "desc",
            "limit": 365,
        }
        try:
            resp = requests.get(_FRED_URL, params=params, timeout=30)
            resp.raise_for_status()
        except requests.RequestException as exc:
            raise CollectorUnavailableError(f"FRED API failed: {exc}") from exc
        return resp.json().get("observations", [])

    def _validate_fx_records(self, raw: list[dict]) -> tuple[list[dict], list[dict]]:
        now = dt.datetime.now(dt.UTC)
        valid, rejected = [], []
        for row in raw:
            try:
                if row.get("value") == ".":
                    # FRED uses "." for missing observations (weekends/holidays)
                    continue
                record = FXRecord(
                    observation_date=dt.date.fromisoformat(row["date"]),
                    eur_usd=float(row["value"]),
                )
                d = record.model_dump()
                d["_ingestion_timestamp"] = now
                d["_source"] = "fred_dexuseu"
                valid.append(d)
            except (ValueError, KeyError, TypeError) as exc:
                rejected.append({**row, "rejection_reason": str(exc)})
        return valid, rejected

    # ── collect ───────────────────────────────────────────────────────────────

    def collect(
        self,
        azure_region: str = "westeurope",
        fx_start: str = "2024-01-01",
    ) -> dict:
        logger.info("cloud_pricing_collect_start", azure_region=azure_region)
        summary: dict = {}

        # Azure GPU pricing
        raw_azure = self._fetch_azure_gpu_prices(azure_region)
        valid_azure, rejected_azure = self._validate_azure_records(raw_azure)
        if valid_azure:
            self.bronze_writer.write(pd.DataFrame(valid_azure), source="cloud_gpu_pricing")
        if rejected_azure:
            self.bronze_writer.write_rejected(rejected_azure, source="cloud_gpu_pricing")
        summary["azure_valid"] = len(valid_azure)
        summary["azure_rejected"] = len(rejected_azure)

        # FRED FX rates
        try:
            raw_fx = self._fetch_fx_rates(fx_start)
            valid_fx, rejected_fx = self._validate_fx_records(raw_fx)
            if valid_fx:
                self.bronze_writer.write(pd.DataFrame(valid_fx), source="fx_rates")
            if rejected_fx:
                self.bronze_writer.write_rejected(rejected_fx, source="fx_rates")
            summary["fx_valid"] = len(valid_fx)
            summary["fx_rejected"] = len(rejected_fx)
        except CollectorUnavailableError as exc:
            logger.warning("fx_rates_skipped", reason=str(exc))
            summary["fx_skipped"] = True

        logger.info("cloud_pricing_collect_done", **summary)
        return summary
