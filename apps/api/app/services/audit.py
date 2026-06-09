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
    AuditoriaCriterion,
    AuditoriaDecisionRequest,
    AuditoriaObjectType,
    AuditoriaReview,
    AuditoriaReviewCreate,
    AuditoriaReviewStatus,
    AuditoriaStatus,
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
AUDITORIA_REVIEWS_TABLE = "auditoria_reviews"
PROTECTED_AUDITORIA_REFERENCES = {
    "dcft",
    "doctor_contable",
    "doctor_contable_financiero_tributario",
    "sentinela",
    "centinela",
    "arsenal",
    "cerebro_to_dcft_future",
    "cerebro_to_sentinela_future",
    "cerebro_to_arsenal_future",
}


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
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {AUDITORIA_REVIEWS_TABLE} (
                id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def normalize_review_reference(value: str) -> str:
    return str(value or "").strip().lower().replace("-", "_").replace(" ", "_")


def protected_reference(value: str) -> bool:
    normalized = normalize_review_reference(value)
    return normalized in PROTECTED_AUDITORIA_REFERENCES or any(
        protected_id in normalized
        for protected_id in [
            "doctor_contable_financiero_tributario",
            "dcft",
            "sentinela",
            "centinela",
            "arsenal",
        ]
    )


def default_auditoria_criteria() -> list[AuditoriaCriterion]:
    return [
        AuditoriaCriterion.visual_quality,
        AuditoriaCriterion.functional_quality,
        AuditoriaCriterion.security,
        AuditoriaCriterion.costs,
        AuditoriaCriterion.human_clarity,
        AuditoriaCriterion.ceo_standard,
        AuditoriaCriterion.technical_readiness,
        AuditoriaCriterion.operational_risk,
        AuditoriaCriterion.commercial_risk,
        AuditoriaCriterion.legal_tax_risk,
    ]


def save_auditoria_review(review: AuditoriaReview) -> AuditoriaReview:
    ensure_audit_schema()
    placeholder = sql_placeholder()
    review.updated_at = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {AUDITORIA_REVIEWS_TABLE} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (
                review.id,
                review.model_dump_json(),
                review.created_at,
                review.updated_at,
            ),
        )
        connection.commit()
    return review


def row_to_auditoria_review(row) -> AuditoriaReview:
    return AuditoriaReview(**json.loads(row["payload_json"]))


def list_auditoria_reviews(limit: int | None = None) -> list[AuditoriaReview]:
    ensure_audit_schema()
    placeholder = sql_placeholder()
    limit_clause = ""
    params: tuple[int, ...] = ()
    if limit is not None:
        limit_clause = f"LIMIT {placeholder}"
        params = (max(1, min(int(limit), 200)),)
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {AUDITORIA_REVIEWS_TABLE}
            ORDER BY updated_at DESC
            {limit_clause}
            """,
            params,
        ).fetchall()
    return [row_to_auditoria_review(row) for row in rows]


def get_auditoria_review(review_id: str) -> AuditoriaReview | None:
    ensure_audit_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"""
            SELECT payload_json
            FROM {AUDITORIA_REVIEWS_TABLE}
            WHERE id = {placeholder}
            """,
            (review_id,),
        ).fetchone()
    return row_to_auditoria_review(row) if row else None


def record_operational_audit_event(
    *,
    action: str,
    status: str,
    detail: str,
    review: AuditoriaReview,
    severity: str = "info",
    metadata: dict[str, object] | None = None,
) -> AuditEvent:
    return create_audit_event(
        AuditEventCreate(
            category=AuditCategory.permission,
            severity=severity,
            source="auditoria.operational_judge",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "review_id": review.id,
                "object_type": review.object_type.value,
                "reference": review.reference,
                "external_connection_enabled": False,
                "runtime_connected": False,
                **(metadata or {}),
            },
        )
    )


def record_bus_audit_from_auditoria(
    *,
    action: str,
    status: str,
    detail: str,
    route_id: str | None = None,
    event_id: str | None = None,
) -> None:
    try:
        from app.services.integration_bus import record_bus_audit_event

        record_bus_audit_event(
            action=action,
            status=status,
            detail=detail,
            route_id=route_id,
            event_id=event_id,
        )
    except Exception:
        return


def create_auditoria_review(request: AuditoriaReviewCreate) -> AuditoriaReview:
    now = utc_now()
    review = AuditoriaReview(
        id=f"auditoria-review-{uuid4()}",
        object_type=request.object_type,
        reference=request.reference.strip(),
        source=request.source.strip(),
        priority=request.priority,
        criteria=request.criteria or default_auditoria_criteria(),
        status=AuditoriaReviewStatus.pending_review,
        result=AuditoriaReviewStatus.pending_review,
        observations=request.observations,
        blockages=request.blockages,
        metadata=request.metadata,
        requires_ceo_decision=False,
        external_connection_enabled=False,
        runtime_connected=False,
        audit_event_ids=[],
        created_at=now,
        updated_at=now,
    )
    event = record_operational_audit_event(
        action="audit_review_created",
        status=review.status.value,
        detail=f"AUDITORIA review created for {review.object_type.value}:{review.reference}.",
        review=review,
        metadata={"source": request.source, "priority": request.priority},
    )
    review.audit_event_ids.append(event.id)
    saved = save_auditoria_review(review)
    record_bus_audit_from_auditoria(
        action="audit_review_created",
        status=saved.status.value,
        detail=f"AUDITORIA queued review {saved.id}.",
        route_id=str(request.metadata.get("route_id") or "") or None,
    )
    return saved


def create_auditoria_review_from_bus(
    *,
    route_id: str,
    subject: str,
    payload: dict[str, object],
    source: str = "cerebro",
) -> AuditoriaReview:
    object_type = AuditoriaObjectType.cerebro_task
    reference = str(payload.get("task_id") or subject)
    criteria = [
        AuditoriaCriterion.functional_quality,
        AuditoriaCriterion.security,
        AuditoriaCriterion.costs,
        AuditoriaCriterion.operational_risk,
        AuditoriaCriterion.ceo_standard,
    ]
    if str(payload.get("object_type") or "").strip():
        try:
            object_type = AuditoriaObjectType(str(payload["object_type"]))
        except ValueError:
            object_type = AuditoriaObjectType.cerebro_task
    review = create_auditoria_review(
        AuditoriaReviewCreate(
            object_type=object_type,
            reference=reference,
            source=source,
            priority=str(payload.get("priority") or "p2"),
            criteria=criteria,
            observations=[
                "CEREBRO envio esta tarea a AUDITORIA por bus interno.",
                "Sin runtime externo, sin APIs externas y sin secretos.",
            ],
            metadata={"route_id": route_id, "subject": subject},
        )
    )
    return review


def decide_auditoria_review(
    review_id: str,
    request: AuditoriaDecisionRequest,
) -> AuditoriaReview | None:
    review = get_auditoria_review(review_id)
    if review is None:
        return None

    if request.decision in {AuditoriaReviewStatus.pending_review, AuditoriaReviewStatus.in_review}:
        raise ValueError("invalid_auditoria_decision")

    if request.decision == AuditoriaReviewStatus.approved and (
        review.object_type == AuditoriaObjectType.protected_product
        or protected_reference(review.reference)
    ):
        event = record_operational_audit_event(
            action="audit_blocked",
            status=AuditoriaReviewStatus.blocked.value,
            detail="AUDITORIA cannot unlock protected products or protected routes.",
            review=review,
            severity="high",
            metadata={"attempted_decision": request.decision.value},
        )
        review.status = AuditoriaReviewStatus.blocked
        review.result = AuditoriaReviewStatus.blocked
        review.decision = AuditoriaReviewStatus.blocked
        review.blockages = [
            *review.blockages,
            "Protected product or route remains blocked; CEO decision and a separate future block are required.",
        ]
        review.audit_event_ids.append(event.id)
        save_auditoria_review(review)
        record_bus_audit_from_auditoria(
            action="audit_blocked",
            status="blocked",
            detail="AUDITORIA blocked protected unlock attempt.",
            route_id=review.reference if review.reference.startswith("cerebro_to_") else None,
        )
        raise PermissionError("protected_product_cannot_be_unlocked_by_auditoria")

    review.status = request.decision
    review.result = request.decision
    review.decision = request.decision
    review.auditor = request.auditor
    review.observations = [*review.observations, *request.observations]
    review.blockages = [*review.blockages, *request.blockages]
    review.criteria_results = request.criteria_results
    review.requires_ceo_decision = request.decision == AuditoriaReviewStatus.requires_ceo_decision
    review.decided_at = utc_now()
    action = "audit_decision_recorded"
    severity = "info"
    if request.decision == AuditoriaReviewStatus.approved:
        action = "audit_approved"
    elif request.decision == AuditoriaReviewStatus.blocked:
        action = "audit_blocked"
        severity = "high"
    elif request.decision in {
        AuditoriaReviewStatus.rejected,
        AuditoriaReviewStatus.requires_ceo_decision,
    }:
        severity = "medium"

    event = record_operational_audit_event(
        action=action,
        status=request.decision.value,
        detail=f"AUDITORIA decision recorded: {request.decision.value}.",
        review=review,
        severity=severity,
        metadata={"auditor": request.auditor},
    )
    review.audit_event_ids.append(event.id)
    saved = save_auditoria_review(review)
    record_bus_audit_from_auditoria(
        action=action,
        status=request.decision.value,
        detail=f"AUDITORIA decision for {saved.id}: {request.decision.value}.",
        route_id=saved.reference if saved.reference.startswith("cerebro_to_") else None,
    )
    return saved


def list_auditoria_queue() -> list[AuditoriaReview]:
    return [
        review
        for review in list_auditoria_reviews()
        if review.status
        in {
            AuditoriaReviewStatus.pending_review,
            AuditoriaReviewStatus.in_review,
            AuditoriaReviewStatus.requires_ceo_decision,
        }
    ]


def has_approved_auditoria_review_for(reference: str) -> bool:
    normalized = normalize_review_reference(reference)
    for review in list_auditoria_reviews():
        if review.status != AuditoriaReviewStatus.approved:
            continue
        if normalize_review_reference(review.reference) == normalized:
            return True
        target_id = normalize_review_reference(str(review.metadata.get("target_id", ""))) if hasattr(review, "metadata") else ""
        if target_id == normalized:
            return True
    return False


def get_auditoria_status() -> AuditoriaStatus:
    reviews = list_auditoria_reviews()
    return AuditoriaStatus(
        status="auditoria_operational_internal",
        pending_reviews=sum(1 for item in reviews if item.status == AuditoriaReviewStatus.pending_review),
        in_review=sum(1 for item in reviews if item.status == AuditoriaReviewStatus.in_review),
        approved_reviews=sum(1 for item in reviews if item.status == AuditoriaReviewStatus.approved),
        observed_reviews=sum(1 for item in reviews if item.status == AuditoriaReviewStatus.observed),
        rejected_reviews=sum(1 for item in reviews if item.status == AuditoriaReviewStatus.rejected),
        blocked_reviews=sum(1 for item in reviews if item.status == AuditoriaReviewStatus.blocked),
        requires_ceo_decision=sum(1 for item in reviews if item.status == AuditoriaReviewStatus.requires_ceo_decision),
        queue=len(list_auditoria_queue()),
        criteria=default_auditoria_criteria(),
        external_connection_enabled=False,
        runtime_connected=False,
    )


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
            status="pass" if registry.total == 14 else "fail",
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
