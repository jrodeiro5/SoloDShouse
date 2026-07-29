---
title: Connections Layer
summary: YAML-driven connection management with FernetVault encryption, schema discovery, and role-based access control for data sources.
topics: [architecture, connections, security, configuration]
---

# Connections Layer

The connections layer manages data source configurations through YAML-driven
declarative definitions with FernetVault encryption for sensitive credentials.
It provides role-based access control, schema discovery, and dynamic collector
registration for domain-agnostic data ingestion.

This layer bridges configuration management with the collector pattern (SDS-043)
and schema discovery (SDS-044), enabling zero-configuration data source
onboarding.

## Architecture Overview

The connections layer consists of three main components:

1. **ConnectionManager** — Loads, decrypts, and exposes typed connection
   configurations from YAML files
2. **FernetVault** — Encrypts/decrypts sensitive credentials using Fernet
   symmetric encryption
3. **SchemaDiscovery** — Probes connected sources using dlt and infers
   Iceberg schemas

These components work together to provide a complete connection management
solution that integrates with the collector registry and dynamic collector
system.

## Connection Configuration

Connections are defined in `config/connections.yaml` with the following structure:

```yaml
connections:
  - name: my_database
    type: postgres
    roles:
      - reader
      - writer
    host: localhost
    port: 5432
    database: mydb
    user: admin
    password: vault://encrypted_value
    schema: public
    table: my_table
```

Each connection entry includes:

- **name**: Unique identifier for the connection
- **type**: Connection type (postgres, s3, rest, filesystem)
- **roles**: List of access roles (reader, writer, etc.)
- **config**: Type-specific configuration parameters

## Supported Connection Types

### PostgreSQL

```python
class PostgresConfig(BaseConfigModel):
    host: str
    port: int = 5432
    database: str
    user: str
    password: str
    schema: str = "public"
    table: str | None = None
```

PostgreSQL connections support schema and table specification, with automatic
table discovery if no table is specified.

### S3

```python
class S3Config(BaseConfigModel):
    endpoint: str | None = None
    bucket: str
    access_key: str | None = None
    secret_key: str | None = None
    prefix: str | None = None
    file_glob: str = "*.parquet"
```

S3 connections support endpoint customization, bucket and prefix specification,
and file glob patterns for multi-file ingestion.

### REST

```python
class RestConfig(BaseConfigModel):
    base_url: str
    endpoint: str | None = None
    method: str = "GET"
    headers: dict[str, str] = Field(default_factory=dict)
```

REST connections support base URL and endpoint composition, HTTP method
specification, and custom headers.

### Filesystem

```python
class FilesystemConfig(BaseConfigModel):
    path: str | None = None
    file_glob: str = "*.parquet"
```

Filesystem connections support local directory paths and file glob patterns
for batch ingestion.

## ConnectionManager

The `ConnectionManager` class provides the primary interface for managing
connections:

```python
class ConnectionManager:
    def __init__(
        self,
        config_path: str | Path = "config/connections.yaml",
        vault: FernetVault | None = None,
    ) -> None:
        self._config_path = Path(config_path)
        self._vault = vault or FernetVault()
        self._connections: dict[str, ConnectionConfig] = {}
        self.reload()
```

Key methods:

- **reload()**: Re-reads the YAML config file and rebuilds the connection map
- **list_connections()**: Returns sorted list of registered connection names
- **get_connection(name)**: Returns the connection config for a name (raises KeyError if not found)
- **get_connections_by_role(role)**: Returns all connections accessible to a role

### Configuration Loading

The `reload()` method:

1. Reads `config/connections.yaml`
2. Parses connection entries
3. Resolves `${ENV_VAR}` placeholders
4. Decrypts `vault://` prefixed values
5. Validates connection types and roles
6. Stores validated connections in memory

### Placeholder Resolution

ConnectionManager supports two placeholder types:

1. **Environment variables**: `${ENV_VAR}` syntax resolved at runtime
2. **Vault-encrypted values**: `vault://encrypted_value` syntax decrypted
   using FernetVault

```python
def _resolve_placeholders(self, name: str, config: dict[str, str]) -> dict[str, str]:
    resolved: dict[str, str] = {}
    for key, value in config.items():
        value = self._resolve_env_vars(name, key, value)
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
```

## FernetVault

FernetVault provides symmetric encryption for sensitive credentials:

```python
class FernetVault:
    def __init__(self, key: str | None = None) -> None:
        env_key = key or os.environ.get("SOLODSHOUSE_VAULT_KEY")
        if not env_key:
            raise OSError(
                "SOLODSHOUSE_VAULT_KEY is not set. "
                "Generate a key with `python -c 'from connections.vault import generate_key; print(generate_key())'` "
                "and export it."
            )
        try:
            self._fernet = Fernet(env_key.encode("utf-8"))
        except Exception as exc:
            raise ValueError(
                "SOLODSHOUSE_VAULT_KEY is not a valid Fernet key. "
                "Generate one with generate_key()."
            ) from exc
```

Key features:

- **Key management**: Reads key from `SOLODSHOUSE_VAULT_KEY` environment variable
- **Encryption**: `encrypt(value)` returns base64-encoded Fernet token
- **Decryption**: `decrypt(token)` returns original plaintext
- **Key generation**: `generate_key()` creates new random Fernet keys

### Security Considerations

- Keys must be generated using `generate_key()` and stored securely
- The `SOLODSHOUSE_VAULT_KEY` environment variable should never be committed
- Decrypted values are returned as plaintext strings
- Tampered tokens raise `cryptography.fernet.InvalidToken`

## SchemaDiscovery Integration

The connections layer integrates with SchemaDiscovery for automatic schema
inference:

```python
class SchemaDiscovery:
    def __init__(self, schemas_dir: str | Path = SCHEMAS_DIR) -> None:
        self._schemas_dir = Path(schemas_dir)
        self._schemas_dir.mkdir(parents=True, exist_ok=True)

    def discover(self, source_name: str, connection: ConnectionConfig) -> dict[str, Any]:
        """Probe *connection*, infer schema, and persist to YAML."""
        inferred = self._infer_schema(source_name, connection)
        self._write_config(source_name, inferred)
        return inferred
```

SchemaDiscovery probes each connection type using dlt pipelines and writes
inferred schemas to `config/schemas/{source_name}.yaml`.

## Dynamic Collector Registration

At import time, the connections layer automatically registers dynamic
collectors for all configured connections:

```python
if _MGR is not None:
    for _name in _MGR.list_connections():
        _cls = type(f"_Dynamic_{_name}", (DynamicCollector,), {"_source": _name})
        register_collector(_name)(_cls)
        logger.info("dynamic_collector_registered", source=_name)
```

This means adding a new connection to `config/connections.yaml` automatically
creates a collector for it, enabling zero-configuration data ingestion.

## Error Handling

The connections layer handles several error scenarios:

- **Missing config file**: Logs warning and continues with empty connection map
- **Unset vault key**: Logs warning and continues with statically registered collectors
- **Invalid connection type**: Raises ValueError with valid types list
- **Missing required fields**: Raises ValueError with field name and entry details
- **Decryption failures**: Raises ValueError with connection name and field name
- **Environment variable resolution**: Raises ValueError with variable name and connection context

## See Also

- [Collector Pattern](../concepts/collector-pattern.md) — plugin system
- [Dynamic Collector](../concepts/dynamic-collector.md) — connection-backed collectors
- [Schema Discovery](../concepts/schema-discovery.md) — dlt-powered schema inference
- [Medallion Architecture](../concepts/medallion-architecture.md) — Bronze→Silver→Gold
