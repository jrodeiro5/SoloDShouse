import pytest

from ingestion.iceberg_schemas import load_schema_config, schema_from_config


def test_schema_from_config():
    sample_config = {
        "source": "test_sample",
        "columns": [
            {"name": "round_id", "type": "string"},
            {"name": "tokens_per_sec", "type": "double"},
            {"name": "ingested_at", "type": "timestamptz"},
        ],
        "partition": {"field": "ingested_at", "transform": "day"},
    }
    schema, partition_spec = schema_from_config(sample_config)
    assert schema is not None
    assert partition_spec is not None


def test_schema_from_config_invalid_type():
    invalid_config = {
        "source": "test_invalid",
        "columns": [{"name": "col1", "type": "unsupported_type"}],
    }
    with pytest.raises(ValueError, match="Unknown type 'unsupported_type'"):
        schema_from_config(invalid_config)


def test_schema_from_config_invalid_transform():
    invalid_config = {
        "source": "test_invalid",
        "columns": [{"name": "ts", "type": "timestamptz"}],
        "partition": {"field": "ts", "transform": "unsupported_transform"},
    }
    with pytest.raises(ValueError, match="Unknown partition transform 'unsupported_transform'"):
        schema_from_config(invalid_config)


def test_schema_from_config_missing_partition_field():
    invalid_config = {
        "source": "test_invalid",
        "columns": [{"name": "col1", "type": "string"}],
        "partition": {"field": "missing_ts", "transform": "day"},
    }
    with pytest.raises(ValueError, match="Partition field 'missing_ts' not found"):
        schema_from_config(invalid_config)


def test_load_schema_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_schema_config("non_existent_source_schema")
