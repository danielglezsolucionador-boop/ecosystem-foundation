from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import (
    AuditCategory,
    AuditCheck,
    AuditEvent,
    AuditEventCreate,
    AuditOverview,
    AuditReport,
)
from app.services.app_registry import summarize_registered_apps
from app.services.contracts import get_contract_status
from app.services.events import get_event_status
from app.services.integration_bus import get_bus_status
from app.services.memory import get_memory_status
from app.services.permissions import list_permission_roles
from app.services.security import get_security_overview
from app.services.storage import get_storage_status

AUDIT_REPORTS_TABLE = "audit_reports"
CENTRAL_AUDIT_EVENTS_TABLE = "central_audit_events"


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def ensure_audit_schema() -> None:
    initialize_database()

    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS audit_reports (
                id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CENTRAL_AUDIT_EVENTS_TABLE} (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                source TEXT NOT NULL,
                action TEXT NOT NULL,
                status TEXT NOT NULL,
                detail TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def create_audit_event(event: AuditEventCreate) -> AuditEvent:
    ensure_audit_schema()
    placeholder = sql_placeholder()
    audit_event = AuditEvent(
        id=str(uuid4()),
        category=event.category,
        severity=event.severity,
        source=event.source,
        action=event.action,
        status=event.status,
        detail=event.detail,
        metadata=event.metadata,
        created_at=utc_now(),
    )

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {CENTRAL_AUDIT_EVENTS_TABLE} (
                id, category, severity, source, action, status, detail,
                metadata_json, created_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}
            )
            """,
            (
                audit_event.id,
                audit_event.category.value,
                audit_event.severity.value,
                audit_event.source,
                audit_event.action,
                audit_event.status,
                audit_event.detail,
                json.dumps(audit_event.metadata, sort_keys=True),
                audit_event.created_at,
            ),
        )
        connection.commit()

    return audit_event


def row_to_audit_event(row) -> AuditEvent:
    return AuditEvent(
        id=row["id"],
        category=row["category"],
        severity=row["severity"],
        source=row["source"],
        action=row["action"],
        status=row["status"],
        detail=row["detail"],
        metadata=json.loads(row["metadata_json"]),
        created_at=row["created_at"],
    )


def list_audit_events(category: AuditCategory | None = None) -> list[AuditEvent]:
    ensure_audit_schema()
    placeholder = sql_placeholder()
    where = ""
    params: tuple[str, ...] = ()

    if category:
        where = f"WHERE category = {placeholder}"
        params = (category.value,)

    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT
                id, category, severity, source, action, status, detail,
                metadata_json, created_at
            FROM {CENTRAL_AUDIT_EVENTS_TABLE}
            {where}
            ORDER BY created_at DESC
            """,
            params,
        ).fetchall()

    return [row_to_audit_event(row) for row in rows]


def get_audit_event(event_id: str) -> AuditEvent | None:
    ensure_audit_schema()
    placeholder = sql_placeholder()

    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT
                id, category, severity, source, action, status, detail,
                metadata_json, created_at
            FROM {CENTRAL_AUDIT_EVENTS_TABLE}
            WHERE id = {placeholder}
            """,
            (event_id,),
        ).fetchone()

    return row_to_audit_event(row) if row else None


def run_local_audit() -> AuditReport:
    ensure_audit_schema()
    placeholder = sql_placeholder()

    registry = summarize_registered_apps()
    storage = get_storage_status()
    memory = get_memory_status()
    roles = list_permission_roles()
    security = get_security_overview()
    events = get_event_status()
    integration_bus = get_bus_status()
    contracts = get_contract_status()

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
        AuditCheck(
            id="security_foundation_ready",
            status="pass"
            if security.status == "security_foundation_ready"
            and not security.secrets_exposed
            else "fail",
            detail=f"{len(security.roles)} roles and {len(security.policies)} policies.",
        ),
        AuditCheck(
            id="internal_events_operational",
            status="pass" if events.status == "internal_events_operational" else "fail",
            detail=f"{events.events} events tracked.",
        ),
        AuditCheck(
            id="integration_bus_operational",
            status="pass"
            if integration_bus.status == "integration_bus_operational"
            else "fail",
            detail=f"{integration_bus.routes} routes tracked.",
        ),
        AuditCheck(
            id="contracts_operational",
            status="pass" if contracts.status == "contracts_operational" else "fail",
            detail=f"{contracts.contracts} contracts tracked.",
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

    create_audit_event(
        AuditEventCreate(
            category=AuditCategory.runtime,
            severity="info",
            source="audit.run_local_audit",
            action="generate_report",
            status=report.status,
            detail=f"Local audit report generated with {len(report.checks)} checks.",
            metadata={"report_id": report.id},
        )
    )

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


def get_audit_overview() -> AuditOverview:
    ensure_audit_schema()
    events = list_audit_events()
    reports = list_audit_reports()
    severity_summary = {severity: 0 for severity in ["info", "low", "medium", "high", "critical"]}

    for event in events:
        severity_summary[event.severity.value] += 1

    return AuditOverview(
        status="central_audit_operational",
        events=len(events),
        reports=len(reports),
        severity_summary=severity_summary,
        categories=list(AuditCategory),
        external_connections_enabled=False,
    )
