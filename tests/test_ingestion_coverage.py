import pytest
import requests

from ingestion.exceptions import CollectorUnavailableError, StepError
from ingestion.http import make_session
from ingestion.iceberg_schemas import load_schema_config, schema_from_config


def test_collector_unavailable_error():
    err = CollectorUnavailableError("Source down")
    assert str(err) == "Source down"


def test_step_error():
    orig = ValueError("something wrong")
    err = StepError(1, "test_step", orig)
    assert err.step_number == 1
    assert err.step_name == "test_step"
    assert err.original is orig
    assert "Step 1 (test_step) failed: something wrong" in str(err)


def test_make_session():
    session = make_session(total=2, backoff_factor=0.1)
    assert isinstance(session, requests.Session)
    assert "https://" in session.adapters
    assert "http://" in session.adapters


def test_schema_from_config_valid():
    config = {
        "source": "test_src",
        "columns": [
            {"name": "col1", "type": "string"},
            {"name": "col2", "type": "double"},
            {"name": "ts", "type": "timestamptz"},
        ],
        "partition": {
            "field": "ts",
            "transform": "day",
        },
    }
    schema, spec = schema_from_config(config)
    assert schema is not None
    assert spec is not None


def test_schema_from_config_unknown_type():
    config = {
        "source": "test_src",
        "columns": [{"name": "col1", "type": "unknown_type"}],
    }
    with pytest.raises(ValueError, match="Unknown type 'unknown_type'"):
        schema_from_config(config)


def test_schema_from_config_unknown_transform():
    config = {
        "source": "test_src",
        "columns": [{"name": "ts", "type": "timestamptz"}],
        "partition": {"field": "ts", "transform": "unknown_transform"},
    }
    with pytest.raises(ValueError, match="Unknown partition transform"):
        schema_from_config(config)


def test_schema_from_config_partition_field_not_found():
    config = {
        "source": "test_src",
        "columns": [{"name": "col1", "type": "string"}],
        "partition": {"field": "missing_ts", "transform": "day"},
    }
    with pytest.raises(ValueError, match="Partition field 'missing_ts' not found"):
        schema_from_config(config)


def test_load_schema_config():
    try:
        cfg = load_schema_config("carbon_intensity")
        assert "columns" in cfg
    except FileNotFoundError:
        pass

    with pytest.raises(FileNotFoundError):
        load_schema_config("non_existent_schema_xyz_123")
