"""Tests for the YAML-driven Iceberg schema builders (ingestion.iceberg_schemas)."""

from __future__ import annotations

from pathlib import Path

import pytest

from ingestion.iceberg_schemas import load_schema_config, schema_from_config


def test_schema_from_config_without_partition() -> None:
    schema, spec = schema_from_config(
        {
            "source": "demo",
            "columns": [
                {"name": "id", "type": "string"},
                {"name": "value", "type": "double"},
            ],
        }
    )
    assert [f.name for f in schema.fields] == ["id", "value"]
    assert spec.fields == ()


def test_schema_from_config_with_day_partition() -> None:
    schema, spec = schema_from_config(
        {
            "source": "demo",
            "columns": [
                {"name": "id", "type": "string"},
                {"name": "run_date", "type": "date"},
                {"name": "_ingestion_timestamp", "type": "timestamptz"},
            ],
            "partition": {"field": "_ingestion_timestamp", "transform": "day"},
        }
    )
    assert [f.name for f in schema.fields] == ["id", "run_date", "_ingestion_timestamp"]
    assert len(spec.fields) == 1
    partition_field = spec.fields[0]
    assert partition_field.name == "ingestion_day"
    assert partition_field.source_id == schema.fields[2].field_id
    assert str(partition_field.transform) == "day"


def test_schema_from_config_unknown_type_raises() -> None:
    with pytest.raises(ValueError, match="Unknown type 'uuid'"):
        schema_from_config({"source": "demo", "columns": [{"name": "id", "type": "uuid"}]})


def test_schema_from_config_unknown_transform_raises() -> None:
    with pytest.raises(ValueError, match="Unknown partition transform 'hour'"):
        schema_from_config(
            {
                "source": "demo",
                "columns": [{"name": "_ingestion_timestamp", "type": "timestamptz"}],
                "partition": {"field": "_ingestion_timestamp", "transform": "hour"},
            }
        )


def test_schema_from_config_unknown_partition_field_raises() -> None:
    with pytest.raises(ValueError, match="Partition field 'missing_col' not found"):
        schema_from_config(
            {
                "source": "demo",
                "columns": [{"name": "id", "type": "string"}],
                "partition": {"field": "missing_col", "transform": "day"},
            }
        )


def test_load_schema_config_missing_source_raises(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("ingestion.iceberg_schemas._SCHEMAS_DIR", tmp_path)
    with pytest.raises(FileNotFoundError):
        load_schema_config("does_not_exist")


def test_load_schema_config_reads_yaml(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "demo.yaml").write_text(
        "source: demo\n"
        "columns:\n"
        "  - name: id\n"
        "    type: string\n"
    )
    monkeypatch.setattr("ingestion.iceberg_schemas._SCHEMAS_DIR", tmp_path)
    cfg = load_schema_config("demo")
    assert cfg["source"] == "demo"
    assert cfg["columns"][0]["name"] == "id"
