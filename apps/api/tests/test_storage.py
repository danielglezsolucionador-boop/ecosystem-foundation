import sqlite3

from fastapi.testclient import TestClient

from app.core.database import initialize_database, resolve_sqlite_path
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

