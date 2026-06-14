"""Connection-backed auto-collectors — bridges SDS-043↔SDS-044.

At import time, reads ``config/connections.yaml`` via ConnectionManager
and registers one DynamicCollector per connection.  Each collector fetches
from its configured source, validates against its YAML schema, and writes
to Bronze via BronzeWriter.

Graceful when ``connections.yaml`` is empty or the vault key is unset:
importing ``ingestion.collectors`` succeeds and ``list_sources()`` returns
only statically registered collectors.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import pandas as pd
import structlog

from ingestion.collectors.base import BaseCollector
from ingestion.collectors.registry import register_collector
from ingestion.iceberg_schemas import load_schema_config

if TYPE_CHECKING:
    from pyiceberg.catalog import Catalog

    from connections.manager import ConnectionConfig

logger = structlog.get_logger()

# ── safe import ──────────────────────────────────────────────────────────
_MGR: Any = None
try:
    from connections.manager import ConnectionManager

    _MGR = ConnectionManager()
except OSError as exc:
    logger.warning("dynamic_collector_vault_unset", reason=str(exc)[:120],
                   hint="Set SOLODSHOUSE_VAULT_KEY or leave connections.yaml empty.")
except Exception as exc:
    logger.warning("dynamic_collector_init_failed", reason=str(exc)[:120])


# ── collector class ──────────────────────────────────────────────────────

class DynamicCollector(BaseCollector):
    """Collector backed by a YAML connection entry (SDS-044).

    One instance per connection name.  Fetches data with raw drivers
    (requests / boto3 / psycopg2) — dlt is used by SchemaDiscovery,
    not by the collector itself.
    """

    def __init__(self, catalog: "Catalog", source_name: str = ""):  # pyright: ignore[reportUnannotatedClassAttribute]
        super().__init__(catalog)
        self._source = source_name
        self._conn: ConnectionConfig | None = None

    # ── public API ───────────────────────────────────────────────────────

    def collect(self, *args: Any, **kwargs: Any) -> dict[str, Any]:  # pyright: ignore[reportIncompatibleMethodOverride]
        conn = self._ensure_connection()
        raw = self._fetch_data(conn)
        valid, rejected = self._validate_records(raw)
        if valid:
            df = pd.DataFrame(valid)
            df["_ingestion_timestamp"] = pd.Timestamp.now(tz="UTC")
            df["_source"] = self._source
            self.bronze_writer.write(df, self._source)
        if rejected:
            self.bronze_writer.write_rejected(rejected, self._source)
        return {"valid": len(valid), "rejected": len(rejected)}

    def _fetch_data(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, conn: ConnectionConfig, *args: Any, **kwargs: Any
    ) -> list[dict[str, Any]]:
        cfg = conn.config
        if conn.type == "rest":
            return _fetch_rest(cfg)
        if conn.type == "s3":
            return _fetch_s3(self._source, cfg)
        if conn.type == "postgres":
            return _fetch_postgres(cfg)
        if conn.type == "filesystem":
            return _fetch_filesystem(cfg)
        raise ValueError(f"Unsupported connection type: {conn.type}")

    def _validate_records(  # pyright: ignore[reportIncompatibleMethodOverride]
        self, raw: list[dict[str, Any]], *args: Any, **kwargs: Any
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        if not raw:
            return [], []
        try:
            schema_cfg = load_schema_config(self._source)
            col_names = {c["name"] for c in schema_cfg.get("columns", [])}
        except FileNotFoundError:
            col_names = set(raw[0].keys()) if raw else set()

        valid: list[dict[str, Any]] = []
        rejected: list[dict[str, Any]] = []
        for record in raw:
            try:
                valid.append({k: record.get(k) for k in col_names if k not in
                              ("_ingestion_timestamp", "_source")})
            except Exception:
                rejected.append({"rejection_reason": "validation_error",
                                 "payload": str(record)[:500]})
        return valid, rejected

    # ── internal ─────────────────────────────────────────────────────────

    def _ensure_connection(self) -> ConnectionConfig:
        if self._conn is not None:
            return self._conn
        from connections.manager import ConnectionManager
        self._conn = ConnectionManager().get_connection(self._source)
        return self._conn


# ── fetch helpers ────────────────────────────────────────────────────────

def _fetch_rest(config: Any) -> list[dict[str, Any]]:
    import requests

    url = config.base_url
    endpoint: str = getattr(config, "endpoint", "") or ""
    full_url = f"{url.rstrip('/')}/{endpoint.lstrip('/')}" if endpoint else url
    resp = requests.get(full_url, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "items", "records"):
            if key in data and isinstance(data[key], list):
                return data[key]
        return [data]
    return []


def _fetch_s3(source: str, config: Any) -> list[dict[str, Any]]:
    import io

    import boto3

    bucket = config.bucket
    prefix: str = getattr(config, "prefix", "") or source
    file_glob: str = getattr(config, "file_glob", "*.parquet")

    client = boto3.client(
        "s3",
        endpoint_url=getattr(config, "endpoint", None) or None,
        aws_access_key_id=getattr(config, "access_key", None) or None,
        aws_secret_access_key=getattr(config, "secret_key", None) or None,
    )
    resp = client.list_objects_v2(Bucket=bucket, Prefix=prefix, MaxKeys=10)
    if not resp.get("Contents"):
        return []
    key = resp["Contents"][0]["Key"]
    obj = client.get_object(Bucket=bucket, Key=key)
    buf = io.BytesIO(obj["Body"].read())
    if key.endswith(".parquet") or file_glob.endswith(".parquet"):
        df = pd.read_parquet(buf)
    elif key.endswith(".csv") or file_glob.endswith(".csv"):
        df = pd.read_csv(buf)
    else:
        df = pd.read_parquet(buf)
    return df.to_dict(orient="records")


def _fetch_postgres(config: Any) -> list[dict[str, Any]]:
    import psycopg2

    conn = psycopg2.connect(
        host=config.host,
        port=config.port,
        dbname=config.database,
        user=config.user,
        password=config.password,
    )
    from psycopg2 import sql

    table: str = getattr(config, "table", "") or ""
    schema: str = getattr(config, "schema", "public") or "public"
    cur = conn.cursor()
    if table:
        query = sql.SQL("SELECT * FROM {}.{} LIMIT 1000").format(
            sql.Identifier(schema), sql.Identifier(table)
        )
    else:
        query = sql.SQL("SELECT * FROM information_schema.tables LIMIT 1000")
    cur.execute(query)
    cols = [desc[0] for desc in cur.description]
    rows = [dict(zip(cols, row)) for row in cur.fetchall()]
    conn.close()
    return rows


def _fetch_filesystem(config: Any) -> list[dict[str, Any]]:
    from pathlib import Path

    path: str = getattr(config, "path", "") or ""
    file_glob: str = getattr(config, "file_glob", "*.parquet")
    dir_path = Path(path)
    files = sorted(dir_path.rglob(file_glob)) if dir_path.exists() else []
    rows: list[dict[str, Any]] = []
    for f in files[:10]:
        if f.suffix == ".parquet":
            df = pd.read_parquet(f)
        elif f.suffix == ".csv":
            df = pd.read_csv(f)
        else:
            continue
        rows.extend(df.to_dict(orient="records"))
    return rows


# ── module-level auto-registration ───────────────────────────────────────

if _MGR is not None:
    for _name in _MGR.list_connections():
        _cls = type(
            f"_Dynamic_{_name}",
            (DynamicCollector,),
            {"_source": _name},
        )
        register_collector(_name)(_cls)
        logger.info("dynamic_collector_registered", source=_name)
