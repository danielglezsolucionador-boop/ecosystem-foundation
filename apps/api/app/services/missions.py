from __future__ import annotations

from datetime import UTC, datetime
import json
from uuid import uuid4

from app.schemas.audit import AuditoriaCriterion, AuditoriaObjectType, AuditoriaReviewCreate
from app.schemas.auth import AuthenticatedUser
from app.schemas.cerebro import (
    CerebroMissionCreate,
    CerebroMissionState,
    CerebroState,
    CerebroTaskCreate,
)
from app.schemas.missions import (
    MissionAssignment,
    MissionAuditReviewLink,
    MissionDailyReport,
    MissionForgeRequest,
    MissionLoopAssignRequest,
    MissionLoopAuditRequest,
    MissionLoopBlockRequest,
    MissionLoopCompleteRequest,
    MissionLoopCreate,
    MissionLoopDispatchRequest,
    MissionLoopEvent,
    MissionLoopForjaRequest,
    MissionLoopMission,
    MissionLoopPlanRequest,
    MissionLoopStatus,
    MissionLoopStep,
    MissionLoopUpdateRequest,
    MissionReport,
    MissionRevenueLink,
    MissionTimeline,
)
from app.schemas.revenue import RevenueOpportunityCreate
from app.services.audit import create_auditoria_review
from app.services.cerebro import (
    CEREBRO_MISSIONS_TABLE,
    CerebroError,
    audit_cerebro_action,
    create_cerebro_task,
    create_mission,
    fetch_payload,
    fetch_payloads,
    list_missions,
    update_payload,
)
from app.services.revenue import create_opportunity

TERMINAL_STATUSES = {
    MissionLoopStatus.completed,
    MissionLoopStatus.blocked,
    MissionLoopStatus.rejected,
    MissionLoopStatus.failed,
}
PROHIBITED_MISSION_ACTIONS = {
    "activate_dcft",
    "activate_sentinela",
    "activate_arsenal",
    "activate_sunat",
    "connect_external_api",
    "deploy_direct",
    "real_payment",
}
DEPARTMENT_KEYWORDS = {
    "pluma": "PLUMA",
    "lente": "LENTE",
    "marketing": "MARKETING",
    "marca personal": "MARCA PERSONAL",
    "forja": "FORJA",
    "auditoria": "AUDITORIA",
    "auditoría": "AUDITORIA",
    "nube": "NUBE",
    "cerebro": "CEREBRO",
    "web factory": "WEB FACTORY",
    "api": "CREADOR_DE_APIS_Y_SKILLS",
    "apis": "CREADOR_DE_APIS_Y_SKILLS",
    "skills": "CREADOR_DE_APIS_Y_SKILLS",
    "tendencias": "BUSCADOR_DE_TENDENCIAS",
    "amazon": "SNIFF_AMAZON",
    "comercio": "COMERCIO_AUTONOMO",
    "arsenal": "ARSENAL",
}
REVENUE_TERMS = (
    "vende",
    "venta",
    "ingreso",
    "ingresos",
    "revenue",
    "roi",
    "comercial",
    "monetizar",
    "margen",
)


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def actor_label(actor: AuthenticatedUser) -> str:
    return actor.name or actor.email or actor.role.value


def normalize_text(value: object) -> str:
    return str(value or "").strip().lower()


def mission_error(status_code: int, detail: dict) -> CerebroError:
    return CerebroError(status_code=status_code, detail=detail)


def inferred_departments(request: MissionLoopCreate) -> list[str]:
    seen: list[str] = []
    for department in request.involved_departments:
        normalized = department.strip().upper()
        if normalized and normalized not in seen:
            seen.append(normalized)

    haystack = normalize_text(f"{request.title} {request.objective or ''} {request.ceo_instruction}")
    for keyword, department in DEPARTMENT_KEYWORDS.items():
        if keyword in haystack and department not in seen:
            seen.append(department)

    if not seen:
        seen.extend(["CEREBRO", "AUDITORIA"])
    if "AUDITORIA" not in seen:
        seen.append("AUDITORIA")
    return seen[:10]


def has_revenue_signal(request: MissionLoopCreate) -> bool:
    haystack = normalize_text(f"{request.title} {request.objective or ''} {request.ceo_instruction}")
    return bool(request.revenue_goal_link or request.ecommerce_goal_link or any(term in haystack for term in REVENUE_TERMS))


def default_expected_impact(request: MissionLoopCreate) -> str:
    if request.expected_business_impact != "unknown":
        return request.expected_business_impact
    if has_revenue_signal(request):
        return "Impacto comercial por estimar; Revenue OS debe calcular ROI antes de gasto real."
    return "unknown"


def default_steps(title_prefix: str, departments: list[str], now: str) -> list[MissionLoopStep]:
    steps = [
        MissionLoopStep(
            id=f"mission_step_{uuid4()}",
            title=f"{title_prefix}: entender orden CEO",
            owner_department="CEREBRO",
            status="ready",
            notes="CEREBRO convierte la orden en misión interna.",
            created_at=now,
            updated_at=now,
        )
    ]
    for department in departments[:8]:
        if department == "CEREBRO":
            continue
        steps.append(
            MissionLoopStep(
                id=f"mission_step_{uuid4()}",
                title=f"Preparar trabajo con {department}",
                owner_department=department,
                status="pending",
                notes="Preparado sin runtime externo ni ejecución real.",
                created_at=now,
                updated_at=now,
            )
        )
    steps.append(
        MissionLoopStep(
            id=f"mission_step_{uuid4()}",
            title="Reportar estado al CEO",
            owner_department="CEREBRO",
            status="pending",
            notes="El CEO recibe avance, bloqueo y siguiente acción.",
            created_at=now,
            updated_at=now,
        )
    )
    return steps


def default_next_action(status_value: str) -> str:
    if status_value == MissionLoopStatus.needs_clarification.value:
        return "CEO, aclara objetivo, departamento o resultado esperado."
    if status_value == MissionLoopStatus.waiting_ceo_approval.value:
        return "CEO, esto requiere tu decisión antes de avanzar."
    if status_value == MissionLoopStatus.waiting_audit.value:
        return "AUDITORIA debe revisar antes de continuar."
    if status_value == MissionLoopStatus.waiting_forge.value:
        return "FORJA tiene una solicitud preparada; sin ejecución externa."
    if status_value == MissionLoopStatus.completed.value:
        return "Revisar reporte final de misión."
    if status_value == MissionLoopStatus.blocked.value:
        return "Resolver bloqueo o mantener protegido."
    return "Planificar, asignar y reportar avance al CEO."


def mission_status_from_payload(payload: dict) -> str:
    raw = str(payload.get("status") or payload.get("state") or MissionLoopStatus.created.value)
    try:
        return MissionLoopStatus(raw).value
    except ValueError:
        return MissionLoopStatus.needs_clarification.value


def normalized_payload(payload: dict) -> dict:
    normalized = dict(payload)
    status_value = mission_status_from_payload(normalized)
    now = utc_now()
    normalized.setdefault("ceo_instruction", normalized.get("objective") or normalized.get("title") or "")
    normalized.setdefault("source", normalized.get("origin") or "ceo_instruction")
    normalized.setdefault("expected_business_impact", "unknown")
    normalized.setdefault("revenue_goal_link", None)
    normalized.setdefault("ecommerce_goal_link", None)
    normalized.setdefault("approval_reason", normalized.get("authority_reason") or "not_required")
    normalized["status"] = status_value
    normalized["state"] = status_value
    normalized.setdefault("current_phase", status_value)
    normalized.setdefault("next_action", default_next_action(status_value))
    normalized.setdefault("deadline", None)
    normalized.setdefault("steps", [])
    normalized.setdefault("assignments", [])
    normalized.setdefault("events", [])
    normalized.setdefault("audit_reviews", [])
    normalized.setdefault("forge_requests", [])
    normalized.setdefault("revenue_links", [])
    normalized.setdefault("reports", [])
    normalized.setdefault("audit_trail", [])
    normalized.setdefault("technical_status", "prepared")
    normalized.setdefault("external_connection_enabled", False)
    normalized.setdefault("runtime_connected", False)
    normalized.setdefault("payment_connected", False)
    normalized.setdefault("sunat_enabled", False)
    normalized.setdefault("local_agent_enabled", False)
    normalized.setdefault("created_at", now)
    normalized.setdefault("updated_at", now)
    return normalized


def loop_projection(payload: dict) -> dict:
    normalized = normalized_payload(payload)
    return {
        "id": normalized["id"],
        "title": normalized["title"],
        "objective": normalized["objective"],
        "ceo_instruction": normalized["ceo_instruction"],
        "source": normalized["source"],
        "leader_department": normalized.get("leader_department") or "CEREBRO",
        "involved_departments": normalized.get("involved_departments") or [],
        "priority": normalized.get("priority") or "p1",
        "action_type": normalized.get("action_type") or "internal_mission",
        "expected_business_impact": normalized.get("expected_business_impact") or "unknown",
        "revenue_goal_link": normalized.get("revenue_goal_link"),
        "ecommerce_goal_link": normalized.get("ecommerce_goal_link"),
        "requires_money": bool(normalized.get("requires_money", False)),
        "requires_ceo_approval": bool(normalized.get("requires_ceo_approval", False)),
        "approval_reason": normalized.get("approval_reason") or "not_required",
        "status": normalized["status"],
        "current_phase": normalized.get("current_phase") or normalized["status"],
        "next_action": normalized.get("next_action") or default_next_action(normalized["status"]),
        "deadline": normalized.get("deadline"),
        "steps": normalized.get("steps") or [],
        "assignments": normalized.get("assignments") or [],
        "events": normalized.get("events") or [],
        "audit_reviews": normalized.get("audit_reviews") or [],
        "forge_requests": normalized.get("forge_requests") or [],
        "revenue_links": normalized.get("revenue_links") or [],
        "reports": normalized.get("reports") or [],
        "audit_trail": normalized.get("audit_trail") or [],
        "technical_status": normalized.get("technical_status") or "prepared",
        "external_connection_enabled": False,
        "runtime_connected": False,
        "payment_connected": False,
        "sunat_enabled": False,
        "local_agent_enabled": False,
        "created_at": normalized["created_at"],
        "updated_at": normalized["updated_at"],
    }


def mission_from_payload(payload: dict) -> MissionLoopMission:
    return MissionLoopMission(**loop_projection(payload))


def list_mission_payloads() -> list[dict]:
    list_missions()
    payloads: list[dict] = []
    for payload in fetch_payloads(CEREBRO_MISSIONS_TABLE):
        try:
            payloads.append(normalized_payload(payload))
        except Exception:
            continue
    return payloads


def get_mission_payload(mission_id: str) -> dict:
    payload = fetch_payload(CEREBRO_MISSIONS_TABLE, mission_id)
    if payload is None:
        raise mission_error(404, {"error": "mission_not_found", "mission_id": mission_id})
    return normalized_payload(payload)


def save_mission_payload(payload: dict) -> dict:
    normalized = normalized_payload(payload)
    normalized["updated_at"] = utc_now()
    update_payload(CEREBRO_MISSIONS_TABLE, normalized["id"], json.dumps(normalized, ensure_ascii=False))
    return normalized


def append_event(
    payload: dict,
    *,
    event_type: str,
    actor: AuthenticatedUser,
    message: str,
    status_value: str | None = None,
    department: str = "CEREBRO",
) -> dict:
    status_value = status_value or mission_status_from_payload(payload)
    audit_event_id = audit_cerebro_action(
        action=f"mission_loop_{event_type}",
        actor=actor,
        status=status_value,
        detail=message,
        state=CerebroState.delegated,
        destination=department,
        reason=payload.get("objective") or payload.get("title"),
        requires_ceo_approval=bool(payload.get("requires_ceo_approval", False)),
    )
    event = MissionLoopEvent(
        id=f"mission_event_{uuid4()}",
        mission_id=payload["id"],
        type=event_type,
        actor=actor_label(actor),
        department=department,
        message=message,
        status=status_value,
        audit_event_id=audit_event_id,
        created_at=utc_now(),
    )
    payload.setdefault("events", []).insert(0, event.model_dump(mode="json"))
    payload.setdefault("audit_trail", []).insert(0, audit_event_id)
    return payload


def set_status(payload: dict, status_value: MissionLoopStatus, *, current_phase: str | None = None, next_action: str | None = None) -> dict:
    payload["status"] = status_value.value
    payload["state"] = status_value.value
    payload["current_phase"] = current_phase or status_value.value
    payload["next_action"] = next_action or default_next_action(status_value.value)
    return payload


def link_revenue_if_needed(payload: dict, request: MissionLoopCreate, actor: AuthenticatedUser) -> dict:
    if not has_revenue_signal(request):
        return payload
    opportunity = create_opportunity(
        RevenueOpportunityCreate(
            title=f"Misión: {request.title}",
            origin="mission_execution_loop",
            department=request.leader_department,
            action_type="organic" if not request.requires_money else request.action_type,
            investment_usd=request.investment_required or 0,
            expected_revenue_usd=request.expected_revenue,
            risk=request.risk,
            ecommerce_separate=request.ecommerce_separate,
            recommendation="Calcular ROI antes de gasto real. Sin pagos ni ventas reales.",
        ),
        actor,
    )
    link = MissionRevenueLink(
        id=f"mission_revenue_link_{uuid4()}",
        mission_id=payload["id"],
        opportunity_id=opportunity.id,
        goal_scope="ecommerce" if request.ecommerce_separate else "global",
        economic_impact=payload.get("expected_business_impact") or "unknown",
        created_at=utc_now(),
    )
    payload.setdefault("revenue_links", []).insert(0, link.model_dump(mode="json"))
    payload["revenue_goal_link"] = payload.get("revenue_goal_link") or (
        "ecommerce_usd_10000" if request.ecommerce_separate else "global_usd_6000"
    )
    return payload


def create_loop_mission(request: MissionLoopCreate, actor: AuthenticatedUser) -> MissionLoopMission:
    departments = inferred_departments(request)
    expected_impact = default_expected_impact(request)
    objective = request.objective or request.ceo_instruction
    unclear = len(normalize_text(request.ceo_instruction)) < 8 or not objective.strip()
    action_type = normalize_text(request.action_type).replace(" ", "_")
    prohibited = action_type in PROHIBITED_MISSION_ACTIONS
    state = (
        CerebroMissionState.needs_clarification
        if unclear
        else CerebroMissionState.waiting_ceo_approval
        if prohibited
        else None
    )
    core = create_mission(
        CerebroMissionCreate(
            title=request.title,
            objective=objective,
            origin=request.source,
            leader_department=request.leader_department,
            involved_departments=departments,
            priority=request.priority,
            action_type=action_type or "internal_mission",
            estimated_economic_impact=request.expected_revenue or 0,
            relation_to_monthly_goal=(
                expected_impact if expected_impact != "unknown" else None
            ),
            state=state,
            risks=[request.risk],
            requires_money=request.requires_money,
            requires_ceo_approval=(
                True
                if prohibited
                else request.requires_ceo_approval
            ),
            expected_report="Reporte CEO con avance, bloqueo, auditoría, FORJA y revenue si aplica.",
            investment_required=request.investment_required,
            expected_revenue=request.expected_revenue or 0,
            ecommerce_separate=request.ecommerce_separate,
        ),
        actor,
    )
    payload = normalized_payload(core.model_dump(mode="json"))
    payload.update(
        {
            "ceo_instruction": request.ceo_instruction,
            "source": request.source,
            "expected_business_impact": expected_impact,
            "revenue_goal_link": request.revenue_goal_link,
            "ecommerce_goal_link": request.ecommerce_goal_link,
            "approval_reason": (
                "protected_or_external_action_blocked_in_block_l"
                if prohibited
                else request.approval_reason
                or payload.get("authority_reason")
                or "not_required"
            ),
            "deadline": request.deadline,
            "assignments": [],
            "events": [],
            "audit_reviews": [],
            "forge_requests": [],
            "revenue_links": [],
            "reports": [],
            "payment_connected": False,
            "local_agent_enabled": False,
        }
    )
    if unclear:
        set_status(payload, MissionLoopStatus.needs_clarification)
    elif prohibited:
        set_status(
            payload,
            MissionLoopStatus.waiting_ceo_approval,
            next_action="CEO debe decidir en otro frente; esta misión no ejecuta acción protegida.",
        )
    elif core.requires_ceo_approval:
        set_status(
            payload,
            MissionLoopStatus.waiting_ceo_approval,
            next_action="CEO, esto requiere tu decisión antes de avanzar.",
        )
    else:
        set_status(payload, MissionLoopStatus.created, next_action="Planificar misión y asignar departamentos.")
    append_event(
        payload,
        event_type="created",
        actor=actor,
        message="CEO -> CEREBRO: misión interna registrada sin ejecución externa.",
        status_value=payload["status"],
    )
    payload = link_revenue_if_needed(payload, request, actor)
    saved = save_mission_payload(payload)
    return mission_from_payload(saved)


def list_loop_missions() -> list[MissionLoopMission]:
    missions: list[MissionLoopMission] = []
    for payload in list_mission_payloads():
        try:
            missions.append(mission_from_payload(payload))
        except Exception:
            continue
    return missions


def get_loop_mission(mission_id: str) -> MissionLoopMission:
    return mission_from_payload(get_mission_payload(mission_id))


def plan_loop_mission(
    mission_id: str,
    request: MissionLoopPlanRequest,
    actor: AuthenticatedUser,
) -> MissionLoopMission:
    payload = get_mission_payload(mission_id)
    departments = request.involved_departments or payload.get("involved_departments") or ["CEREBRO", "AUDITORIA"]
    now = utc_now()
    if request.steps:
        steps = [
            MissionLoopStep(
                id=f"mission_step_{uuid4()}",
                title=step,
                owner_department=departments[index % len(departments)],
                status="pending",
                notes="Paso planificado por CEREBRO; sin ejecución real.",
                created_at=now,
                updated_at=now,
            )
            for index, step in enumerate(request.steps)
        ]
    else:
        steps = default_steps("Mission Loop", departments, now)
    payload["steps"] = [step.model_dump(mode="json") for step in steps]
    payload["involved_departments"] = departments
    set_status(
        payload,
        MissionLoopStatus.planned,
        next_action=request.next_action or "Asignar departamentos y preparar auditoría.",
    )
    append_event(
        payload,
        event_type="planned",
        actor=actor,
        message="CEREBRO planificó la misión interna.",
        status_value=MissionLoopStatus.planned.value,
    )
    return mission_from_payload(save_mission_payload(payload))


def assign_loop_mission(
    mission_id: str,
    request: MissionLoopAssignRequest,
    actor: AuthenticatedUser,
) -> MissionLoopMission:
    payload = get_mission_payload(mission_id)
    departments = [department for department in request.departments if department.strip()]
    if request.department:
        departments.insert(0, request.department)
    departments = list(dict.fromkeys(department.strip().upper() for department in departments if department.strip()))
    if not departments:
        raise mission_error(400, {"error": "mission_assignment_department_required"})
    now = utc_now()
    for department in departments:
        assignment = MissionAssignment(
            id=f"mission_assignment_{uuid4()}",
            mission_id=mission_id,
            department=department,
            instruction=request.instruction,
            status="assigned",
            created_at=now,
        )
        payload.setdefault("assignments", []).insert(0, assignment.model_dump(mode="json"))
    existing_departments = payload.setdefault("involved_departments", [])
    for department in departments:
        if department not in existing_departments:
            existing_departments.append(department)
    set_status(payload, MissionLoopStatus.assigned, next_action="Despachar trabajo interno y esperar avances.")
    append_event(
        payload,
        event_type="assigned",
        actor=actor,
        department=",".join(departments),
        message=f"CEREBRO asignó misión a {', '.join(departments)}.",
        status_value=MissionLoopStatus.assigned.value,
    )
    return mission_from_payload(save_mission_payload(payload))


def dispatch_loop_mission(
    mission_id: str,
    request: MissionLoopDispatchRequest,
    actor: AuthenticatedUser,
) -> MissionLoopMission:
    payload = get_mission_payload(mission_id)
    department = request.department.strip().upper()
    payload.setdefault("executed_actions", []).insert(0, f"dispatch_prepared:{department}")
    payload.setdefault("pending_actions", []).insert(0, f"{department}: {request.instruction}")
    set_status(payload, MissionLoopStatus.in_progress, next_action="Esperar respuesta de departamento y auditar.")
    append_event(
        payload,
        event_type="dispatched",
        actor=actor,
        department=department,
        message="CEREBRO despachó una instrucción interna preparada; sin runtime externo.",
        status_value=MissionLoopStatus.in_progress.value,
    )
    return mission_from_payload(save_mission_payload(payload))


def parse_audit_criteria(raw_criteria: list[str]) -> list[AuditoriaCriterion]:
    criteria: list[AuditoriaCriterion] = []
    for raw in raw_criteria:
        try:
            criteria.append(AuditoriaCriterion(raw))
        except ValueError:
            continue
    return criteria or [
        AuditoriaCriterion.functional_quality,
        AuditoriaCriterion.security,
        AuditoriaCriterion.ceo_standard,
        AuditoriaCriterion.operational_risk,
    ]


def request_loop_audit(
    mission_id: str,
    request: MissionLoopAuditRequest,
    actor: AuthenticatedUser,
) -> MissionLoopMission:
    payload = get_mission_payload(mission_id)
    review = create_auditoria_review(
        AuditoriaReviewCreate(
            object_type=AuditoriaObjectType.cerebro_task,
            reference=mission_id,
            source="mission_execution_loop",
            priority=request.priority,
            criteria=parse_audit_criteria(request.criteria),
            observations=[
                request.reason,
                "Revisión interna: sin APIs externas, sin secretos y sin ejecución real.",
            ],
            metadata={
                "mission_id": mission_id,
                "external_connection_enabled": False,
                "runtime_connected": False,
            },
        )
    )
    link = MissionAuditReviewLink(
        id=f"mission_audit_review_{uuid4()}",
        mission_id=mission_id,
        review_id=review.id,
        status=review.status.value,
        created_at=utc_now(),
    )
    payload.setdefault("audit_reviews", []).insert(0, link.model_dump(mode="json"))
    set_status(payload, MissionLoopStatus.waiting_audit, next_action="AUDITORIA debe revisar antes de pasar a FORJA o CEO.")
    append_event(
        payload,
        event_type="audit_requested",
        actor=actor,
        department="AUDITORIA",
        message="CEREBRO pidió auditoría interna de la misión.",
        status_value=MissionLoopStatus.waiting_audit.value,
    )
    return mission_from_payload(save_mission_payload(payload))


def send_loop_to_forja(
    mission_id: str,
    request: MissionLoopForjaRequest,
    actor: AuthenticatedUser,
) -> MissionLoopMission:
    payload = get_mission_payload(mission_id)
    task = create_cerebro_task(
        CerebroTaskCreate(
            title=request.title or f"FORJA preparada para {payload['title']}",
            description=request.instruction,
            destination="forja",
            priority=request.priority,
            requires_ceo_approval=False,
            reason="Solicitud interna preparada por Mission Execution Loop; sin tocar FORJA externa.",
        ),
        actor,
    )
    forge_request = MissionForgeRequest(
        id=f"mission_forge_request_{uuid4()}",
        mission_id=mission_id,
        task_id=task.id,
        status="prepared",
        technical_status="prepared_no_external_forja_execution",
        created_at=utc_now(),
    )
    payload.setdefault("forge_requests", []).insert(0, forge_request.model_dump(mode="json"))
    set_status(payload, MissionLoopStatus.waiting_forge, next_action="FORJA tiene solicitud interna preparada; revisar con AUDITORIA.")
    append_event(
        payload,
        event_type="sent_to_forja",
        actor=actor,
        department="FORJA",
        message="CEREBRO preparó solicitud para FORJA; no se tocó FORJA externa.",
        status_value=MissionLoopStatus.waiting_forge.value,
    )
    return mission_from_payload(save_mission_payload(payload))


def update_loop_mission(
    mission_id: str,
    request: MissionLoopUpdateRequest,
    actor: AuthenticatedUser,
) -> MissionLoopMission:
    payload = get_mission_payload(mission_id)
    if request.status:
        set_status(payload, request.status, next_action=request.next_action)
    elif request.next_action:
        payload["next_action"] = request.next_action
    update = {
        "id": f"mission_update_{uuid4()}",
        "mission_id": mission_id,
        "department": request.department,
        "status": payload["status"],
        "message": request.message,
        "created_at": utc_now(),
    }
    payload.setdefault("updates", []).insert(0, update)
    append_event(
        payload,
        event_type="updated",
        actor=actor,
        department=request.department,
        message=request.message,
        status_value=payload["status"],
    )
    return mission_from_payload(save_mission_payload(payload))


def complete_loop_mission(
    mission_id: str,
    request: MissionLoopCompleteRequest,
    actor: AuthenticatedUser,
) -> MissionLoopMission:
    payload = get_mission_payload(mission_id)
    report = MissionReport(
        id=f"mission_report_{uuid4()}",
        mission_id=mission_id,
        type="ceo_report",
        summary=request.summary,
        status=MissionLoopStatus.completed.value,
        created_at=utc_now(),
    )
    payload.setdefault("reports", []).insert(0, report.model_dump(mode="json"))
    if request.evidence:
        payload.setdefault("executed_actions", []).insert(0, f"evidence:{request.evidence}")
    set_status(payload, MissionLoopStatus.completed, next_action="CEO puede revisar el reporte final.")
    append_event(
        payload,
        event_type="completed",
        actor=actor,
        message="CEREBRO cerró la misión con reporte CEO.",
        status_value=MissionLoopStatus.completed.value,
    )
    return mission_from_payload(save_mission_payload(payload))


def block_loop_mission(
    mission_id: str,
    request: MissionLoopBlockRequest,
    actor: AuthenticatedUser,
) -> MissionLoopMission:
    payload = get_mission_payload(mission_id)
    payload.setdefault("risks", []).insert(0, request.reason)
    set_status(payload, MissionLoopStatus.blocked, next_action="CEO, revisar bloqueo o mantener protegido.")
    append_event(
        payload,
        event_type="blocked",
        actor=actor,
        department=request.blocked_by,
        message=request.reason,
        status_value=MissionLoopStatus.blocked.value,
    )
    return mission_from_payload(save_mission_payload(payload))


def mission_timeline(mission_id: str) -> MissionTimeline:
    payload = get_mission_payload(mission_id)
    timeline: list[dict] = []
    for key in ("events", "assignments", "audit_reviews", "forge_requests", "revenue_links", "reports", "updates"):
        for entry in payload.get(key, []) or []:
            item = dict(entry)
            item["timeline_type"] = key
            item.setdefault("created_at", payload.get("updated_at") or utc_now())
            timeline.append(item)
    timeline.sort(key=lambda item: str(item.get("created_at") or ""), reverse=True)
    return MissionTimeline(
        mission_id=mission_id,
        timeline=timeline,
        external_connection_enabled=False,
        runtime_connected=False,
        generated_at=utc_now(),
    )


def active_loop_missions() -> list[MissionLoopMission]:
    return [
        mission
        for mission in list_loop_missions()
        if mission.status not in TERMINAL_STATUSES
    ][:24]


def get_mission_daily_report() -> MissionDailyReport:
    missions = list_loop_missions()
    active = [mission for mission in missions if mission.status not in TERMINAL_STATUSES]
    today = utc_now()[:10]
    completed_today = [
        mission
        for mission in missions
        if mission.status == MissionLoopStatus.completed and mission.updated_at.startswith(today)
    ]
    waiting_audit = [mission for mission in missions if mission.status == MissionLoopStatus.waiting_audit]
    waiting_forge = [mission for mission in missions if mission.status == MissionLoopStatus.waiting_forge]
    waiting_ceo = [mission for mission in missions if mission.status == MissionLoopStatus.waiting_ceo_approval]
    unknown_impact = [mission for mission in missions if mission.expected_business_impact == "unknown"]
    return MissionDailyReport(
        status="mission_execution_loop_operational_internal",
        active_missions=len(active),
        waiting_audit=len(waiting_audit),
        waiting_forge=len(waiting_forge),
        waiting_ceo_approval=len(waiting_ceo),
        completed_today=len(completed_today),
        economic_impact_unknown=len(unknown_impact),
        morning_summary="CEO -> CEREBRO -> misión -> departamentos -> auditoría -> FORJA si falta construcción.",
        midday_summary="CEREBRO mantiene próximos pasos, bloqueos y evidencia sin runtime externo.",
        evening_summary="CEREBRO reporta lo hecho, lo bloqueado y lo que requiere decisión CEO.",
        missions=active[:8],
        external_connection_enabled=False,
        runtime_connected=False,
        generated_at=utc_now(),
    )
