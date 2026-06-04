from datetime import UTC, datetime
from functools import lru_cache
import json
from pathlib import Path
from typing import Any
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.events import (
    EventAuditEvent,
    EventCatalogItem,
    EventConsumer,
    EventCreate,
    EventRecord,
    EventReplayResult,
    EventStatus,
    EventStatusSummary,
)

DATA_PATH = Path(__file__).resolve().parents[1] / "data"
EVENTS_CATALOG_PATH = DATA_PATH / "events_catalog.json"
EVENTS_CONSUMERS_PATH = DATA_PATH / "events_consumers.json"
EVENTS_TABLE = "internal_events"
EVENTS_AUDIT_TABLE = "internal_event_audit"


class EventValidationError(RuntimeError):
    def __init__(self, detail: dict[str, object]) -> None:
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def row_value(row: Any, key: str) -> Any:
    return row[key]


def read_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


@lru_cache
def list_event_catalog() -> tuple[EventCatalogItem, ...]:
    raw_catalog = read_json(EVENTS_CATALOG_PATH)
    return tuple(EventCatalogItem(**item) for item in raw_catalog)


def get_event_catalog_item(event_type: str) -> EventCatalogItem | None:
    normalized_type = event_type.strip()
    return next(
        (item for item in list_event_catalog() if item.id == normalized_type),
        None,
    )


@lru_cache
def list_event_consumers() -> tuple[EventConsumer, ...]:
    raw_consumers = read_json(EVENTS_CONSUMERS_PATH)
    return tuple(EventConsumer(**item) for item in raw_consumers)


def ensure_events_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {EVENTS_TABLE} (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                source TEXT NOT NULL,
                subject TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                replay_count INTEGER NOT NULL,
                external_queue_connected INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {EVENTS_AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                event_id TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def row_to_event(row: Any) -> EventRecord:
    return EventRecord(
        id=row_value(row, "id"),
        type=row_value(row, "type"),
        source=row_value(row, "source"),
        subject=row_value(row, "subject"),
        status=row_value(row, "status"),
        payload=json.loads(row_value(row, "payload_json")),
        metadata=json.loads(row_value(row, "metadata_json")),
        replay_count=row_value(row, "replay_count"),
        external_queue_connected=bool(row_value(row, "external_queue_connected")),
        created_at=row_value(row, "created_at"),
        updated_at=row_value(row, "updated_at"),
    )


def insert_event_audit(
    connection: Any,
    event_id: str,
    action: str,
    status: EventStatus,
    detail: str,
    placeholder: str,
) -> EventAuditEvent:
    audit = EventAuditEvent(
        id=str(uuid4()),
        event_id=event_id,
        action=action,
        status=status,
        detail=detail,
        created_at=utc_now(),
    )
    connection.execute(
        f"""
        INSERT INTO {EVENTS_AUDIT_TABLE}
            (id, event_id, action, status, detail, created_at)
        VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """,
        (
            audit.id,
            audit.event_id,
            audit.action,
            audit.status.value,
            audit.detail,
            audit.created_at,
        ),
    )
    return audit


def validate_event_payload(event: EventCreate) -> EventCatalogItem:
    catalog_item = get_event_catalog_item(event.type)
    if catalog_item is None:
        raise EventValidationError(
            {
                "error": "event_type_not_registered",
                "event_type": event.type,
            }
        )

    missing_fields = [
        field
        for field in catalog_item.required_payload_fields
        if field not in event.payload
    ]
    if missing_fields:
        raise EventValidationError(
            {
                "error": "event_payload_missing_required_fields",
                "event_type": event.type,
                "missing_fields": missing_fields,
            }
        )

    return catalog_item


def publish_event(event: EventCreate) -> EventRecord:
    ensure_events_schema()
    validate_event_payload(event)
    placeholder = sql_placeholder()
    now = utc_now()
    event_status = (
        EventStatus.dead_letter if event.route_to_dead_letter else EventStatus.published
    )
    record = EventRecord(
        id=str(uuid4()),
        type=event.type,
        source=event.source,
        subject=event.subject,
        status=event_status,
        payload=event.payload,
        metadata=event.metadata,
        replay_count=0,
        external_queue_connected=False,
        created_at=now,
        updated_at=now,
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {EVENTS_TABLE} (
                id, type, source, subject, status, payload_json, metadata_json,
                replay_count, external_queue_connected, created_at, updated_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                record.id,
                record.type,
                record.source,
                record.subject,
                record.status.value,
                json.dumps(record.payload, sort_keys=True),
                json.dumps(record.metadata, sort_keys=True),
                record.replay_count,
                0,
                record.created_at,
                record.updated_at,
            ),
        )
        insert_event_audit(
            connection,
            record.id,
            "dead_letter" if event.route_to_dead_letter else "publish",
            record.status,
            "Event persisted in local internal event history.",
            placeholder,
        )
        connection.commit()

    return record


def list_events(
    status: EventStatus | None = None,
    type: str | None = None,
    source: str | None = None,
) -> list[EventRecord]:
    ensure_events_schema()
    placeholder = sql_placeholder()
    clauses: list[str] = []
    params: list[str] = []

    if status:
        clauses.append(f"status = {placeholder}")
        params.append(status.value)
    if type:
        clauses.append(f"type = {placeholder}")
        params.append(type.strip())
    if source:
        clauses.append(f"source = {placeholder}")
        params.append(source.strip())

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id, type, source, subject, status, payload_json, metadata_json,
                replay_count, external_queue_connected, created_at, updated_at
            FROM {EVENTS_TABLE}
            {where}
            ORDER BY updated_at DESC
            """,
            tuple(params),
        ).fetchall()

    return [row_to_event(row) for row in rows]


def get_event(event_id: str) -> EventRecord | None:
    ensure_events_schema()
    placeholder = sql_placeholder()

    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                id, type, source, subject, status, payload_json, metadata_json,
                replay_count, external_queue_connected, created_at, updated_at
            FROM {EVENTS_TABLE}
            WHERE id = {placeholder}
            """,
            (event_id,),
        ).fetchone()

    return row_to_event(row) if row else None


def replay_event(event_id: str, reason: str) -> EventReplayResult | None:
    original = get_event(event_id)
    if original is None:
        return None

    ensure_events_schema()
    placeholder = sql_placeholder()
    now = utc_now()
    replayed = EventRecord(
        id=str(uuid4()),
        type=original.type,
        source=original.source,
        subject=original.subject,
        status=EventStatus.replayed,
        payload=original.payload,
        metadata={**original.metadata, "replay_reason": reason, "original_event_id": original.id},
        replay_count=original.replay_count + 1,
        external_queue_connected=False,
        created_at=now,
        updated_at=now,
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {EVENTS_TABLE} (
                id, type, source, subject, status, payload_json, metadata_json,
                replay_count, external_queue_connected, created_at, updated_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                replayed.id,
                replayed.type,
                replayed.source,
                replayed.subject,
                replayed.status.value,
                json.dumps(replayed.payload, sort_keys=True),
                json.dumps(replayed.metadata, sort_keys=True),
                replayed.replay_count,
                0,
                replayed.created_at,
                replayed.updated_at,
            ),
        )
        audit = insert_event_audit(
            connection,
            replayed.id,
            "replay",
            EventStatus.replayed,
            f"Replay requested for {original.id}: {reason}",
            placeholder,
        )
        connection.commit()

    return EventReplayResult(
        original_event_id=original.id,
        replayed_event=replayed,
        audit_event_id=audit.id,
    )


def list_event_audit() -> list[EventAuditEvent]:
    ensure_events_schema()

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT id, event_id, action, status, detail, created_at
            FROM {EVENTS_AUDIT_TABLE}
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [
        EventAuditEvent(
            id=row_value(row, "id"),
            event_id=row_value(row, "event_id"),
            action=row_value(row, "action"),
            status=row_value(row, "status"),
            detail=row_value(row, "detail"),
            created_at=row_value(row, "created_at"),
        )
        for row in rows
    ]


def list_dead_letter_events() -> list[EventRecord]:
    return list_events(status=EventStatus.dead_letter)


def get_event_status() -> EventStatusSummary:
    ensure_events_schema()

    with connect() as connection:
        events_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {EVENTS_TABLE}"
        ).fetchone()
        dead_letter_row = connection.execute(
            f"SELECT COUNT(*) AS count FROM {EVENTS_TABLE} WHERE status = 'dead_letter'"
        ).fetchone()

    return EventStatusSummary(
        status="internal_events_operational",
        events=row_value(events_row, "count"),
        dead_letter_events=row_value(dead_letter_row, "count"),
        catalog_items=len(list_event_catalog()),
        consumers=len(list_event_consumers()),
        external_queue_connected=False,
    )
