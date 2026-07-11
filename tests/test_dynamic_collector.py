"""Tests for ingestion.collectors.dynamic — connection → collector bridge."""

from __future__ import annotations

import importlib
import tempfile
from pathlib import Path
from textwrap import dedent
from unittest.mock import MagicMock, patch

import pytest

from connections.manager import ConnectionManager
from connections.vault import FernetVault, generate_key
from ingestion.collectors.base import BaseCollector
from ingestion.collectors.dynamic import _MGR, DynamicCollector
from ingestion.collectors.registry import get_collector, register_collector


@pytest.fixture
def vault() -> FernetVault:
    return FernetVault(key=generate_key())


@pytest.fixture
def conn_yaml(vault: FernetVault) -> Path:
    enc = vault.encrypt("test123")
    content = dedent(f"""\
    connections:
      - name: api_test
        type: rest
        roles: [reader]
        base_url: https://httpbin.org
        endpoint: json

      - name: s3_test
        type: s3
        roles: [reader]
        endpoint: http://localhost:9000
        bucket: test-bucket
        access_key: minioadmin
        secret_key: vault://{enc}
        prefix: test-prefix/
        file_glob: "*.parquet"

      - name: pg_test
        type: postgres
        roles: [reader, admin]
        host: localhost
        port: 5432
        database: testdb
        user: tester
        password: vault://{enc}
        schema: public
        table: test_table

      - name: fs_test
        type: filesystem
        roles: [reader]
        path: /tmp/test-data
        file_glob: "*.csv"
    """)
    tmp = Path(tempfile.mkstemp(suffix=".yaml")[1])
    tmp.write_text(content)
    return tmp


class TestDynamicCollectorRegistration:
    def test_all_connection_types_registered(
        self, conn_yaml: Path, vault: FernetVault
    ) -> None:
        mgr = ConnectionManager(config_path=conn_yaml, vault=vault)
        sources = mgr.list_connections()
        assert len(sources) == 4
        for name in ["api_test", "s3_test", "pg_test", "fs_test"]:
            assert name in sources

    def test_manual_registration_adds_to_registry(
        self, conn_yaml: Path, vault: FernetVault
    ) -> None:
        mgr = ConnectionManager(config_path=conn_yaml, vault=vault)
        for name in mgr.list_connections():
            cls = type(f"_Test_{name}", (DynamicCollector,), {"_source": name})
            register_collector(name)(cls)

        for name in mgr.list_connections():
            collector_cls = get_collector(name)
            assert issubclass(collector_cls, BaseCollector)

    def test_dynamic_module_import_handles_missing_yaml(self) -> None:
        import ingestion.collectors.dynamic as dyn
        importlib.reload(dyn)
        if _MGR is None:
            pass
        else:
            assert _MGR.list_connections() == []


class TestDynamicCollectorBehavior:
    @pytest.fixture(autouse=True)
    def _set_vault_key(self, monkeypatch) -> None:
        monkeypatch.setenv("SOLODSHOUSE_VAULT_KEY", generate_key())

    def _make_collector_cls(self, source_name: str) -> type:
        cls = type(f"_Test_{source_name}", (DynamicCollector,), {"_source": source_name})
        register_collector(source_name)(cls)
        return cls

    def _mock_catalog(self) -> MagicMock:
        return MagicMock()

    def test_collect_rest_with_mocked_fetch(self) -> None:
        cls = self._make_collector_cls("collector_rest_test")
        mock_fetch = [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
        mock_conn = MagicMock()
        mock_conn.type = "rest"
        with (
            patch.object(cls, "_fetch_data", return_value=mock_fetch),
            patch.object(cls, "_ensure_connection", return_value=mock_conn),
        ):
            catalog = self._mock_catalog()
            collector = cls(catalog=catalog, source_name="collector_rest_test")
            result = collector.collect()
            assert result["valid"] == 2
            assert result["rejected"] == 0

    def test_collect_writes_to_bronze(self) -> None:
        cls = self._make_collector_cls("collector_bronze_test")
        mock_fetch = [{"x": 1}, {"x": 2}, {"x": 3}]
        mock_conn = MagicMock()
        mock_conn.type = "rest"
        with (
            patch.object(cls, "_fetch_data", return_value=mock_fetch),
            patch.object(cls, "_ensure_connection", return_value=mock_conn),
        ):
            catalog = self._mock_catalog()
            collector = cls(catalog=catalog, source_name="collector_bronze_test")
            collector.bronze_writer = MagicMock()
            result = collector.collect()
            assert result["valid"] == 3
            collector.bronze_writer.write.assert_called_once()

    def test_collect_rejects_invalid_records(self) -> None:
        cls = self._make_collector_cls("collector_reject_test")
        mock_fetch = [{"id": 1}, {"id": 2, "bad": "value"}]
        mock_conn = MagicMock()
        mock_conn.type = "rest"

        def _failing_validate(raw, *a, **kw):
            valid = [r for r in raw if "bad" not in r]
            rejected = [{"rejection_reason": "bad_field", "payload": str(r)}
                        for r in raw if "bad" in r]
            return valid, rejected

        with (
            patch.object(cls, "_fetch_data", return_value=mock_fetch),
            patch.object(cls, "_validate_records", side_effect=_failing_validate),
            patch.object(cls, "_ensure_connection", return_value=mock_conn),
        ):
            catalog = self._mock_catalog()
            collector = cls(catalog=catalog, source_name="collector_reject_test")
            collector.bronze_writer = MagicMock()
            result = collector.collect()
            assert result["valid"] == 1
            assert result["rejected"] == 1

    def test_validate_records_filters_by_schema_columns(self) -> None:
        cls = self._make_collector_cls("validate_test")
        catalog = self._mock_catalog()
        collector = cls(catalog=catalog, source_name="validate_test")
        raw = [
            {"id": 1, "name": "A", "extra": "ignored"},
            {"id": 2, "name": "B", "extra": "also-ignored"},
        ]
        schema_cols = [{"name": "id"}, {"name": "name"}]
        with patch("ingestion.collectors.dynamic.load_schema_config",
                   return_value={"columns": schema_cols}):
            valid, rejected = collector._validate_records(raw)
            assert len(valid) == 2
            assert len(rejected) == 0
            assert "extra" not in valid[0]

    def test_fetch_rest_url_construction(self) -> None:
        from connections.manager import RestConfig
        from ingestion.collectors.dynamic import _fetch_rest

        config = RestConfig(base_url="https://example.com", endpoint="api/v2/data")
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = [{"a": 1}]
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            result = _fetch_rest(config)
            mock_get.assert_called_once_with("https://example.com/api/v2/data", timeout=30)
            assert result == [{"a": 1}]

    def test_unsupported_connection_type_raises(self) -> None:
        cls = self._make_collector_cls("bad_type_test")
        catalog = self._mock_catalog()
        collector = cls(catalog=catalog, source_name="bad_type_test")
        mock_conn = MagicMock()
        mock_conn.type = "kafka"
        with pytest.raises(ValueError, match="Unsupported connection type"):
            collector._fetch_data(mock_conn)
