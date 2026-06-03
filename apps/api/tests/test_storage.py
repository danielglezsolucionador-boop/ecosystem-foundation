import sqlite3
import sys
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.core.database import (
    get_database_backend,
    initialize_database,
    resolve_sqlite_path,
    sql_placeholder,
)
from app.main import app


def test_resolve_sqlite_path_supports_local_database(tmp_path) -> None:
    database_file = tmp_path / "ecosystem.db"

    resolved = resolve_sqlite_path(f"sqlite:///{database_file}")

    assert resolved == database_file.resolve()


def test_initialize_database_creates_metadata_schema(tmp_path) -> None:
    database_file = tmp_path / "ecosystem.db"
    database_url = f"sqlite:///{database_file}"

    status = initialize_database(database_url)

    assert status.status == "connected"
    assert status.backend == "sqlite"
    assert status.configured is True
    assert status.persistent is True
    assert status.schema_version == "1"

    with sqlite3.connect(database_file) as connection:
        row = connection.execute(
            "SELECT value FROM platform_metadata WHERE key = 'schema_version'"
        ).fetchone()

    assert row[0] == "1"


def test_database_backend_detects_postgres_urls() -> None:
    assert get_database_backend("postgresql://user:pass@example.com:5432/db") == "postgresql"
    assert get_database_backend("postgres://user:pass@example.com:5432/db") == "postgresql"
    assert sql_placeholder("postgresql://user:pass@example.com:5432/db") == "%s"


def test_initialize_database_supports_postgres_connection_contract(monkeypatch) -> None:
    executed: list[tuple[str, tuple[str, ...] | None]] = []

    class FakeConnection:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def execute(self, sql, params=None):
            executed.append((sql, params))
            return self

        def fetchone(self):
            return {"value": "1"}

        def commit(self):
            return None

    fake_psycopg = SimpleNamespace(connect=lambda *_args, **_kwargs: FakeConnection())
    fake_rows = SimpleNamespace(dict_row=object())
    monkeypatch.setitem(sys.modules, "psycopg", fake_psycopg)
    monkeypatch.setitem(sys.modules, "psycopg.rows", fake_rows)

    status = initialize_database("postgresql://user:pass@example.com:5432/db")

    assert status.status == "connected"
    assert status.backend == "postgresql"
    assert status.persistent is True
    assert status.schema_version == "1"
    assert any("%s" in sql for sql, _params in executed)


def test_storage_status_endpoint() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/storage/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "status": "connected",
        "backend": "sqlite",
        "configured": True,
        "persistent": True,
        "schema_version": "1",
    }
