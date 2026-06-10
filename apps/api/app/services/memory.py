from datetime import UTC, datetime
import json
from typing import Any
from uuid import uuid4

from app.core.database import connect, get_row_value, initialize_database, sql_placeholder
from app.core.safe_data import safe_dict, safe_json_value, safe_list, safe_payload_json
from app.schemas.memory import (
    MemoryAuditEvent,
    MemoryEntry,
    MemoryEntryCreate,
    MemoryEntryUpdate,
    MemoryRecordStatus,
    MemoryStatus,
    MemoryType,
    MemoryVersion,
)
from app.services.storage import get_storage_status

MEMORY_TABLE = "ecosystem_memory_records"
MEMORY_VERSION_TABLE = "ecosystem_memory_versions"
MEMORY_AUDIT_TABLE = "ecosystem_memory_audit_events"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def ensure_memory_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MEMORY_TABLE} (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                content TEXT NOT NULL,
                type TEXT NOT NULL,
                status TEXT NOT NULL,
                source TEXT NOT NULL,
                app_id TEXT,
                service_id TEXT,
                tags_json TEXT NOT NULL,
                retention_policy TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                version INTEGER NOT NULL,
                external_source_connected INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MEMORY_VERSION_TABLE} (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                version INTEGER NOT NULL,
                action TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {MEMORY_AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                memory_id TEXT NOT NULL,
                action TEXT NOT NULL,
                version INTEGER NOT NULL,
                status TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def row_value(row: Any, key: str) -> Any:
    return get_row_value(row, key)


def row_to_memory_entry(row: Any) -> MemoryEntry:
    return MemoryEntry(
        id=row_value(row, "id"),
        title=row_value(row, "title"),
        content=row_value(row, "content"),
        type=row_value(row, "type"),
        status=row_value(row, "status"),
        source=row_value(row, "source"),
        app_id=row_value(row, "app_id"),
        service_id=row_value(row, "service_id"),
        tags=safe_list(safe_json_value(row_value(row, "tags_json"), [])),
        retention_policy=row_value(row, "retention_policy"),
        metadata=safe_dict(safe_json_value(row_value(row, "metadata_json"), {})),
        version=row_value(row, "version"),
        external_source_connected=bool(row_value(row, "external_source_connected")),
        created_at=row_value(row, "created_at"),
        updated_at=row_value(row, "updated_at"),
    )


def insert_memory_version(
    connection: Any,
    memory: MemoryEntry,
    action: str,
    placeholder: str,
) -> MemoryVersion:
    version = MemoryVersion(
        id=str(uuid4()),
        memory_id=memory.id,
        version=memory.version,
        action=action,
        payload=memory,
        created_at=utc_now(),
    )
    connection.execute(
        f"""
        INSERT INTO {MEMORY_VERSION_TABLE}
            (id, memory_id, version, action, payload_json, created_at)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        (
            version.id,
            version.memory_id,
            version.version,
            version.action,
            version.model_dump_json(),
            version.created_at,
        ),
    )
    return version


def insert_memory_audit_event(
    connection: Any,
    memory: MemoryEntry,
    action: str,
    status: str,
    placeholder: str,
) -> MemoryAuditEvent:
    event = MemoryAuditEvent(
        id=str(uuid4()),
        memory_id=memory.id,
        action=action,
        version=memory.version,
        status=status,
        created_at=utc_now(),
    )
    connection.execute(
        f"""
        INSERT INTO {MEMORY_AUDIT_TABLE}
            (id, memory_id, action, version, status, created_at)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        (
            event.id,
            event.memory_id,
            event.action,
            event.version,
            event.status,
            event.created_at,
        ),
    )
    return event


def list_memory_entries(
    app_id: str | None = None,
    type: MemoryType | None = None,
    status: MemoryRecordStatus | None = None,
) -> list[MemoryEntry]:
    ensure_memory_schema()
    placeholder = sql_placeholder()
    clauses: list[str] = []
    params: list[str] = []

    if app_id:
        clauses.append(f"app_id = {placeholder}")
        params.append(app_id.strip().lower())
    if type:
        clauses.append(f"type = {placeholder}")
        params.append(type.value)
    if status:
        clauses.append(f"status = {placeholder}")
        params.append(status.value)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id, title, content, type, status, source, app_id, service_id,
                tags_json, retention_policy, metadata_json, version,
                external_source_connected, created_at, updated_at
            FROM {MEMORY_TABLE}
            {where}
            ORDER BY updated_at DESC
            """,
            tuple(params),
        ).fetchall()

    return [row_to_memory_entry(row) for row in rows]


def get_memory_entry(memory_id: str) -> MemoryEntry | None:
    ensure_memory_schema()
    placeholder = sql_placeholder()

    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                id, title, content, type, status, source, app_id, service_id,
                tags_json, retention_policy, metadata_json, version,
                external_source_connected, created_at, updated_at
            FROM {MEMORY_TABLE}
            WHERE id = {placeholder}
            """,
            (memory_id,),
        ).fetchone()

    return row_to_memory_entry(row) if row else None


def create_memory_entry(entry: MemoryEntryCreate) -> MemoryEntry:
    ensure_memory_schema()
    placeholder = sql_placeholder()
    now = utc_now()
    memory_entry = MemoryEntry(
        id=str(uuid4()),
        title=entry.title,
        content=entry.content,
        type=entry.type,
        status=entry.status,
        source=entry.source,
        app_id=entry.app_id.strip().lower() if entry.app_id else None,
        service_id=entry.service_id.strip().lower() if entry.service_id else None,
        tags=entry.tags,
        retention_policy=entry.retention_policy,
        metadata=entry.metadata,
        version=1,
        external_source_connected=False,
        created_at=now,
        updated_at=now,
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {MEMORY_TABLE} (
                id, title, content, type, status, source, app_id, service_id,
                tags_json, retention_policy, metadata_json, version,
                external_source_connected, created_at, updated_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                memory_entry.id,
                memory_entry.title,
                memory_entry.content,
                memory_entry.type.value,
                memory_entry.status.value,
                memory_entry.source,
                memory_entry.app_id,
                memory_entry.service_id,
                json.dumps(memory_entry.tags, sort_keys=True),
                memory_entry.retention_policy,
                json.dumps(memory_entry.metadata, sort_keys=True),
                memory_entry.version,
                0,
                memory_entry.created_at,
                memory_entry.updated_at,
            ),
        )
        insert_memory_version(connection, memory_entry, "create", placeholder)
        insert_memory_audit_event(connection, memory_entry, "create", "success", placeholder)
        connection.commit()

    return memory_entry


def update_memory_entry(
    memory_id: str,
    update: MemoryEntryUpdate,
) -> MemoryEntry | None:
    current = get_memory_entry(memory_id)
    if current is None:
        return None

    placeholder = sql_placeholder()
    updated = MemoryEntry(
        id=current.id,
        title=update.title if update.title is not None else current.title,
        content=update.content if update.content is not None else current.content,
        type=update.type if update.type is not None else current.type,
        status=update.status if update.status is not None else current.status,
        source=update.source if update.source is not None else current.source,
        app_id=update.app_id.strip().lower()
        if update.app_id is not None
        else current.app_id,
        service_id=update.service_id.strip().lower()
        if update.service_id is not None
        else current.service_id,
        tags=update.tags if update.tags is not None else current.tags,
        retention_policy=update.retention_policy
        if update.retention_policy is not None
        else current.retention_policy,
        metadata=update.metadata if update.metadata is not None else current.metadata,
        version=current.version + 1,
        external_source_connected=False,
        created_at=current.created_at,
        updated_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {MEMORY_TABLE}
            SET
                title = {placeholder},
                content = {placeholder},
                type = {placeholder},
                status = {placeholder},
                source = {placeholder},
                app_id = {placeholder},
                service_id = {placeholder},
                tags_json = {placeholder},
                retention_policy = {placeholder},
                metadata_json = {placeholder},
                version = {placeholder},
                external_source_connected = {placeholder},
                updated_at = {placeholder}
            WHERE id = {placeholder}
            """,
            (
                updated.title,
                updated.content,
                updated.type.value,
                updated.status.value,
                updated.source,
                updated.app_id,
                updated.service_id,
                json.dumps(updated.tags, sort_keys=True),
                updated.retention_policy,
                json.dumps(updated.metadata, sort_keys=True),
                updated.version,
                0,
                updated.updated_at,
                updated.id,
            ),
        )
        insert_memory_version(connection, updated, update.change_reason, placeholder)
        insert_memory_audit_event(connection, updated, "update", "success", placeholder)
        connection.commit()

    return updated


def list_memory_versions(memory_id: str) -> list[MemoryVersion]:
    ensure_memory_schema()
    placeholder = sql_placeholder()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {MEMORY_VERSION_TABLE}
            WHERE memory_id = {placeholder}
            ORDER BY version DESC
            """,
            (memory_id,),
        ).fetchall()

    versions: list[MemoryVersion] = []
    for row in rows:
        payload = safe_payload_json(row_value(row, "payload_json"))
        if payload is None:
            continue
        try:
            versions.append(MemoryVersion(**payload))
        except Exception:
            continue
    return versions


def list_memory_by_app(app_id: str) -> list[MemoryEntry]:
    return list_memory_entries(app_id=app_id)


def list_memory_audit_events() -> list[MemoryAuditEvent]:
    ensure_memory_schema()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, memory_id, action, version, status, created_at
            FROM {MEMORY_AUDIT_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        MemoryAuditEvent(
            id=row_value(row, "id"),
            memory_id=row_value(row, "memory_id"),
            action=row_value(row, "action"),
            version=row_value(row, "version"),
            status=row_value(row, "status"),
            created_at=row_value(row, "created_at"),
        )
        for row in rows
    ]


def get_memory_status() -> MemoryStatus:
    ensure_memory_schema()
    storage = get_storage_status()

    with connect() as connection:
        entries_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {MEMORY_TABLE}"
        ).fetchone()
        versions_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {MEMORY_VERSION_TABLE}"
        ).fetchone()
        audit_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {MEMORY_AUDIT_TABLE}"
        ).fetchone()

    return MemoryStatus(
        status="local_operational",
        backend=storage.backend,
        entries=row_value(entries_row, "count"),
        versions=row_value(versions_row, "count"),
        audit_events=row_value(audit_row, "count"),
        supported_types=list(MemoryType),
        external_sources_connected=False,
    )
