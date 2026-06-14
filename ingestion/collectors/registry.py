"""Collector registry — decorator-based plugin system (SDS-043).

``@register_collector("source_name")`` adds a collector to the module-level
registry.  Importing ``ingestion.collectors`` triggers registration of all
collectors in the package.

Usage::

    from ingestion.collectors.registry import register_collector, list_sources, get_collector

    @register_collector("my_source")
    class MyCollector(BaseCollector): ...

    list_sources()   # -> ["mlperf_benchmarks", "cloud_gpu_pricing", "my_source"]
    get_collector("my_source")  # -> <class MyCollector>
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ingestion.collectors.base import BaseCollector

_collectors: dict[str, type["BaseCollector"]] = {}


def register_collector(name: str):
    """Decorator that registers a BaseCollector subclass under *name*."""

    def _decorator(cls: type["BaseCollector"]) -> type["BaseCollector"]:
        _collectors[name] = cls
        return cls

    return _decorator


def list_sources() -> list[str]:
    """Return the sorted list of registered source names."""
    return sorted(_collectors.keys())


def get_collector(name: str) -> type["BaseCollector"]:
    """Return the registered collector class for *name*.

    Raises ``KeyError`` if *name* is not registered.
    """
    return _collectors[name]
