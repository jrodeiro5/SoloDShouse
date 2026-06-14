"""Tests for connections.discovery — dlt schema auto-discovery."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from connections.discovery import (
    SchemaDiscovery,
    _extract_first_record,
    _fallback_columns,
    _infer_from_dict,
    _map_dlt_to_iceberg,
)
from connections.manager import ConnectionConfig


class TestSchemaDiscovery:
    def test_list_discovered_empty_for_missing_dir(self) -> None:
        sd = SchemaDiscovery(schemas_dir=tempfile.mkdtemp())
        assert sd.list_discovered() == []

    def test_list_discovered_returns_yaml_stems(self) -> None:
        d = Path(tempfile.mkdtemp())
        (d / "source_a.yaml").write_text("columns: []")
        (d / "source_b.yaml").write_text("columns: []")
        sd = SchemaDiscovery(schemas_dir=d)
        names = sd.list_discovered()
        assert "source_a" in names
        assert "source_b" in names

    def test_discover_writes_yaml_config(self) -> None:
        d = Path(tempfile.mkdtemp())
        sd = SchemaDiscovery(schemas_dir=d)
        conn = ConnectionConfig(
            name="test_source",
            type="filesystem",
            roles=["reader"],
            config={"path": "/tmp"},
        )
        result = sd.discover("test_source", conn)
        assert result["source"] == "test_source"
        assert (d / "test_source.yaml").exists()

    def test_discover_rest_with_envelope(self) -> None:
        d = Path(tempfile.mkdtemp())
        sd = SchemaDiscovery(schemas_dir=d)
        conn = ConnectionConfig(
            name="api_source",
            type="rest",
            roles=["reader"],
            config={"base_url": "http://localhost", "endpoint": "/data"},
        )
        result = sd.discover("api_source", conn)
        assert result["source"] == "api_source"

    def test_unsupported_type_raises_value_error(self) -> None:
        sd = SchemaDiscovery(schemas_dir=tempfile.mkdtemp())
        conn = ConnectionConfig(
            name="bad",
            type="unknown_type",  # type: ignore[arg-type]
            roles=["reader"],
        )
        with pytest.raises(ValueError, match="Unsupported"):
            sd.discover("bad", conn)


class TestHelpers:
    def test_map_dlt_to_iceberg_known_types(self) -> None:
        assert _map_dlt_to_iceberg("text") == "string"
        assert _map_dlt_to_iceberg("bigint") == "long"
        assert _map_dlt_to_iceberg("boolean") == "boolean"
        assert _map_dlt_to_iceberg("double") == "double"

    def test_map_dlt_to_iceberg_unknown_falls_back_to_string(self) -> None:
        assert _map_dlt_to_iceberg("geography") == "string"

    def test_infer_from_dict(self) -> None:
        record = {"id": 1, "name": "Alice", "score": 95.5, "active": True}
        columns = _infer_from_dict(record)
        names = {c["name"] for c in columns}
        assert names == {"id", "name", "score", "active"}

    def test_extract_first_record_from_list(self) -> None:
        assert _extract_first_record([{"a": 1}, {"b": 2}]) == {"a": 1}

    def test_extract_first_record_from_envelope(self) -> None:
        assert _extract_first_record({"results": [{"x": "y"}]}) == {"x": "y"}

    def test_extract_first_record_empty(self) -> None:
        assert _extract_first_record([]) == {}

    def test_fallback_columns(self) -> None:
        cols = _fallback_columns()
        assert cols[0]["name"] == "_raw"
