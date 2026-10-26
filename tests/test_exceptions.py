"""Tests for ingestion.exceptions — custom pipeline exception types."""

from __future__ import annotations

from ingestion.exceptions import CollectorUnavailableError, StepError


def test_collector_unavailable_error_is_an_exception() -> None:
    err = CollectorUnavailableError("host unreachable after retries")
    assert isinstance(err, Exception)
    assert str(err) == "host unreachable after retries"


def test_step_error_keeps_original_and_formats_message() -> None:
    original = ValueError("boom")
    err = StepError(3, "transform", original)
    assert err.step_number == 3
    assert err.step_name == "transform"
    assert err.original is original
    assert isinstance(err, Exception)
    assert str(err) == "Step 3 (transform) failed: boom"
