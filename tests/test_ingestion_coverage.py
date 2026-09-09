from unittest.mock import patch

import pytest

from ingestion.exceptions import CollectorUnavailableError, StepError
from ingestion.http import make_session
from ingestion.iceberg_schemas import load_schema_config, schema_from_config


def test_exceptions():
    err = CollectorUnavailableError("unreachable")
    assert str(err) == "unreachable"

    orig = ValueError("something went wrong")
    step_err = StepError(1, "extract", orig)
    assert step_err.step_number == 1
    assert step_err.step_name == "extract"
    assert step_err.original == orig
    assert "Step 1 (extract) failed: something went wrong" in str(step_err)


def test_http_make_session():
    session = make_session(total=2, backoff_factor=0.1)
    assert session is not None
    assert "http://" in session.adapters
    assert "https://" in session.adapters


def test_schema_from_config_valid():
    config = {
        "source": "test_src",
        "columns": [
            {"name": "id", "type": "string"},
            {"name": "val", "type": "double"},
            {"name": "ts", "type": "timestamptz"},
        ],
        "partition": {
            "field": "ts",
            "transform": "day",
        },
    }
    schema, part_spec = schema_from_config(config)
    assert schema is not None
    assert part_spec is not None
    assert len(schema.fields) == 3


def test_schema_from_config_no_partition():
    config = {
        "source": "test_src_nopart",
        "columns": [
            {"name": "id", "type": "string"},
        ],
    }
    schema, part_spec = schema_from_config(config)
    assert schema is not None
    assert len(part_spec.fields) == 0


def test_schema_from_config_unknown_type():
    config = {
        "source": "bad_type_src",
        "columns": [
            {"name": "id", "type": "unknown_type"},
        ],
    }
    with pytest.raises(ValueError, match="Unknown type 'unknown_type'"):
        schema_from_config(config)


def test_schema_from_config_unknown_transform():
    config = {
        "source": "bad_transform_src",
        "columns": [
            {"name": "ts", "type": "timestamptz"},
        ],
        "partition": {
            "field": "ts",
            "transform": "invalid_transform",
        },
    }
    with pytest.raises(ValueError, match="Unknown partition transform 'invalid_transform'"):
        schema_from_config(config)


def test_schema_from_config_missing_partition_field():
    config = {
        "source": "missing_part_field_src",
        "columns": [
            {"name": "id", "type": "string"},
        ],
        "partition": {
            "field": "non_existent",
            "transform": "day",
        },
    }
    with pytest.raises(ValueError, match="Partition field 'non_existent' not found"):
        schema_from_config(config)


def test_load_schema_config(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_schema_config("non_existent_source_schema_xyz")

    schema_file = tmp_path / "dummy_source.yaml"
    schema_file.write_text("source: dummy_source\ncolumns: []")

    with patch("ingestion.iceberg_schemas._SCHEMAS_DIR", tmp_path):
        config = load_schema_config("dummy_source")
        assert config["source"] == "dummy_source"
