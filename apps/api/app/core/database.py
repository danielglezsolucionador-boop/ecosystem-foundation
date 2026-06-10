from dataclasses import dataclass
from importlib import import_module
from pathlib import Path
import sqlite3
from typing import Any

from app.core.config import get_settings

SQLITE_PREFIX = "sqlite:///"
POSTGRES_PREFIXES = ("postgresql://", "postgres://")
SCHEMA_VERSION = "1"


@dataclass(frozen=True)
class DatabaseStatus:
    status: str
    backend: str
    configured: bool
    persistent: bool
    schema_version: str


def get_database_backend(database_url: str) -> str:
    if database_url.startswith(SQLITE_PREFIX):
        return "sqlite"
    if database_url.startswith(POSTGRES_PREFIXES):
        return "postgresql"
    raise RuntimeError(
        "Unsupported database URL. Expected sqlite:///, postgresql:// or postgres://."
    )


def sql_placeholder(database_url: str | None = None) -> str:
    url = database_url or get_settings().database_url
    return "%s" if get_database_backend(url) == "postgresql" else "?"


def resolve_sqlite_path(database_url: str) -> Path:
    if not database_url.startswith(SQLITE_PREFIX):
        raise RuntimeError("Only sqlite:/// database URLs are supported locally.")

    raw_path = database_url.removeprefix(SQLITE_PREFIX)

    if raw_path == ":memory:":
        return Path(":memory:")

    return Path(raw_path).expanduser().resolve()


def connect_sqlite(database_url: str) -> sqlite3.Connection:
    path = resolve_sqlite_path(database_url)

    if path != Path(":memory:"):
        path.parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def connect_postgres(database_url: str) -> Any:
    try:
        psycopg = import_module("psycopg")
        rows = import_module("psycopg.rows")
    except ImportError as exc:
        raise RuntimeError(
            "PostgreSQL DATABASE_URL is configured but psycopg is not installed. "
            "Install requirements.txt before starting the Vercel runtime."
        ) from exc

    return psycopg.connect(database_url, row_factory=rows.dict_row)


def connect(database_url: str | None = None) -> Any:
    url = database_url or get_settings().database_url
    backend = get_database_backend(url)

    if backend == "sqlite":
        return connect_sqlite(url)

    return connect_postgres(url)


def get_row_value(row: Any, key: str, index: int | None = None, default: Any = None) -> Any:
    if row is None:
        return default
    if isinstance(row, dict):
        return row.get(key, default)
    try:
        return row[key]
    except (KeyError, IndexError, TypeError):
        pass
    if index is not None:
        try:
            return row[index]
        except (KeyError, IndexError, TypeError):
            return default
    return default


def initialize_database(database_url: str | None = None) -> DatabaseStatus:
    url = database_url or get_settings().database_url
    backend = get_database_backend(url)
    placeholder = sql_placeholder(url)

    with connect(url) as connection:
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
            VALUES ('schema_version', {placeholder})
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """.format(placeholder=placeholder),
            (SCHEMA_VERSION,),
        )
        connection.commit()

        row = connection.execute(
            "SELECT value FROM platform_metadata WHERE key = 'schema_version'"
        ).fetchone()

    return DatabaseStatus(
        status="connected",
        backend=backend,
        configured=True,
        persistent=url != "sqlite:///:memory:",
        schema_version=get_row_value(row, "value"),
    )
