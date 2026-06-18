from __future__ import annotations

import base64
from datetime import UTC, datetime
import hashlib
import json
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.core.database import connect, get_row_value, initialize_database, sql_placeholder
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.bunker import BunkerSealedAccess, BunkerSealedStatus, SealedReport
from app.schemas.cerebro import SombraInboxMessageCreate
from app.services.audit import create_audit_event

BUNKER_SEALED_REPORTS_TABLE = "bunker_sealed_reports"
PERU_TZ = ZoneInfo("America/Lima")


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def bunker_now() -> datetime:
    return datetime.now(PERU_TZ)


def ensure_bunker_vault_schema() -> None:
    initialize_database()
    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {BUNKER_SEALED_REPORTS_TABLE} (
                id TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                classification TEXT NOT NULL,
                original_message_id TEXT NOT NULL UNIQUE,
                filename_or_id TEXT NOT NULL,
                vault_path TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                content_size_bytes INTEGER NOT NULL,
                content_blob_base64 TEXT NOT NULL,
                status TEXT NOT NULL,
                access TEXT NOT NULL,
                source_created_at TEXT,
                received_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                audit_access_count INTEGER NOT NULL DEFAULT 0,
                metadata_json TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _json_load(value: str | None, fallback: object) -> object:
    try:
        return json.loads(value or "")
    except (TypeError, json.JSONDecodeError):
        return fallback


def sealed_vault_path(now: datetime | None = None) -> str:
    current = now or bunker_now()
    return f"BUNKER/SOMBRA/{current:%Y-%m-%d}/{current:%H-%M-%S}/"


def sealed_bytes(message: SombraInboxMessageCreate, raw_body: bytes) -> bytes:
    if raw_body:
        return raw_body
    return message.model_dump_json().encode("utf-8")


def filename_or_id(message: SombraInboxMessageCreate) -> str:
    candidate = (
        message.metadata.get("filename")
        or message.metadata.get("file_name")
        or message.metadata.get("name")
        or message.message_id
    )
    return " ".join(str(candidate or message.message_id).split())[:160] or message.message_id


def sealed_report_metadata(message: SombraInboxMessageCreate, content_hash: str, content_size: int) -> dict[str, object]:
    return {
        "origin": "SOMBRA",
        "classification": "SECRETO_MILITAR_CEO",
        "message_type": message.type.value,
        "severity": message.severity.value,
        "hash": content_hash,
        "size_bytes": content_size,
        "status": BunkerSealedStatus.sealed.value,
        "access": BunkerSealedAccess.ceo_only.value,
        "content_indexed": False,
        "llm_allowed": False,
        "embeddings_allowed": False,
        "preview_allowed": False,
        "routed_to_centinela": False,
        "routed_to_forja": False,
        "routed_to_pluma": False,
    }


def row_to_sealed_report(row: object) -> SealedReport:
    metadata = _json_load(get_row_value(row, "metadata_json", default="{}"), {})
    return SealedReport(
        id=get_row_value(row, "id"),
        source=get_row_value(row, "source"),
        classification=get_row_value(row, "classification"),
        original_message_id=get_row_value(row, "original_message_id"),
        filename_or_id=get_row_value(row, "filename_or_id"),
        vault_path=get_row_value(row, "vault_path"),
        content_sha256=get_row_value(row, "content_sha256"),
        content_size_bytes=int(get_row_value(row, "content_size_bytes", default=0) or 0),
        status=BunkerSealedStatus(get_row_value(row, "status")),
        access=BunkerSealedAccess(get_row_value(row, "access")),
        source_created_at=get_row_value(row, "source_created_at", default=None),
        received_at=get_row_value(row, "received_at"),
        updated_at=get_row_value(row, "updated_at"),
        audit_access_count=int(get_row_value(row, "audit_access_count", default=0) or 0),
        metadata=metadata if isinstance(metadata, dict) else {},
    )


def audit_bunker_event(
    *,
    action: str,
    status: str,
    detail: str,
    report: SealedReport | None = None,
    actor: AuthenticatedUser | None = None,
    metadata: dict[str, object] | None = None,
) -> str:
    merged_metadata: dict[str, object] = {
        "classification": "SECRETO_MILITAR_CEO",
        "content_included": False,
        "external_connection_enabled": False,
        "runtime_connected": False,
    }
    if report is not None:
        merged_metadata.update(
            {
                "sealed_report_id": report.id,
                "original_message_id": report.original_message_id,
                "vault_path": report.vault_path,
                "content_sha256": report.content_sha256,
                "content_size_bytes": report.content_size_bytes,
                "sealed_status": report.status.value,
                "access": report.access.value,
            }
        )
    if actor is not None:
        merged_metadata.update({"actor": actor.email or actor.name or actor.id, "role": actor.role.value})
    merged_metadata.update(metadata or {})
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.security,
            severity=AuditSeverity.high,
            source="bunker.sealed_vault",
            action=action,
            status=status,
            detail=detail,
            metadata=merged_metadata,
        )
    )
    return event.id


def archive_sealed_report(
    message: SombraInboxMessageCreate,
    *,
    raw_body: bytes = b"",
) -> SealedReport:
    ensure_bunker_vault_schema()
    placeholder = sql_placeholder()
    now = utc_now()
    body = sealed_bytes(message, raw_body)
    content_hash = hashlib.sha256(body).hexdigest()
    content_size = len(body)

    with connect() as connection:
        existing = connection.execute(
            f"SELECT * FROM {BUNKER_SEALED_REPORTS_TABLE} WHERE original_message_id = {placeholder}",
            (message.message_id,),
        ).fetchone()
        if existing is not None:
            report = row_to_sealed_report(existing)
            audit_bunker_event(
                action="sealed_report_duplicate_received",
                status="duplicate",
                detail="BUNKER kept an existing sealed SOMBRA report; content was not opened.",
                report=report,
            )
            return report

        metadata = sealed_report_metadata(message, content_hash, content_size)
        report_id = f"sealed-sombra-{uuid4()}"
        path = sealed_vault_path()
        connection.execute(
            f"""
            INSERT INTO {BUNKER_SEALED_REPORTS_TABLE} (
                id,
                source,
                classification,
                original_message_id,
                filename_or_id,
                vault_path,
                content_sha256,
                content_size_bytes,
                content_blob_base64,
                status,
                access,
                source_created_at,
                received_at,
                updated_at,
                audit_access_count,
                metadata_json
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                report_id,
                "SOMBRA",
                "SECRETO_MILITAR_CEO",
                message.message_id,
                filename_or_id(message),
                path,
                content_hash,
                content_size,
                base64.b64encode(body).decode("ascii"),
                BunkerSealedStatus.sealed.value,
                BunkerSealedAccess.ceo_only.value,
                message.created_at,
                now,
                now,
                0,
                _json_dump(metadata),
            ),
        )
        connection.commit()
        row = connection.execute(
            f"SELECT * FROM {BUNKER_SEALED_REPORTS_TABLE} WHERE id = {placeholder}",
            (report_id,),
        ).fetchone()

    report = row_to_sealed_report(row)
    audit_bunker_event(
        action="sealed_report_archived",
        status=report.status.value,
        detail="BUNKER archived a sealed SOMBRA report as CEO_ONLY metadata; content was not read.",
        report=report,
    )
    return report


def list_sealed_reports(limit: int = 50) -> list[SealedReport]:
    ensure_bunker_vault_schema()
    safe_limit = max(1, min(int(limit or 50), 100))
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM {BUNKER_SEALED_REPORTS_TABLE}
            ORDER BY received_at DESC
            LIMIT {safe_limit}
            """
        ).fetchall()
    return [row_to_sealed_report(row) for row in rows]


def get_sealed_report(report_id: str) -> SealedReport | None:
    ensure_bunker_vault_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT * FROM {BUNKER_SEALED_REPORTS_TABLE} WHERE id = {placeholder}",
            (report_id,),
        ).fetchone()
    return row_to_sealed_report(row) if row else None


def update_sealed_report_status(
    report_id: str,
    status: BunkerSealedStatus,
    *,
    actor: AuthenticatedUser,
    reason: str | None = None,
) -> SealedReport | None:
    ensure_bunker_vault_schema()
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {BUNKER_SEALED_REPORTS_TABLE}
            SET status = {placeholder},
                updated_at = {placeholder},
                audit_access_count = audit_access_count + 1
            WHERE id = {placeholder}
            """,
            (status.value, now, report_id),
        )
        connection.commit()
        row = connection.execute(
            f"SELECT * FROM {BUNKER_SEALED_REPORTS_TABLE} WHERE id = {placeholder}",
            (report_id,),
        ).fetchone()
    if row is None:
        return None
    report = row_to_sealed_report(row)
    audit_bunker_event(
        action="sealed_report_status_updated",
        status=report.status.value,
        detail="CEO updated sealed SOMBRA report state; content remains closed unless explicitly shared.",
        report=report,
        actor=actor,
        metadata={"reason": reason or "not_provided"},
    )
    return report


def audit_sealed_report_list_access(actor: AuthenticatedUser, count: int) -> None:
    audit_bunker_event(
        action="sealed_report_metadata_listed",
        status="metadata_only",
        detail="CEO listed sealed SOMBRA report metadata; content was not returned.",
        actor=actor,
        metadata={"items_returned": count},
    )
