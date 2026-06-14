"""Connection layer — SDS-044 dlt-based connection, discovery, and auth.

Provides:
- ``FernetVault`` — encrypt/decrypt connection secrets
- ``ConnectionManager`` — YAML-driven source connection registry
- ``SchemaDiscovery`` — dlt-powered schema auto-discovery
"""

from connections.discovery import SchemaDiscovery
from connections.manager import ConnectionConfig, ConnectionManager
from connections.vault import FernetVault, generate_key

__all__ = [
    "ConnectionConfig",
    "ConnectionManager",
    "FernetVault",
    "SchemaDiscovery",
    "generate_key",
]
