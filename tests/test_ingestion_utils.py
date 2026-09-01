
import pytest

from ingestion.exceptions import CollectorUnavailableError, StepError
from ingestion.http import make_session
from ingestion.iceberg_schemas import load_schema_config, schema_from_config


def test_collector_unavailable_error():
    err = CollectorUnavailableError("Source down")
    assert str(err) == "Source down"


def test_step_error():
    orig = ValueError("Connection timeout")
    err = StepError(step_number=2, step_name="Ingest Bronze", original=orig)
    assert err.step_number == 2
    assert err.step_name == "Ingest Bronze"
    assert err.original is orig
    assert "Step 2 (Ingest Bronze) failed: Connection timeout" in str(err)


def test_make_session():
    session = make_session(total=2, backoff_factor=0.1)
    assert "https://" in session.adapters
    assert "http://" in session.adapters


def test_schema_from_config_valid_and_invalid():
    # Valid config with partition
    cfg = {
        "source": "test_src",
        "columns": [
            {"name": "id", "type": "string"},
            {"name": "val", "type": "double"},
            {"name": "ts", "type": "timestamptz"},
        ],
        "partition": {"field": "ts", "transform": "day"},
    }
    schema, spec = schema_from_config(cfg)
    assert len(schema.fields) == 3
    assert len(spec.fields) == 1

    # Valid config without partition
    cfg_no_part = {
        "source": "test_src",
        "columns": [{"name": "id", "type": "string"}],
    }
    schema2, spec2 = schema_from_config(cfg_no_part)
    assert len(schema2.fields) == 1
    assert len(spec2.fields) == 0

    # Unknown column type
    cfg_bad_type = {
        "source": "test_src",
        "columns": [{"name": "id", "type": "unknown_type"}],
    }
    with pytest.raises(ValueError, match="Unknown type 'unknown_type'"):
        schema_from_config(cfg_bad_type)

    # Unknown partition transform
    cfg_bad_transform = {
        "source": "test_src",
        "columns": [{"name": "ts", "type": "timestamptz"}],
        "partition": {"field": "ts", "transform": "unknown_transform"},
    }
    with pytest.raises(ValueError, match="Unknown partition transform"):
        schema_from_config(cfg_bad_transform)

    # Partition field missing from columns
    cfg_missing_part_field = {
        "source": "test_src",
        "columns": [{"name": "id", "type": "string"}],
        "partition": {"field": "ts", "transform": "day"},
    }
    with pytest.raises(ValueError, match="Partition field 'ts' not found"):
        schema_from_config(cfg_missing_part_field)


def test_load_schema_config_not_found():
    with pytest.raises(FileNotFoundError):
        load_schema_config("non_existent_source_12345")
