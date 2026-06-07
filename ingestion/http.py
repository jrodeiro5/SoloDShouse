"""Shared HTTP session factory with retry for all collectors."""

from __future__ import annotations

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry


def make_session(total: int = 3, backoff_factor: float = 0.5) -> requests.Session:
    """Return a requests.Session that retries on transient server errors.

    Retries: 3 attempts, exponential backoff (0.5s, 1s, 2s).
    Retried status codes: 429, 500, 502, 503, 504.
    4xx client errors are NOT retried.
    """
    session = requests.Session()
    retry = Retry(
        total=total,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session
