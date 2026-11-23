"""Tests for the shared HTTP session factory (ingestion.http)."""

from __future__ import annotations

from ingestion.http import make_session


def test_make_session_retries_transient_server_errors() -> None:
    session = make_session()
    try:
        for prefix in ("https://", "http://"):
            assert prefix in session.adapters
            retry = session.adapters[prefix].max_retries
            assert retry.total == 3
            assert retry.backoff_factor == 0.5
            assert retry.raise_on_status is False
            assert set(retry.status_forcelist) == {429, 500, 502, 503, 504}
            assert set(retry.allowed_methods) == {"GET"}
    finally:
        session.close()


def test_make_session_honours_custom_retry_settings() -> None:
    session = make_session(total=5, backoff_factor=1.0)
    try:
        retry = session.get_adapter("https://example.com").max_retries
        assert retry.total == 5
        assert retry.backoff_factor == 1.0
    finally:
        session.close()
