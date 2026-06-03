from dataclasses import dataclass
from pathlib import Path
import sqlite3

from app.core.config import get_settings

SQLITE_PREFIX = "sqlite:///"
SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class DatabaseStatus:
    status: str
    backend: str
    configured: bool
    persistent: bool
    schema_version: str


def resolve_sqlite_path(database_url: str) -> Path:
    if not database_url.startswith(SQLITE_PREFIX):
        raise RuntimeError("Only sqlite:/// database URLs are supported locally.")

    raw_path = database_url.removeprefix(SQLITE_PREFIX)

    if raw_path == ":memory:":
        return Path(":memory:")

    return Path(raw_path).expanduser().resolve()


def connect(database_url: str | None = None) -> sqlite3.Connection:
    url = database_url or get_settings().database_url
    path = resolve_sqlite_path(url)

    if path != Path(":memory:"):
        path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database(database_url: str | None = None) -> DatabaseStatus:
    with connect(database_url) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS platform_metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            INSERT INTO platform_metadata (key, value)
            VALUES ('schema_version', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (SCHEMA_VERSION,),
        )
        connection.commit()

        row = connection.execute(
            "SELECT value FROM platform_metadata WHERE key = 'schema_version'"
        ).fetchone()

    return DatabaseStatus(
        status="connected",
        backend="sqlite",
        configured=True,
        persistent=(database_url or get_settings().database_url) != "sqlite:///:memory:",
        schema_version=row["value"],
    )

