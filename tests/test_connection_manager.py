"""Tests for connections.manager — YAML-driven connection registry."""

from __future__ import annotations

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from connections.manager import ConnectionManager
from connections.vault import FernetVault, generate_key


@pytest.fixture
def vault() -> FernetVault:
    return FernetVault(key=generate_key())


@pytest.fixture
def config_file(vault: FernetVault) -> Path:
    enc_password = vault.encrypt("s3cr3t")
    yaml_content = dedent(f"""\
    connections:
      - name: prod_pg
        type: postgres
        roles: [reader, admin]
        host: db.example.com
        port: 5432
        database: analytics
        user: reader
        password: vault://{enc_password}

      - name: data_lake
        type: s3
        roles: [reader]
        endpoint: http://minio:9000
        bucket: raw-data
        access_key: minioadmin
        secret_key: vault://{vault.encrypt("minioadmin123")}

      - name: weather_api
        type: rest
        roles: [reader]
        base_url: https://api.weather.com
        endpoint: v1/forecast
    """)
    tmp = Path(tempfile.mktemp(suffix=".yaml"))
    tmp.write_text(yaml_content)
    return tmp


class TestConnectionManager:
    def test_list_connections(self, config_file: Path, vault: FernetVault) -> None:
        mgr = ConnectionManager(config_path=config_file, vault=vault)
        assert mgr.list_connections() == ["data_lake", "prod_pg", "weather_api"]

    def test_missing_config_file_returns_empty(self, monkeypatch) -> None:
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", generate_key())
        mgr = ConnectionManager(config_path="nonexistent.yaml")
        assert mgr.list_connections() == []

    def test_get_connection_returns_config(self, config_file: Path, vault: FernetVault) -> None:
        mgr = ConnectionManager(config_path=config_file, vault=vault)
        conn = mgr.get_connection("prod_pg")
        assert conn.name == "prod_pg"
        assert conn.type == "postgres"
        assert conn.roles == ["reader", "admin"]
        assert conn.config["host"] == "db.example.com"
        assert conn.config["user"] == "reader"
        assert conn.config["password"] == "s3cr3t"  # decrypted

    def test_get_connection_missing_raises_keyerror(self, config_file: Path, vault: FernetVault) -> None:
        mgr = ConnectionManager(config_path=config_file, vault=vault)
        with pytest.raises(KeyError, match="not found"):
            mgr.get_connection("nonexistent")

    def test_get_connections_by_role(self, config_file: Path, vault: FernetVault) -> None:
        mgr = ConnectionManager(config_path=config_file, vault=vault)
        admin_conns = mgr.get_connections_by_role("admin")
        assert len(admin_conns) == 1
        assert admin_conns[0].name == "prod_pg"

    def test_reader_role_returns_all(self, config_file: Path, vault: FernetVault) -> None:
        mgr = ConnectionManager(config_path=config_file, vault=vault)
        reader_conns = mgr.get_connections_by_role("reader")
        assert len(reader_conns) == 3

    def test_env_var_resolution(self, vault: FernetVault, monkeypatch) -> None:
        monkeypatch.setenv("DB_HOST", "prod-db.example.com")
        yaml = dedent("""\
        connections:
          - name: env_test
            type: postgres
            host: ${DB_HOST}
            port: 5432
            database: test
            user: admin
            password: plaintext
        """)
        tmp = Path(tempfile.mktemp(suffix=".yaml"))
        tmp.write_text(yaml)
        mgr = ConnectionManager(config_path=tmp, vault=vault)
        assert mgr.get_connection("env_test").config["host"] == "prod-db.example.com"

    def test_missing_env_var_raises_value_error(self, vault: FernetVault, monkeypatch) -> None:
        monkeypatch.delenv("MISSING_VAR", raising=False)
        yaml = dedent("""\
        connections:
          - name: missing_env
            type: postgres
            host: ${MISSING_VAR}
            port: 5432
            database: test
            user: admin
            password: pw
        """)
        tmp = Path(tempfile.mktemp(suffix=".yaml"))
        tmp.write_text(yaml)
        with pytest.raises(ValueError, match="MISSING_VAR"):
            ConnectionManager(config_path=tmp, vault=vault)

    def test_invalid_type_raises_value_error(self, vault: FernetVault) -> None:
        yaml = dedent("""\
        connections:
          - name: bad_type
            type: kafka
            host: localhost
        """)
        tmp = Path(tempfile.mktemp(suffix=".yaml"))
        tmp.write_text(yaml)
        with pytest.raises(ValueError, match="unknown type"):
            ConnectionManager(config_path=tmp, vault=vault)

    def test_missing_name_raises_value_error(self, vault: FernetVault) -> None:
        yaml = dedent("""\
        connections:
          - type: postgres
            host: localhost
        """)
        tmp = Path(tempfile.mktemp(suffix=".yaml"))
        tmp.write_text(yaml)
        with pytest.raises(ValueError, match="name"):
            ConnectionManager(config_path=tmp, vault=vault)

    def test_reload_updates_connections(self, vault: FernetVault) -> None:
        yaml1 = dedent("""\
        connections:
          - name: first
            type: rest
            base_url: http://localhost
        """)
        yaml2 = dedent("""\
        connections:
          - name: second
            type: s3
            bucket: new-bucket
        """)
        tmp = Path(tempfile.mktemp(suffix=".yaml"))
        tmp.write_text(yaml1)
        mgr = ConnectionManager(config_path=tmp, vault=vault)
        assert mgr.list_connections() == ["first"]
        tmp.write_text(yaml2)
        mgr.reload()
        assert mgr.list_connections() == ["second"]
