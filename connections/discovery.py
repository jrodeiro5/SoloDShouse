"""Schema auto-discovery — dlt-powered schema inference (SDS-044).

Probes a connected data source through dlt, infers column names and types,
and writes a declarative YAML schema to ``config/schemas/{source}.yaml``
so the SDS-043 collector registry picks it up automatically.

    discovery = SchemaDiscovery()
    schema = discovery.discover("my_source", connection_config)
    # -> writes config/schemas/my_source.yaml
    # -> returns {"table": "...", "columns": [...]}
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import structlog
import yaml

from connections.manager import (
    ConnectionConfig,
    FilesystemConfig,
    PostgresConfig,
    RestConfig,
    S3Config,
)

logger = structlog.get_logger()

SCHEMAS_DIR = Path("config/schemas")
_YAML_WIDTH = 120


class SchemaDiscovery:
    """Auto-discover table schemas from connected data sources using dlt.

    Results are persisted as YAML schema configs in ``config/schemas/``,
    compatible with the SDS-043 ``load_schema_config()`` / ``schema_from_config()``
    pipeline.
    """

    def __init__(self, schemas_dir: str | Path = SCHEMAS_DIR) -> None:
        self._schemas_dir = Path(schemas_dir)
        self._schemas_dir.mkdir(parents=True, exist_ok=True)

    def discover(self, source_name: str, connection: ConnectionConfig) -> dict[str, Any]:
        """Probe *connection*, infer schema, and persist to YAML.

        Returns a dict with ``source`` (str), ``connection_type`` (str),
        and ``columns`` (list[dict]).
        """
        inferred = self._infer_schema(source_name, connection)
        self._write_config(source_name, inferred)
        logger.info(
            "schema_discovered",
            source=source_name,
            conn_type=connection.type,
            columns=len(inferred.get("columns", [])),
        )
        return inferred

    def list_discovered(self) -> list[str]:
        """Return sorted list of discovered source names."""
        if not self._schemas_dir.exists():
            return []
        return sorted(
            p.stem for p in self._schemas_dir.glob("*.yaml") if p.is_file()
        )

    # ── internals ─────────────────────────────────────────────────────────

    def _infer_schema(
        self, source_name: str, connection: ConnectionConfig
    ) -> dict[str, Any]:
        config = connection.config
        conn_type = connection.type

        if conn_type == "postgres":
            assert isinstance(config, PostgresConfig)
            columns = self._probe_postgres(source_name, config)
        elif conn_type == "s3":
            assert isinstance(config, S3Config)
            columns = self._probe_s3(source_name, config)
        elif conn_type == "rest":
            assert isinstance(config, RestConfig)
            columns = self._probe_rest(source_name, config)
        elif conn_type == "filesystem":
            assert isinstance(config, FilesystemConfig)
            columns = self._probe_filesystem(source_name, config)
        else:
            raise ValueError(f"Unsupported connection type: {conn_type}")

        return {
            "source": source_name,
            "connection_type": conn_type,
            "columns": columns,
        }

    def _probe_postgres(self, source: str, config: PostgresConfig) -> list[dict[str, Any]]:
        table = config.table or source
        try:
            import dlt
            from dlt.sources import sql_database

            pipeline = dlt.pipeline(
                pipeline_name=f"discover_{source}",
                destination="duckdb",
                dataset_name="bronze",
            )
            conn_str = (
                f"postgresql://{config.user}:{config.password}"
                f"@{config.host}:{config.port}/{config.database}"
            )
            src = sql_database.sql_database(
                credentials=conn_str,
                schema=config.schema,
                table_names=[table],
            )
            pipeline.run(src)
            return _columns_from_dlt_schema(pipeline.default_schema, table)
        except ImportError:
            logger.warning("dlt_not_installed", hint="pip install dlt")
            return _fallback_columns()

    def _probe_s3(self, source: str, config: S3Config) -> list[dict[str, Any]]:
        prefix = config.prefix or source
        bucket = config.bucket
        try:
            import dlt
            from dlt.sources import filesystem

            pipeline = dlt.pipeline(
                pipeline_name=f"discover_{source}",
                destination="duckdb",
                dataset_name="bronze",
            )
            src = filesystem.filesystem(
                bucket_url=f"s3://{bucket}/{prefix}",
                file_glob=config.file_glob,
            )
            pipeline.run(src)
            return _columns_from_dlt_schema(pipeline.default_schema, source)
        except ImportError:
            logger.warning("dlt_not_installed", hint="pip install dlt")
            return _fallback_columns()

    def _probe_rest(self, source: str, config: RestConfig) -> list[dict[str, Any]]:
        url = config.base_url
        endpoint = config.endpoint or ""
        full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else url
        try:
            import dlt  # noqa: F811
            import requests

            resp = requests.get(full_url, timeout=30)
            resp.raise_for_status()
            data = resp.json()

            pipeline = dlt.pipeline(
                pipeline_name=f"discover_{source}",
                destination="duckdb",
                dataset_name="bronze",
            )
            if isinstance(data, list) and len(data) > 0:
                pipeline.run([data], table_name=source)
                return _columns_from_dlt_schema(pipeline.default_schema, source)
            return _infer_from_dict(_extract_first_record(data))
        except ImportError:
            logger.warning("dlt_not_installed", hint="pip install dlt[duckdb]")
            return _fallback_columns()
        except Exception as exc:
            logger.warning(
                "rest_probe_failed", source=source, url=full_url[:120],
                error=str(exc)[:200],
            )
            return _fallback_columns()

    def _probe_filesystem(self, source: str, config: FilesystemConfig) -> list[dict[str, Any]]:
        path = config.path or f"./data/{source}"
        try:
            import dlt
            from dlt.sources import filesystem

            pipeline = dlt.pipeline(
                pipeline_name=f"discover_{source}",
                destination="duckdb",
                dataset_name="bronze",
            )
            src = filesystem.filesystem(
                bucket_url=path,
                file_glob=config.file_glob,
            )
            pipeline.run(src)
            return _columns_from_dlt_schema(pipeline.default_schema, source)
        except ImportError:
            logger.warning("dlt_not_installed", hint="pip install dlt")
            return _fallback_columns()

    def _write_config(self, source_name: str, schema: dict[str, Any]) -> None:
        config = {
            "source": source_name,
            "columns": schema.get("columns", []),
            "auto_discovered": True,
        }
        out_path = self._schemas_dir / f"{source_name}.yaml"
        out_path.write_text(yaml.dump(config, sort_keys=False, width=_YAML_WIDTH))


# ── helpers ────────────────────────────────────────────────────────────────


def _columns_from_dlt_schema(
    dlt_schema: Any, table_name: str
) -> list[dict[str, Any]]:
    try:
        table = dlt_schema.tables.get(table_name)
        if table is None:
            return []
        return [
            {
                "name": col_name,
                "type": _map_dlt_to_iceberg(col.get("data_type", "string")),
                "nullable": col.get("nullable", True),
            }
            for col_name, col in table.get("columns", {}).items()
        ]
    except Exception:
        return []


def _map_dlt_to_iceberg(dlt_type: str) -> str:
    mapping: dict[str, str] = {
        "text": "string",
        "varchar": "string",
        "bigint": "long",
        "integer": "int",
        "smallint": "int",
        "boolean": "boolean",
        "double": "double",
        "float": "float",
        "timestamp": "timestamp",
        "date": "date",
        "decimal": "decimal(38,18)",
        "json": "string",
        "complex": "string",
    }
    return mapping.get(dlt_type.lower(), "string")


def _infer_from_dict(record: dict[str, Any]) -> list[dict[str, Any]]:
    type_map = {
        int: "long",
        float: "double",
        bool: "boolean",
        str: "string",
    }
    return [
        {
            "name": key,
            "type": type_map.get(type(val), "string"),
            "nullable": True,
        }
        for key, val in record.items()
    ]


def _extract_first_record(data: dict[str, Any] | list[Any]) -> dict[str, Any]:
    if isinstance(data, list) and len(data) > 0:
        first = data[0]
        if isinstance(first, dict):
            return first
    elif isinstance(data, dict):
        for key in ("data", "results", "items", "records"):
            if key in data and isinstance(data[key], list) and len(data[key]) > 0:
                first = data[key][0]
                if isinstance(first, dict):
                    return first
        return data
    return {}


def _fallback_columns() -> list[dict[str, Any]]:
    return [{"name": "_raw", "type": "string", "nullable": True}]
