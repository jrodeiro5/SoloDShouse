"""Connection manager — YAML-driven data source connections with vault-backed secrets (SDS-044).

Loads ``config/connections.yaml``, resolves ``${ENV_VAR}`` placeholders,
decrypts ``vault://`` prefixed values through FernetVault, and exposes
typed ``ConnectionConfig`` objects.

    mgr = ConnectionManager()
    mgr.list_connections()              # -> ["prod_pg", "data_lake"]
    conn = mgr.get_connection("prod_pg")
    conn.config["password"]             # decrypted plaintext
    mgr.get_connections_by_role("reader")  # role-based filtering
"""

from __future__ import annotations

import os
import re
import warnings
from pathlib import Path
from typing import Any, Union

warnings.filterwarnings(
    "ignore",
    category=UserWarning,
    message='Field name "schema" in "PostgresConfig" shadows an attribute in parent "BaseConfigModel"',
)

import structlog
import yaml
from pydantic import BaseModel, Field, model_validator

from connections.vault import FernetVault

logger = structlog.get_logger()

_VALID_TYPES = frozenset({"postgres", "s3", "rest", "filesystem"})
_ENV_VAR_RE = re.compile(r"\$\{(\w+)\}")


class BaseConfigModel(BaseModel):
    model_config = {
        "extra": "allow",
    }

    def __getitem__(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            raise KeyError(item)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item)

    def keys(self) -> Any:
        return self.model_dump().keys()

    def values(self) -> Any:
        return self.model_dump().values()

    def items(self) -> Any:
        return self.model_dump().items()


class PostgresConfig(BaseConfigModel):
    host: str
    port: int = 5432
    database: str
    user: str
    password: str
    schema: str = "public"  # type: ignore[assignment]
    table: str | None = None


class S3Config(BaseConfigModel):
    endpoint: str | None = None
    bucket: str
    access_key: str | None = None
    secret_key: str | None = None
    prefix: str | None = None
    file_glob: str = "*.parquet"


class RestConfig(BaseConfigModel):
    base_url: str
    endpoint: str | None = None
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)


class FilesystemConfig(BaseConfigModel):
    path: str | None = None
    file_glob: str = "*.parquet"


TypedConfig = Union[PostgresConfig, S3Config, RestConfig, FilesystemConfig]


class ConnectionConfig(BaseModel):
    """Validated connection descriptor with decrypted credentials."""

    name: str
    type: str  # postgres | s3 | rest | filesystem
    roles: list[str] = Field(default_factory=lambda: ["reader"])
    config: TypedConfig | dict[str, Any] | None = None

    @model_validator(mode="before")
    @classmethod
    def parse_config(cls, data: Any) -> Any:
        if isinstance(data, dict):
            config_val = data.get("config")
            conn_type = data.get("type")
            if isinstance(config_val, dict) and conn_type:
                if conn_type == "postgres":
                    data["config"] = PostgresConfig(**config_val)
                elif conn_type == "s3":
                    data["config"] = S3Config(**config_val)
                elif conn_type == "rest":
                    data["config"] = RestConfig(**config_val)
                elif conn_type == "filesystem":
                    data["config"] = FilesystemConfig(**config_val)
        return data


class ConnectionManager:
    """Load, decrypt, and expose data source connections.

    Args:
        config_path: Path to YAML file. Defaults to ``config/connections.yaml``.
        vault: FernetVault instance. Defaults to ``FernetVault()``.
    """

    def __init__(
        self,
        config_path: str | Path = "config/connections.yaml",
        vault: FernetVault | None = None,
    ) -> None:
        self._config_path = Path(config_path)
        self._vault = vault or FernetVault()
        self._connections: dict[str, ConnectionConfig] = {}
        self.reload()

    # ── public API ────────────────────────────────────────────────────────

    def reload(self) -> None:
        """Re-read the YAML config file and rebuild the connection map."""
        if not self._config_path.exists():
            logger.warning(
                "connections_config_missing",
                path=str(self._config_path),
                hint="Create config/connections.yaml to register data sources.",
            )
            self._connections = {}
            return

        raw = yaml.safe_load(self._config_path.read_text())
        entries: list[dict[str, Any]] = raw.get("connections", []) if isinstance(raw, dict) else []

        self._connections = {}
        for entry in entries:
            conn = self._parse_entry(entry)
            self._connections[conn.name] = conn

        logger.info(
            "connections_loaded",
            count=len(self._connections),
            sources=list(self._connections.keys()),
        )

    def list_connections(self) -> list[str]:
        """Return sorted list of registered connection names."""
        return sorted(self._connections.keys())

    def get_connection(self, name: str) -> ConnectionConfig:
        """Return the connection config for *name*.

        Raises ``KeyError`` if *name* is not registered.
        """
        if name not in self._connections:
            raise KeyError(
                f"Connection '{name}' not found. "
                f"Available: {list(self._connections.keys())}. "
                f"Add it to {self._config_path}."
            )
        return self._connections[name]

    def get_connections_by_role(self, role: str) -> list[ConnectionConfig]:
        """Return all connections accessible to *role*."""
        return [c for c in self._connections.values() if role in c.roles]

    # ── internals ─────────────────────────────────────────────────────────

    def _parse_entry(self, entry: dict[str, Any]) -> ConnectionConfig:
        name = _require_str(entry, "name")
        conn_type = _require_str(entry, "type")
        roles = entry.get("roles", ["reader"])

        if not isinstance(roles, list) or not all(isinstance(r, str) for r in roles):
            raise ValueError(f"Connection '{name}': 'roles' must be a list of strings.")

        if conn_type not in _VALID_TYPES:
            raise ValueError(
                f"Connection '{name}': unknown type '{conn_type}'. "
                f"Valid: {sorted(_VALID_TYPES)}."
            )

        # Strip metadata keys; remaining keys are connection-specific config
        config: dict[str, str] = {}
        for key, raw_val in entry.items():
            if key in {"name", "type", "roles"}:
                continue
            config[key] = str(raw_val) if raw_val is not None else ""

        # Resolve ${ENV_VAR} and vault:// placeholders
        config = self._resolve_placeholders(name, config)

        typed_config: TypedConfig
        if conn_type == "postgres":
            typed_config = PostgresConfig(**config)  # type: ignore[arg-type]
        elif conn_type == "s3":
            typed_config = S3Config(**config)  # type: ignore[arg-type]
        elif conn_type == "rest":
            typed_config = RestConfig(**config)  # type: ignore[arg-type]
        elif conn_type == "filesystem":
            typed_config = FilesystemConfig(**config)  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unknown type: {conn_type}")

        return ConnectionConfig(name=name, type=conn_type, roles=roles, config=typed_config)

    def _resolve_placeholders(self, name: str, config: dict[str, str]) -> dict[str, str]:
        resolved: dict[str, str] = {}
        for key, value in config.items():
            # 1. Resolve ${ENV_VAR} placeholders
            value = self._resolve_env_vars(name, key, value)
            # 2. Decrypt vault:// prefixed values
            if value.startswith("vault://"):
                try:
                    value = self._vault.decrypt(value.removeprefix("vault://"))
                except Exception as exc:
                    raise ValueError(
                        f"Connection '{name}' field '{key}': "
                        f"failed to decrypt vault value. {exc}"
                    ) from exc
            resolved[key] = value
        return resolved

    def _resolve_env_vars(self, name: str, key: str, value: str) -> str:
        def _replace(m: re.Match[str]) -> str:
            env_var = m.group(1)
            env_val = os.environ.get(env_var)
            if env_val is None:
                raise ValueError(
                    f"Connection '{name}' field '{key}': "
                    f"environment variable '${{{env_var}}}' is not set."
                )
            return env_val

        return _ENV_VAR_RE.sub(_replace, value)


# ── helpers ────────────────────────────────────────────────────────────────


def _require_str(entry: dict[str, Any], field: str) -> str:
    val = entry.get(field)
    if not isinstance(val, str) or not val.strip():
        raise ValueError(
            f"Connection entry missing required field '{field}' or it is empty: {entry}"
        )
    return val.strip()
