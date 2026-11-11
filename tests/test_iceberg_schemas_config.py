"""Tests for YAML-driven schema config helpers (schema_from_config / load_schema_config)."""

from __future__ import annotations

import pytest

from ingestion import iceberg_schemas
from ingestion.iceberg_schemas import load_schema_config, schema_from_config


def _column(name: str, type_name: str) -> dict:
    return {"name": name, "type": type_name}


def test_schema_from_config_builds_schema_without_partition() -> None:
    config = {
        "source": "carbon_intensity",
        "columns": [
            _column("timestamp_utc", "timestamptz"),
            _column("country", "string"),
            _column("carbon_intensity_gco2_kwh", "double"),
            _column("observed_on", "date"),
        ],
    }

    schema, spec = schema_from_config(config)

    assert [f.name for f in schema.fields] == [
        "timestamp_utc",
        "country",
        "carbon_intensity_gco2_kwh",
        "observed_on",
    ]
    assert len(spec.fields) == 0


def test_schema_from_config_builds_day_partition_spec() -> None:
    config = {
        "source": "carbon_intensity",
        "columns": [
            _column("timestamp_utc", "timestamptz"),
            _column("country", "string"),
        ],
        "partition": {"field": "country", "transform": "day"},
    }

    schema, spec = schema_from_config(config)

    assert len(schema.fields) == 2
    assert len(spec.fields) == 1
    partition_field = spec.fields[0]
    assert partition_field.name == "ingestion_day"
    assert partition_field.source_id == 2
    assert partition_field.field_id == 1000


def test_schema_from_config_rejects_unknown_column_type() -> None:
    config = {"source": "bad", "columns": [_column("value", "int")]}

    with pytest.raises(ValueError, match="Unknown type"):
        schema_from_config(config)


def test_schema_from_config_rejects_unknown_partition_transform() -> None:
    config = {
        "source": "bad",
        "columns": [_column("country", "string")],
        "partition": {"field": "country", "transform": "hour"},
    }

    with pytest.raises(ValueError, match="Unknown partition transform"):
        schema_from_config(config)


def test_schema_from_config_rejects_partition_field_not_in_columns() -> None:
    config = {
        "source": "bad",
        "columns": [_column("country", "string")],
        "partition": {"field": "missing_column", "transform": "day"},
    }

    with pytest.raises(ValueError, match="Partition field 'missing_column' not found"):
        schema_from_config(config)


def test_load_schema_config_reads_yaml_file(tmp_path, monkeypatch) -> None:
    schema_dir = tmp_path / "schemas"
    schema_dir.mkdir()
    (schema_dir / "carbon_intensity.yaml").write_text(
        "source: carbon_intensity\ncolumns: []\n", encoding="utf-8"
    )
    monkeypatch.setattr(iceberg_schemas, "_SCHEMAS_DIR", schema_dir)

    config = load_schema_config("carbon_intensity")

    assert config["source"] == "carbon_intensity"
    assert config["columns"] == []
