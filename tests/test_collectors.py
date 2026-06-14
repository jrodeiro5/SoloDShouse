from __future__ import annotations

import importlib
from typing import Any
from unittest.mock import patch

from ingestion.collectors.base import BaseCollector
from ingestion.collectors.registry import register_collector, list_sources, get_collector


@register_collector("dummy_test_source")
class DummyTestCollector(BaseCollector):
    def collect(self) -> dict[str, Any]:
        return {"valid": 1, "rejected": 0}

    def _fetch_data(self) -> Any:
        return []

    def _validate_records(self) -> tuple[list[dict], list[dict]]:
        return [], []


def test_collector_registration() -> None:
    sources = list_sources()
    assert "dummy_test_source" in sources
    cls = get_collector("dummy_test_source")
    assert cls == DummyTestCollector


def test_pkgutil_walk_packages_is_called() -> None:
    import ingestion.collectors

    with patch("pkgutil.walk_packages") as mock_walk, patch("importlib.import_module") as mock_import:
        mock_walk.return_value = [
            (None, "ingestion.collectors.mock_collector", False)
        ]
        
        importlib.reload(ingestion.collectors)
        
        mock_walk.assert_called_once()
        mock_import.assert_any_call("ingestion.collectors.mock_collector")
