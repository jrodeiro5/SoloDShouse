"""Tests for dbt project scaffolding — verify compile and macro resolution (SDS-041)."""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest

DBT_DIR = Path(__file__).resolve().parents[1] / "transformations" / "dbt"


def _dbt(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["dbt", *args, "--project-dir", str(DBT_DIR), "--profiles-dir", str(DBT_DIR)],
        capture_output=True, text=True, timeout=30,
        env={
            "DBT_DUCKDB_PATH": str(DBT_DIR / "target" / "test.duckdb"),
            "PATH": __import__("os").environ["PATH"],
        },
    )


@pytest.fixture(autouse=True)
def _clean_dbt_db() -> None:
    for pattern in ["test.duckdb", "test.duckdb.wal"]:
        p = DBT_DIR / "target" / pattern
        if p.exists():
            p.unlink()


class TestDbtScaffold:
    def test_project_compiles(self) -> None:
        result = _dbt(["compile"])
        assert result.returncode == 0, f"dbt compile failed: {result.stderr}"

    def test_project_parse_succeeds(self) -> None:
        result = _dbt(["parse"])
        assert result.returncode == 0, f"dbt parse failed: {result.stderr}"

    def test_one_model_found(self) -> None:
        result = _dbt(["ls"])
        models = [
            line for line in result.stdout.splitlines()
            if line.startswith("solodshouse.staging")
        ]
        assert len(models) >= 1, f"Expected staging content, got: {models}"

    def test_run_with_test_table_creates_view(self) -> None:
        import duckdb

        db_path = DBT_DIR / "target" / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE TABLE test_source (id INTEGER, name VARCHAR)")
        con.execute("INSERT INTO test_source VALUES (1, 'alice'), (2, 'bob')")
        con.close()

        result = _dbt(["run", "--select", "stg_generic", "--vars",
                        '{"source_table": "test_source"}'])
        assert result.returncode == 0, f"dbt run failed: {result.stderr}"

        con2 = duckdb.connect(str(db_path))
        rows = con2.execute(
            "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'stg_generic'"
        ).fetchone()
        assert rows is not None
        assert rows[0] == 1
        con2.close()

    def test_run_without_table_fails_gracefully(self) -> None:
        result = _dbt(["run", "--select", "stg_generic", "--vars",
                        '{"source_table": "nonexistent_table"}'])
        assert result.returncode != 0

    def test_dbt_test_runs_after_model(self) -> None:
        import duckdb

        db_path = DBT_DIR / "target" / "test.duckdb"
        con = duckdb.connect(str(db_path))
        con.execute("CREATE TABLE test_source (id INTEGER, name VARCHAR)")
        con.execute("INSERT INTO test_source VALUES (1, 'alice'), (2, 'bob')")
        con.close()

        run_result = _dbt(["run", "--select", "stg_generic", "--vars",
                            '{"source_table": "test_source"}'])
        assert run_result.returncode == 0

        test_result = _dbt(["test", "--select", "stg_generic"])
        assert test_result.returncode == 0, f"dbt test failed: {test_result.stderr}"

    def test_sources_yml_parses_glossary_docs(self) -> None:
        result = _dbt(["compile", "--select", "stg_generic"])
        assert result.returncode == 0
        assert "docs_glossary" not in result.stderr.lower()
