"""Tests for the shared ingestion exception types and the HTTP session factory."""

from __future__ import annotations

import pytest
from requests.adapters import HTTPAdapter

from ingestion.exceptions import CollectorUnavailableError, StepError
from ingestion.http import make_session


def test_collector_unavailable_error_is_raised_and_formatted() -> None:
    with pytest.raises(CollectorUnavailableError, match="source unreachable"):
        raise CollectorUnavailableError("source unreachable")


def test_step_error_wraps_original_exception() -> None:
    original = RuntimeError("connection refused")

    err = StepError(3, "bronze_write", original)

    assert err.step_number == 3
    assert err.step_name == "bronze_write"
    assert err.original is original
    assert str(err) == "Step 3 (bronze_write) failed: connection refused"


def test_make_session_mounts_retrying_adapters() -> None:
    session = make_session(total=4, backoff_factor=0.25)

    https_adapter = session.get_adapter("https://example.com")
    http_adapter = session.get_adapter("http://example.com")
    assert isinstance(https_adapter, HTTPAdapter)
    assert isinstance(http_adapter, HTTPAdapter)

    retry = https_adapter.max_retries
    assert retry.total == 4
    assert retry.backoff_factor == 0.25
    assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
    assert set(retry.allowed_methods) == {"GET"}
