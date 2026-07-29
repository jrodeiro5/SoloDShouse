---
title: Manage Connections
summary: How to add, configure, and manage data connections using YAML configuration with FernetVault encryption and role-based access control.
topics: [guides, connections, security, configuration]
---

# Manage Connections

This guide explains how to manage data connections in SoloDShouse using
YAML configuration with FernetVault encryption and role-based access control.
Connections enable domain-agnostic data ingestion through the connections layer
(SDS-044).

## Configuration File

Connections are defined in `config/connections.yaml`:

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

  - name: my_api
    type: rest
    roles:
      - reader
    base_url: https://api.example.com
    endpoint: /data
```

Each connection entry includes:

- **name**: Unique identifier for the connection
- **type**: Connection type (postgres, s3, rest, filesystem)
- **roles**: List of access roles (reader, writer, etc.)
- **config**: Type-specific configuration parameters

## Adding a Connection

### Step 1: Choose Connection Type

Supported connection types:

- **postgres**: PostgreSQL database connections
- **s3**: S3-compatible object storage (SeaweedFS)
- **rest**: REST API endpoints
- **filesystem**: Local filesystem paths

### Step 2: Define Connection Configuration

Create a connection entry in `config/connections.yaml`:

#### PostgreSQL Example

```yaml
- name: production_db
  type: postgres
  roles:
    - reader
    - writer
  host: db.example.com
  port: 5432
  database: production
  user: app_user
  password: vault://encrypted_password_here
  schema: public
  table: users
```

#### S3 Example

```yaml
- name: data_lake
  type: s3
  roles:
    - reader
  endpoint: http://localhost:8333
  bucket: my-bucket
  access_key: vault://encrypted_access_key
  secret_key: vault://encrypted_secret_key
  prefix: data/
  file_glob: "*.parquet"
```

#### REST Example

```yaml
- name: weather_api
  type: rest
  roles:
    - reader
  base_url: https://api.weather.com
  endpoint: /v1/forecast
  method: GET
  headers:
    Authorization: Bearer ${WEATHER_API_KEY}
```

#### Filesystem Example

```yaml
- name: local_data
  type: filesystem
  roles:
    - reader
  path: /data/raw
  file_glob: "*.csv"
```

### Step 3: Encrypt Sensitive Values

For sensitive credentials, use FernetVault encryption:

```bash
# Generate a Fernet key
python -c "from connections.vault import generate_key; print(generate_key())"

# Export the key
export SOLODSHOUSE_VAULT_KEY="your_fernet_key_here"

# Encrypt a value
python -c "from connections.vault import FernetVault; print(FernetVault().encrypt('my_secret'))"
```

The encrypted value is prefixed with `vault://` in the YAML file:

```yaml
password: vault://encrypted_value_here
```

### Step 4: Verify Connection

Test the connection using SchemaDiscovery:

```python
from connections.discovery import SchemaDiscovery
from connections.manager import ConnectionManager

discovery = SchemaDiscovery()
connection = ConnectionManager().get_connection("my_connection")
schema = discovery.discover("my_connection", connection)
print(schema)
```

This probes the connection and writes the inferred schema to
`config/schemas/my_connection.yaml`.

## Connection Management

### List Connections

```python
from connections.manager import ConnectionManager

mgr = ConnectionManager()
connections = mgr.list_connections()
print(connections)  # ['connection1', 'connection2', ...]
```

### Get Connection

```python
connection = mgr.get_connection("my_connection")
print(connection.type)  # 'postgres'
print(connection.roles)  # ['reader', 'writer']
print(connection.config.host)  # 'db.example.com'
```

### Get Connections by Role

```python
readers = mgr.get_connections_by_role("reader")
writers = mgr.get_connections_by_role("writer")
```

### Reload Configuration

```python
mgr.reload()  # Re-reads config/connections.yaml
```

## Role-Based Access Control

Connections support role-based access control through the `roles` field:

```yaml
- name: sensitive_db
  type: postgres
  roles:
    - admin  # Only admin role can access
  host: sensitive-db.example.com
  # ...
```

Access connections by role:

```python
admin_connections = mgr.get_connections_by_role("admin")
reader_connections = mgr.get_connections_by_role("reader")
```

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

Common issues and solutions:

### Missing Configuration File

**Symptom**: `ConnectionManager` logs warning and continues with empty connection map

**Solution**: Create `config/connections.yaml` with at least one connection entry

### Unset Vault Key

**Symptom**: Dynamic collectors fail to initialize, logs warning

**Solution**: Set `SOLODSHOUSE_VAULT_KEY` environment variable:

```bash
export SOLODSHOUSE_VAULT_KEY=$(python -c "from connections.vault import generate_key; print(generate_key())")
```

### Invalid Connection Type

**Symptom**: `ValueError: unknown type 'invalid_type'`

**Solution**: Use one of the supported types: `postgres`, `s3`, `rest`, `filesystem`

### Missing Required Fields

**Symptom**: `ValueError: Connection 'name' field 'host' or it is empty`

**Solution**: Ensure all required fields for the connection type are present

### Decryption Failures

**Symptom**: `ValueError: Connection 'name' field 'password': failed to decrypt vault value`

**Solution**: Verify the Fernet key matches the one used for encryption:

```bash
export SOLODSHOUSE_VAULT_KEY="correct_fernet_key"
```

## Schema Discovery

For connected sources, use SchemaDiscovery to automatically infer schemas:

```python
from connections.discovery import SchemaDiscovery
from connections.manager import ConnectionManager

discovery = SchemaDiscovery()
connection = ConnectionManager().get_connection("my_source")
schema = discovery.discover("my_source", connection)
```

This writes the inferred schema to `config/schemas/my_source.yaml` and returns
the schema dictionary.

## See Also

- [Collector Pattern](../concepts/collector-pattern.md) — plugin system
- [Dynamic Collector](../concepts/dynamic-collector.md) — connection-backed collectors
- [Schema Discovery](../concepts/schema-discovery.md) — dlt-powered schema inference
- [Medallion Architecture](../concepts/medallion-architecture.md) — Bronze→Silver→Gold
- [Add New Source](add-new-source.md) — how to add data sources
