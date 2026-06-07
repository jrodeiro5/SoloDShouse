"""Pydantic v2 schema for MLCommons MLPerf inference benchmark records."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class MLPerfRecord(BaseModel):
    round_id: str
    model_name: str
    accelerator: str
    submitter: str | None = None
    scenario: str | None = None
    tokens_per_sec: float

    @field_validator("model_name", "accelerator")
    @classmethod
    def non_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("must not be empty")
        return v

    @field_validator("tokens_per_sec")
    @classmethod
    def positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("tokens_per_sec must be positive")
        return v
