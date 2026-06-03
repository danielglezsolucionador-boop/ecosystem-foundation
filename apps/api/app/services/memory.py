from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, initialize_database
from app.schemas.memory import MemoryEntry, MemoryEntryCreate, MemoryStatus


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def ensure_memory_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS ecosystem_memory_entries (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                tags_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def row_to_memory_entry(row) -> MemoryEntry:
    return MemoryEntry(
        id=row["id"],
        title=row["title"],
        content=row["content"],
        source=row["source"],
        tags=json.loads(row["tags_json"]),
        created_at=row["created_at"],
    )


def list_memory_entries() -> list[MemoryEntry]:
    ensure_memory_schema()

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT id, title, content, source, tags_json, created_at
            FROM ecosystem_memory_entries
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [row_to_memory_entry(row) for row in rows]


def create_memory_entry(entry: MemoryEntryCreate) -> MemoryEntry:
    ensure_memory_schema()

    memory_entry = MemoryEntry(
        id=str(uuid4()),
        title=entry.title,
        content=entry.content,
        source=entry.source,
        tags=entry.tags,
        created_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO ecosystem_memory_entries (
                id, title, content, source, tags_json, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                memory_entry.id,
                memory_entry.title,
                memory_entry.content,
                memory_entry.source,
                json.dumps(memory_entry.tags),
                memory_entry.created_at,
            ),
        )
        connection.commit()

    return memory_entry


def get_memory_status() -> MemoryStatus:
    ensure_memory_schema()

    with connect() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS count FROM ecosystem_memory_entries"
        ).fetchone()

    return MemoryStatus(
        status="local_operational",
        backend="sqlite",
        entries=row["count"],
        external_sources_connected=False,
    )

