from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.cerebro import (
    CerebroDailyBrief,
    CerebroDecision,
    CerebroDecisionCreate,
    CerebroState,
    CerebroStatus,
    CerebroTask,
    CerebroTaskCreate,
    CerebroTaskStateUpdate,
)
from app.schemas.integration_bus import IntegrationDispatchRequest
from app.services.audit import create_audit_event
from app.services.integration_bus import dispatch_message, route_id_for_cerebro_target

CEREBRO_DECISIONS_TABLE = "cerebro_decisions"
CEREBRO_TASKS_TABLE = "cerebro_tasks"

PROTECTED_DESTINATIONS = {
    "doctor_contable_financiero_tributario": "DCFT",
    "centinela": "SENTINELA",
    "arsenal": "ARSENAL",
}

ALLOWED_DESTINATIONS = {
    "forja": "FORJA",
    "hermes": "HERMES",
    "creador_de_apis_y_skills": "CREADOR DE APIS Y SKILLS",
    "web_factory": "WEB FACTORY",
    "buscador_de_tendencias": "BUSCADOR DE TENDENCIAS",
    "pluma": "PLUMA",
    "lente": "LENTE",
    "marketing": "MARKETING",
    "marca_personal": "MARCA PERSONAL",
    "auditor": "AUDITORIA",
    "nube": "NUBE",
    "sniff_amazon": "SNIFF AMAZON",
    "comercio_autonomo": "COMERCIO AUTONOMO",
}

DESTINATION_ALIASES = {
    "auditoria": "auditor",
    "auditoría": "auditor",
    "apis": "creador_de_apis_y_skills",
    "api": "creador_de_apis_y_skills",
    "api_creator": "creador_de_apis_y_skills",
    "creador de apis y skills": "creador_de_apis_y_skills",
    "creador de apis": "creador_de_apis_y_skills",
    "creador_de_apis": "creador_de_apis_y_skills",
    "dcft": "doctor_contable_financiero_tributario",
    "doctor contable financiero tributario": "doctor_contable_financiero_tributario",
    "sentinela": "centinela",
    "sniff amazon": "sniff_amazon",
    "comercio autónomo": "comercio_autonomo",
    "comercio autonomo": "comercio_autonomo",
    "marca personal": "marca_personal",
    "web factory": "web_factory",
    "buscador de tendencias": "buscador_de_tendencias",
    "local agent": "local_agent",
    "sunat": "sunat",
    "produccion": "production",
    "producción": "production",
}

FORBIDDEN_DESTINATIONS = {
    "local_agent": "Local Agent is prohibited in this block.",
    "sunat": "SUNAT real is prohibited in this block.",
    "production": "Direct production operations are prohibited in this block.",
    "runtime_externo": "External runtime connections are prohibited in this block.",
    "external_api": "External API connections are prohibited in this block.",
}


class CerebroError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_destination(value: str) -> str:
    normalized = " ".join(str(value or "").strip().lower().split())
    normalized = DESTINATION_ALIASES.get(normalized, normalized)
    normalized = normalized.replace(" ", "_").replace("-", "_")
    return DESTINATION_ALIASES.get(normalized, normalized)


def ensure_cerebro_schema() -> None:
    initialize_database()
    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CEREBRO_DECISIONS_TABLE} (
                id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CEREBRO_TASKS_TABLE} (
                id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def actor_name(user: AuthenticatedUser) -> str:
    return user.email or user.name or user.id


def actor_role(user: AuthenticatedUser) -> str:
    return user.role.value.lower()


def safe_reason(value: str | None, fallback: str) -> str:
    reason = " ".join(str(value or "").strip().split())
    return reason or fallback


def audit_cerebro_action(
    *,
    action: str,
    actor: AuthenticatedUser,
    status: str,
    detail: str,
    state: CerebroState,
    destination: str | None = None,
    reason: str | None = None,
    requires_ceo_approval: bool = False,
    blocked: bool = False,
) -> str:
    metadata = {
        "actor": actor_name(actor),
        "role": actor_role(actor),
        "action": action,
        "destination": destination,
        "state": state.value,
        "reason": safe_reason(reason, "not_provided"),
        "requires_ceo_approval": requires_ceo_approval,
        "blocked": blocked,
        "timestamp": utc_now(),
        "external_connection_enabled": False,
        "runtime_connected": False,
    }
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.runtime,
            severity=AuditSeverity.high if blocked else AuditSeverity.info,
            source="cerebro.operational_runtime",
            action=action,
            status=status,
            detail=detail,
            metadata=metadata,
        )
    )
    return event.id


def insert_payload(table_name: str, item_id: str, payload: str) -> None:
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (item_id, payload, now, now),
        )
        connection.commit()


def update_payload(table_name: str, item_id: str, payload: str) -> None:
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {table_name}
            SET payload_json = {placeholder}, updated_at = {placeholder}
            WHERE id = {placeholder}
            """,
            (payload, now, item_id),
        )
        connection.commit()


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_cerebro_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [json.loads(row["payload_json"]) for row in rows]


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_cerebro_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    return json.loads(row["payload_json"]) if row else None


def list_cerebro_decisions() -> list[CerebroDecision]:
    return [CerebroDecision(**payload) for payload in fetch_payloads(CEREBRO_DECISIONS_TABLE)]


def list_cerebro_tasks() -> list[CerebroTask]:
    return [CerebroTask(**payload) for payload in fetch_payloads(CEREBRO_TASKS_TABLE)]


def create_cerebro_decision(
    request: CerebroDecisionCreate,
    actor: AuthenticatedUser,
) -> CerebroDecision:
    ensure_cerebro_schema()
    now = utc_now()
    decision_id = f"cerebro-decision-{uuid4()}"
    audit_event_id = audit_cerebro_action(
        action="create_decision",
        actor=actor,
        status=request.state.value,
        detail="CEREBRO prepared an internal CEO decision.",
        state=request.state,
        reason=request.reason,
        requires_ceo_approval=request.requires_ceo_approval,
    )
    decision = CerebroDecision(
        id=decision_id,
        title=request.title,
        description=request.description,
        priority=request.priority,
        state=request.state,
        requested_by=actor_name(actor),
        actor_role=actor_role(actor),
        reason=request.reason,
        requires_ceo_approval=request.requires_ceo_approval,
        audit_event_id=audit_event_id,
        created_at=now,
        updated_at=now,
    )
    insert_payload(CEREBRO_DECISIONS_TABLE, decision.id, decision.model_dump_json())
    return decision


def resolve_task_route(request: CerebroTaskCreate) -> tuple[str, str, CerebroState, bool, bool, str]:
    destination = normalize_destination(request.destination)
    if destination in PROTECTED_DESTINATIONS:
        label = PROTECTED_DESTINATIONS[destination]
        return (
            destination,
            label,
            CerebroState.blocked,
            True,
            True,
            f"{label} remains protected/no-touch and cannot receive operational tasks.",
        )
    if destination in FORBIDDEN_DESTINATIONS:
        return (
            destination,
            destination.replace("_", " ").upper(),
            CerebroState.blocked,
            True,
            True,
            FORBIDDEN_DESTINATIONS[destination],
        )
    if destination not in ALLOWED_DESTINATIONS:
        return (
            destination,
            destination.replace("_", " ").upper(),
            CerebroState.blocked,
            True,
            True,
            "Destination is not allowed for CEREBRO operational runtime.",
        )
    return (
        destination,
        ALLOWED_DESTINATIONS[destination],
        request.state or CerebroState.delegated,
        False,
        bool(request.requires_ceo_approval) if request.requires_ceo_approval is not None else False,
        "Internal task prepared without external runtime execution.",
    )


def create_cerebro_task(
    request: CerebroTaskCreate,
    actor: AuthenticatedUser,
) -> CerebroTask:
    ensure_cerebro_schema()
    now = utc_now()
    destination, label, state, blocked, requires_ceo, default_reason = resolve_task_route(request)
    reason = safe_reason(request.reason, default_reason)
    task_id = f"cerebro-task-{uuid4()}"
    bus_route_id = None
    bus_dispatch_id = None
    handler_result: dict = {}
    route_dispatched = False
    if not blocked:
        bus_route_id = route_id_for_cerebro_target(destination)
        if bus_route_id:
            dispatch = dispatch_message(
                IntegrationDispatchRequest(
                    route_id=bus_route_id,
                    subject=task_id,
                    payload={
                        "task_id": task_id,
                        "title": request.title,
                        "description": request.description,
                        "destination": destination,
                        "priority": request.priority,
                    },
                    metadata={
                        "source": "cerebro.operational_runtime",
                        "created_by": actor_name(actor),
                        "role": actor_role(actor),
                        "external_connection_enabled": False,
                        "runtime_connected": False,
                    },
                )
            )
            if dispatch:
                bus_dispatch_id = dispatch.id
                handler_result = dispatch.handler_result
                route_dispatched = True
    audit_event_id = audit_cerebro_action(
        action="create_task",
        actor=actor,
        status=state.value,
        detail=(
            "CEREBRO blocked a prohibited operational destination."
            if blocked
            else "CEREBRO delegated an internal task without external runtime execution."
        ),
        state=state,
        destination=destination,
        reason=reason,
        requires_ceo_approval=requires_ceo,
        blocked=blocked,
    )
    task = CerebroTask(
        id=task_id,
        title=request.title,
        description=request.description,
        destination=destination,
        destination_label=label,
        priority=request.priority,
        state=state,
        blocked=blocked,
        reason=reason,
        requested_by=actor_name(actor),
        actor_role=actor_role(actor),
        requires_ceo_approval=requires_ceo,
        route_dispatched=route_dispatched,
        bus_route_id=bus_route_id,
        bus_dispatch_id=bus_dispatch_id,
        handler_result=handler_result,
        audit_event_id=audit_event_id,
        created_at=now,
        updated_at=now,
    )
    insert_payload(CEREBRO_TASKS_TABLE, task.id, task.model_dump_json())
    return task


def update_cerebro_task_state(
    task_id: str,
    request: CerebroTaskStateUpdate,
    actor: AuthenticatedUser,
) -> CerebroTask:
    payload = fetch_payload(CEREBRO_TASKS_TABLE, task_id)
    if payload is None:
        raise CerebroError(
            status_code=404,
            detail={"error": "cerebro_task_not_found", "task_id": task_id},
        )

    task = CerebroTask(**payload)
    if task.blocked and request.state != CerebroState.blocked:
        raise CerebroError(
            status_code=400,
            detail={
                "error": "blocked_task_state_locked",
                "task_id": task.id,
                "destination": task.destination,
                "state": task.state.value,
            },
        )

    task.state = request.state
    task.reason = safe_reason(request.reason, task.reason)
    task.updated_at = utc_now()
    task.audit_event_id = audit_cerebro_action(
        action="update_task_state",
        actor=actor,
        status=task.state.value,
        detail="CEREBRO task state was updated internally.",
        state=task.state,
        destination=task.destination,
        reason=task.reason,
        requires_ceo_approval=task.requires_ceo_approval,
        blocked=task.blocked,
    )
    update_payload(CEREBRO_TASKS_TABLE, task.id, task.model_dump_json())
    return task


def get_cerebro_status() -> CerebroStatus:
    ensure_cerebro_schema()
    decisions = list_cerebro_decisions()
    tasks = list_cerebro_tasks()
    blocked_tasks = [task for task in tasks if task.blocked or task.state == CerebroState.blocked]
    pending_decisions = [
        decision
        for decision in decisions
        if decision.state
        in {CerebroState.draft, CerebroState.proposed, CerebroState.waiting_ceo}
    ]
    return CerebroStatus(
        status="cerebro_operational_internal",
        mode="internal_backend_control_center_only",
        role="Chief of Staff / Jefe de Gabinete IA",
        allowed_departments=list(ALLOWED_DESTINATIONS.values()),
        protected_targets=list(PROTECTED_DESTINATIONS.values()),
        decisions=len(decisions),
        tasks=len(tasks),
        blocked_tasks=len(blocked_tasks),
        pending_decisions=len(pending_decisions),
        generated_at=utc_now(),
    )


def build_brief(brief_type: str) -> CerebroDailyBrief:
    ensure_cerebro_schema()
    decisions = list_cerebro_decisions()
    tasks = list_cerebro_tasks()
    blocked = [task for task in tasks if task.blocked or task.state == CerebroState.blocked]
    pending = [
        decision
        for decision in decisions
        if decision.state
        in {CerebroState.draft, CerebroState.proposed, CerebroState.waiting_ceo}
    ]

    if brief_type == "morning":
        headline = "Reunión de mañana con CEREBRO"
        summary = (
            "CEREBRO lee el estado interno, prepara prioridades y escala al CEO "
            "lo que requiere decisión humana."
        )
    elif brief_type == "evening":
        headline = "Reunión de tarde con CEREBRO"
        summary = (
            "CEREBRO resume tareas internas, bloqueos y decisiones que quedan "
            "para el siguiente ciclo."
        )
    else:
        headline = "Resumen ejecutivo CEREBRO"
        summary = (
            "CEREBRO opera dentro del backend/control center, sin apps protegidas "
            "ni runtimes externos."
        )

    return CerebroDailyBrief(
        type=brief_type,
        headline=headline,
        summary=summary,
        decisions=pending[:8],
        tasks=tasks[:8],
        blocked=blocked[:8],
        allowed_departments=list(ALLOWED_DESTINATIONS.values()),
        protected_targets=list(PROTECTED_DESTINATIONS.values()),
        requires_ceo_approval=bool(pending or blocked),
        generated_at=utc_now(),
    )
