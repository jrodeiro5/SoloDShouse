"""Pydantic v2 schema for ENTSO-E Transparency Platform generation records."""

from __future__ import annotations

import datetime as dt

from pydantic import BaseModel, field_validator


class ENTSOEGenerationRecord(BaseModel):
    timestamp_utc: dt.datetime
    country: str
    psr_type: str
    psr_type_name: str
    quantity_mw: float
    resolution: str

    @field_validator("country")
    @classmethod
    def valid_country(cls, v: str) -> str:
        if len(v) != 2:
            raise ValueError(f"country must be ISO-2 code, got: {v!r}")
        return v.upper()

    @field_validator("quantity_mw")
    @classmethod
    def non_negative(cls, v: float) -> float:
        if v < 0:
            raise ValueError(f"quantity_mw cannot be negative, got: {v}")
        return v

    @field_validator("resolution")
    @classmethod
    def valid_resolution(cls, v: str) -> str:
        if v not in {"PT15M", "PT60M"}:
            raise ValueError(f"resolution must be PT15M or PT60M, got: {v!r}")
        return v
