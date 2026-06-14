"""Abstract BaseCollector — domain-agnostic collector interface (SDS-043)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog


class BaseCollector(ABC):
    """Abstract collector for a named data source.

    Each collector subclass self-registers via the ``@register_collector``
    decorator in ``registry.py``.  Adding a new source = 1 collector file +
    1 YAML schema — zero Dagster or Bronze-writer edits.
    """

    def __init__(self, catalog: "Catalog"):
        self.catalog = catalog
        # Lazy import to avoid circular dependency at type-check time
        from ingestion.bronze_writer import BronzeWriter

        self.bronze_writer = BronzeWriter(catalog)

    # ── abstract ──────────────────────────────────────────────────────────

    @abstractmethod
    def collect(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Orchestrate the full ingestion: fetch → validate → write → return summary.

        Returns a dict with at least ``"valid"`` (int) and ``"rejected"`` (int).
        """
        ...

    @abstractmethod
    def _fetch_data(self, *args: Any, **kwargs: Any) -> Any:
        """Fetch raw data from the upstream source.

        Returns source-specific raw data (DataFrame, list[dict], etc.).
        """
        ...

    @abstractmethod
    def _validate_records(self, *args: Any, **kwargs: Any) -> tuple[list[dict], list[dict]]:
        """Validate & normalise raw records.

        Returns ``(valid_dicts, rejected_dicts)`` — both lists of
        flat dicts ready for Pydantic/Iceberg processing.
        """
        ...

    # ── helpers (concrete, overridable) ────────────────────────────────────

    def _already_ingested(self, source: str) -> bool:
        """Check if *source* data is already present in Bronze.

        Default: no-op (always returns ``False``).  Override when a source
        provides immutable releases (e.g. MLPerf round IDs) so duplicate
        ingestion can be skipped.
        """
        return False
