from unittest.mock import mock_open, patch

import pytest

from ingestion.iceberg_schemas import (
    load_schema_config,
    schema_from_config,
)


def test_schema_from_config_success():
    config = {
        "source": "test_source",
        "columns": [
            {"name": "col_str", "type": "string"},
            {"name": "col_dbl", "type": "double"},
            {"name": "col_date", "type": "date"},
            {"name": "col_ts", "type": "timestamptz"},
        ],
        "partition": {
            "field": "col_ts",
            "transform": "day",
        },
    }
    schema, spec = schema_from_config(config)
    assert len(schema.fields) == 4
    assert spec.fields[0].name == "ingestion_day"


def test_schema_from_config_no_partition():
    config = {
        "source": "test_no_part",
        "columns": [
            {"name": "col_str", "type": "string"},
        ],
    }
    schema, spec = schema_from_config(config)
    assert len(schema.fields) == 1
    assert len(spec.fields) == 0


def test_schema_from_config_unknown_type():
    config = {
        "source": "bad_type",
        "columns": [
            {"name": "col_bad", "type": "unknown_type"},
        ],
    }
    with pytest.raises(ValueError, match="Unknown type 'unknown_type'"):
        schema_from_config(config)


def test_schema_from_config_unknown_transform():
    config = {
        "source": "bad_transform",
        "columns": [
            {"name": "col_ts", "type": "timestamptz"},
        ],
        "partition": {
            "field": "col_ts",
            "transform": "unknown_transform",
        },
    }
    with pytest.raises(ValueError, match="Unknown partition transform 'unknown_transform'"):
        schema_from_config(config)


def test_schema_from_config_missing_partition_field():
    config = {
        "source": "missing_part_field",
        "columns": [
            {"name": "col_str", "type": "string"},
        ],
        "partition": {
            "field": "col_missing",
            "transform": "day",
        },
    }
    with pytest.raises(ValueError, match="Partition field 'col_missing' not found"):
        schema_from_config(config)


@patch("pathlib.Path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="source: carbon_intensity\ncolumns: []")
def test_load_schema_config_success(mock_file, mock_exists):
    cfg = load_schema_config("carbon_intensity")
    assert cfg["source"] == "carbon_intensity"
    assert "columns" in cfg


def test_load_schema_config_not_found():
    with pytest.raises(FileNotFoundError):
        load_schema_config("non_existent_source_12345")
