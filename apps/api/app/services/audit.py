from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import AuditCheck, AuditReport
from app.services.app_registry import summarize_registered_apps
from app.services.memory import get_memory_status
from app.services.permissions import list_permission_roles
from app.services.storage import get_storage_status


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def ensure_audit_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_reports (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def run_local_audit() -> AuditReport:
    ensure_audit_schema()
    placeholder = sql_placeholder()

    registry = summarize_registered_apps()
    storage = get_storage_status()
    memory = get_memory_status()
    roles = list_permission_roles()

    checks = [
        AuditCheck(
            id="app_registry_loaded",
            status="pass" if registry.total == 13 else "fail",
            detail=f"{registry.total} apps registered.",
        ),
        AuditCheck(
            id="external_connections_disabled",
            status="pass" if not registry.external_connections_enabled else "fail",
            detail="External app connections are disabled by design.",
        ),
        AuditCheck(
            id="storage_connected",
            status="pass" if storage.status == "connected" else "fail",
            detail=f"Storage backend: {storage.backend}.",
        ),
        AuditCheck(
            id="memory_local_operational",
            status="pass" if memory.status == "local_operational" else "fail",
            detail=f"Memory entries: {memory.entries}.",
        ),
        AuditCheck(
            id="roles_external_touch_disabled",
            status="pass"
            if all(role.can_touch_external_apps is False for role in roles)
            else "fail",
            detail=f"{len(roles)} roles loaded with external touch disabled.",
        ),
    ]

    report = AuditReport(
        id=str(uuid4()),
        status="pass" if all(check.status == "pass" for check in checks) else "fail",
        checks=checks,
        created_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            """
            INSERT INTO audit_reports (id, status, payload_json, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """.format(placeholder=placeholder),
            (
                report.id,
                report.status,
                report.model_dump_json(),
                report.created_at,
            ),
        )
        connection.commit()

    return report


def list_audit_reports() -> list[AuditReport]:
    ensure_audit_schema()

    with connect() as connection:
        rows = connection.execute(
            """
            SELECT payload_json
            FROM audit_reports
            ORDER BY created_at DESC
            """
        ).fetchall()

    return [AuditReport(**json.loads(row["payload_json"])) for row in rows]
