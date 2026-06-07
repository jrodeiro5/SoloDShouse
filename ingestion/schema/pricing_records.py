"""Pydantic v2 schemas for cloud GPU pricing and FX rate records."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, field_validator


class CloudPricingRecord(BaseModel):
    provider: str
    instance_type: str
    region: str
    price_usd_per_hour: float
    sku_name: str
    captured_at: dt.datetime

    @field_validator("price_usd_per_hour")
    @classmethod
    def positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("price_usd_per_hour must be positive")
        return v


class FXRecord(BaseModel):
    observation_date: dt.date
    eur_usd: float

    @field_validator("eur_usd")
    @classmethod
    def positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("eur_usd must be positive")
        return v
