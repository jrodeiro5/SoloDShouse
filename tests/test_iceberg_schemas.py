from __future__ import annotations

import pytest
from pyiceberg.partitioning import PartitionSpec
from pyiceberg.schema import Schema

import ingestion.iceberg_schemas as ibs
from ingestion.iceberg_schemas import load_schema_config, schema_from_config


def test_schema_from_config_valid():
    cfg = {
        "source": "test_src",
        "columns": [
            {"name": "col_str", "type": "string"},
            {"name": "col_dbl", "type": "double"},
            {"name": "_ts", "type": "timestamptz"},
        ],
        "partition": {
            "field": "_ts",
            "transform": "day",
        },
    }
    schema, spec = schema_from_config(cfg)
    assert isinstance(schema, Schema)
    assert isinstance(spec, PartitionSpec)
    assert len(schema.fields) == 3


def test_schema_from_config_unknown_type():
    cfg = {
        "source": "test_src",
        "columns": [{"name": "col1", "type": "unknown_type"}],
    }
    with pytest.raises(ValueError, match="Unknown type 'unknown_type'"):
        schema_from_config(cfg)


def test_schema_from_config_unknown_transform():
    cfg = {
        "source": "test_src",
        "columns": [{"name": "_ts", "type": "timestamptz"}],
        "partition": {"field": "_ts", "transform": "month"},
    }
    with pytest.raises(ValueError, match="Unknown partition transform 'month'"):
        schema_from_config(cfg)


def test_schema_from_config_partition_field_missing():
    cfg = {
        "source": "test_src",
        "columns": [{"name": "col1", "type": "string"}],
        "partition": {"field": "missing_ts", "transform": "day"},
    }
    with pytest.raises(ValueError, match="Partition field 'missing_ts' not found"):
        schema_from_config(cfg)


def test_load_schema_config_missing():
    with pytest.raises(FileNotFoundError, match="Schema config not found"):
        load_schema_config("non_existent_source")


def test_load_schema_config_success(tmp_path, monkeypatch):
    schema_file = tmp_path / "my_source.yaml"
    schema_file.write_text("source: my_source\ncolumns: []")
    monkeypatch.setattr(ibs, "_SCHEMAS_DIR", tmp_path)

    cfg = load_schema_config("my_source")
    assert cfg["source"] == "my_source"
