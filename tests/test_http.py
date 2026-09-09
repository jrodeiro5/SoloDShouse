from __future__ import annotations

import requests

from ingestion.http import make_session


def test_make_session_returns_configured_session():
    session = make_session(total=2, backoff_factor=0.1)
    assert isinstance(session, requests.Session)
    assert "https://" in session.adapters
    assert "http://" in session.adapters
