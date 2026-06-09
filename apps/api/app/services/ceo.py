from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from dataclasses import dataclass, field
from datetime import UTC, datetime
import json
import time
from typing import Any

from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.ceo import (
    CeoDailyAction,
    CeoDailyCenter,
    CeoDailyItem,
    CeoDailyView,
    CeoDecisionActionRequest,
)
from app.schemas.governance import DecisionTransitionRequest, GovernanceDecision, GovernanceRole
from app.services.audit import create_audit_event
from app.services.cerebro import build_brief, get_cerebro_status, list_cerebro_decisions, list_cerebro_tasks
from app.services.audit import get_auditoria_status, list_auditoria_reviews
from app.services.governance import (
    GovernanceError,
    approve_decision,
    get_decision,
    get_governance_report,
    list_decisions,
    reject_decision,
)
from app.services.integration_bus import get_bus_overview, get_bus_status, list_bus_audit
from app.services.nube import get_nube_status

PROTECTED_TARGETS = {
    "dcft",
    "doctor_contable_financiero_tributario",
    "doctor_contable",
    "sentinela",
    "centinela",
    "arsenal",
}
PROHIBITED_ACTIONS = {
    "activate_dcft",
    "activate_sentinela",
    "activate_arsenal",
    "activate_sunat",
    "activate_local_agent",
    "deploy_direct",
    "connect_external_api",
    "connect_runtime",
    "touch_nube_local",
}
INTERNAL_TIMEOUT_SECONDS = 1.2
_SNAPSHOT_EXECUTOR = ThreadPoolExecutor(max_workers=6, thread_name_prefix="ceo_daily_center")


@dataclass
class CeoSnapshot:
    decisions: list[GovernanceDecision] = field(default_factory=list)
    tasks: list[Any] = field(default_factory=list)
    routes: list[Any] = field(default_factory=list)
    auditoria_reviews: list[Any] = field(default_factory=list)
    governance_report: Any | None = None
    cerebro_status: dict[str, Any] = field(default_factory=dict)
    bus_status: dict[str, Any] = field(default_factory=dict)
    auditoria_status: dict[str, Any] = field(default_factory=dict)
    nube_status: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    elapsed_ms: int = 0


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def item(
    *,
    item_id: str,
    title: str,
    body: str,
    status: str,
    source: str,
    meta: str | None = None,
    requires_ceo_decision: bool = False,
    blocked: bool = False,
) -> CeoDailyItem:
    return CeoDailyItem(
        id=item_id,
        title=title,
        body=body,
        status=status,
        source=source,
        meta=meta,
        requires_ceo_decision=requires_ceo_decision,
        blocked=blocked,
    )


def safe_model_dump(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    if isinstance(model, dict):
        return model
    return {}


def read_value(source: Any, name: str, default: Any = "unknown") -> Any:
    if isinstance(source, dict):
        return source.get(name, default)
    return getattr(source, name, default)


def safe_snapshot_call(
    label: str,
    callback,
    default: Any,
    warnings: list[str],
    timeout_seconds: float | None = None,
) -> Any:
    timeout_seconds = INTERNAL_TIMEOUT_SECONDS if timeout_seconds is None else timeout_seconds
    future = _SNAPSHOT_EXECUTOR.submit(callback)
    try:
        return future.result(timeout=timeout_seconds)
    except FuturesTimeoutError:
        future.cancel()
        warnings.append(f"{label}_timeout_fallback")
        return default
    except Exception:
        warnings.append(f"{label}_fallback")
        return default


def build_ceo_snapshot() -> CeoSnapshot:
    started = time.perf_counter()
    warnings: list[str] = []
    governance_report = safe_snapshot_call("governance_report", get_governance_report, None, warnings)
    decisions = (
        list(getattr(governance_report, "pending_decisions", []))[:12]
        if governance_report is not None
        else safe_snapshot_call("governance_decisions", pending_governance_decisions, [], warnings)[:12]
    )
    tasks = safe_snapshot_call("cerebro_tasks", list_cerebro_tasks, [], warnings)[:16]
    bus_overview = safe_snapshot_call("bus_overview", get_bus_overview, None, warnings)
    routes = list(getattr(bus_overview, "routes", []))[:24] if bus_overview is not None else []
    cerebro_status = safe_model_dump(safe_snapshot_call("cerebro_status", get_cerebro_status, {}, warnings))
    bus_status = safe_model_dump(safe_snapshot_call("bus_status", get_bus_status, {}, warnings))
    auditoria_status = safe_model_dump(safe_snapshot_call("auditoria_status", get_auditoria_status, {}, warnings))
    auditoria_reviews = safe_snapshot_call(
        "auditoria_reviews",
        lambda: list_auditoria_reviews(limit=24),
        [],
        warnings,
    )[:24]
    nube_status = safe_model_dump(safe_snapshot_call("nube_status", get_nube_status, {}, warnings))
    return CeoSnapshot(
        decisions=decisions,
        tasks=tasks,
        routes=routes,
        auditoria_reviews=auditoria_reviews,
        governance_report=governance_report,
        cerebro_status=cerebro_status,
        bus_status=bus_status,
        auditoria_status=auditoria_status,
        nube_status=nube_status,
        warnings=warnings,
        elapsed_ms=int((time.perf_counter() - started) * 1000),
    )


def record_ceo_event(
    *,
    action: str,
    status: str,
    detail: str,
    severity: AuditSeverity = AuditSeverity.info,
    metadata: dict[str, object] | None = None,
) -> str:
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.permission,
            severity=severity,
            source="ceo.daily_center",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "external_connection_enabled": False,
                "runtime_connected": False,
                "sunat_enabled": False,
                "local_agent_enabled": False,
                **(metadata or {}),
            },
        )
    )
    return event.id


def pending_governance_decisions() -> list[GovernanceDecision]:
    return [
        decision
        for decision in list_decisions()
        if str(decision.status.value if hasattr(decision.status, "value") else decision.status) == "pending_review"
    ]


def decision_items(decisions: list[GovernanceDecision]) -> list[CeoDailyItem]:
    return [
        item(
            item_id=decision.id,
            title=decision.title,
            body=decision.description,
            status=decision.status.value,
            source="governance",
            meta=f"solicita:{decision.requested_by.value}",
            requires_ceo_decision=True,
        )
        for decision in decisions[:8]
    ]


def task_items(tasks: list[Any] | None = None) -> list[CeoDailyItem]:
    tasks = list_cerebro_tasks() if tasks is None else tasks
    return [
        item(
            item_id=task.id,
            title=task.title,
            body=task.reason or task.description,
            status=task.state.value,
            source="cerebro",
            meta=task.destination_label,
            requires_ceo_decision=task.requires_ceo_approval,
            blocked=task.blocked,
        )
        for task in tasks[:8]
    ]


def risk_items(report: Any | None = None, allow_fetch: bool = True) -> list[CeoDailyItem]:
    if report is None:
        if not allow_fetch:
            return []
        report = get_governance_report()
    return [
        item(
            item_id=risk.id,
            title=risk.title,
            body=risk.description,
            status=risk.severity.value,
            source="governance",
            meta=risk.status.value,
            requires_ceo_decision=risk.severity.value in {"high", "critical"},
        )
        for risk in report.open_risks[:8]
    ]


def opportunity_items(routes: list[Any] | None = None) -> list[CeoDailyItem]:
    routes = get_bus_overview().routes if routes is None else routes
    targets = {"creador_de_apis_y_skills", "web_factory", "marketing", "sniff_amazon", "comercio_autonomo"}
    opportunities: list[CeoDailyItem] = []
    for route in routes:
        if route.target in targets and route.allowed:
            opportunities.append(
                item(
                    item_id=route.id,
                    title=f"{route.source.upper()} -> {route.target.upper()}",
                    body="Esto puede generar ingresos si el CEO decide priorizarlo. Preparado sin ejecución externa.",
                    status=route.status,
                    source="integration_bus",
                    meta=route.action_type,
                )
            )
    return opportunities[:8]


def route_items(routes: list[Any] | None = None) -> list[CeoDailyItem]:
    routes = get_bus_overview().routes if routes is None else routes
    return [
        item(
            item_id=route.id,
            title=f"{route.source} -> {route.target}",
            body=(
                "Ruta interna preparada sin runtime externo."
                if route.allowed
                else route.blocked_reason or "Ruta bloqueada por governance."
            ),
            status=route.status,
            source="integration_bus",
            meta=route.action_type,
            blocked=not route.allowed,
            requires_ceo_decision=route.requires_ceo_approval,
        )
        for route in routes[:10]
    ]


def blockage_items(
    report: Any | None = None,
    routes: list[Any] | None = None,
    tasks: list[Any] | None = None,
    allow_fetch: bool = True,
) -> list[CeoDailyItem]:
    report = get_governance_report() if report is None and allow_fetch else report
    routes = get_bus_overview().routes if routes is None and allow_fetch else (routes or [])
    tasks = list_cerebro_tasks() if tasks is None and allow_fetch else (tasks or [])
    route_blocks = [route for route in routes if not route.allowed]
    task_blocks = [task for task in tasks if task.blocked]
    blocked: list[CeoDailyItem] = []
    if report is None:
        for protected in ["DCFT", "SENTINELA", "ARSENAL"]:
            blocked.append(
                item(
                    item_id=f"gate:{protected.lower()}",
                    title=protected,
                    body="Producto protegido; no se ejecuta y requiere aprobación CEO.",
                    status="blocked",
                    source="governance",
                    meta="protected_fallback",
                    blocked=True,
                    requires_ceo_decision=True,
                )
            )
    else:
        blocked.extend(
            item(
                item_id=f"gate:{gate.app_id}",
                title=gate.app_name,
                body=gate.reason or "App protegida o pendiente; no se ejecuta.",
                status=gate.state.value,
                source="governance",
                meta="app protegida",
                blocked=True,
                requires_ceo_decision=True,
            )
            for gate in report.blocked_apps[:6]
        )
    blocked.extend(
        item(
            item_id=f"route:{route.id}",
            title=f"{route.source} -> {route.target}",
            body=route.blocked_reason or "Ruta bloqueada.",
            status=route.status,
            source="integration_bus",
            meta="route_blocked",
            blocked=True,
            requires_ceo_decision=route.requires_ceo_approval,
        )
        for route in route_blocks[:6]
    )
    blocked.extend(
        item(
            item_id=f"task:{task.id}",
            title=task.title,
            body=task.reason,
            status=task.state.value,
            source="cerebro",
            meta=task.destination_label,
            blocked=True,
            requires_ceo_decision=task.requires_ceo_approval,
        )
        for task in task_blocks[:6]
    )
    return blocked[:10]


def auditoria_items(status_filter: set[str], reviews: list[Any] | None = None) -> list[CeoDailyItem]:
    reviews = list_auditoria_reviews(limit=24) if reviews is None else reviews
    reviews = [
        review
        for review in reviews
        if review.status.value in status_filter
    ]
    return [
        item(
            item_id=review.id,
            title=f"{review.object_type.value}: {review.reference}",
            body="; ".join([*review.observations, *review.blockages]) or "Sin observación crítica registrada.",
            status=review.status.value,
            source="auditoria",
            meta=review.auditor or review.priority,
            requires_ceo_decision=review.requires_ceo_decision,
            blocked=review.status.value == "blocked",
        )
        for review in reviews[:6]
    ]


def state_general(snapshot: CeoSnapshot | None = None) -> str:
    if snapshot is None:
        governance = get_governance_report()
        nube = get_nube_status()
        cerebro = get_cerebro_status()
        governance_status = governance.status
        nube_public = nube.production_public_status
        nube_cost = nube.cost_status
        cerebro_status = cerebro.status
    else:
        governance_status = read_value(snapshot.governance_report, "status", "governance_degraded")
        nube_public = read_value(snapshot.nube_status, "production_public_status", "unknown")
        nube_cost = read_value(snapshot.nube_status, "cost_status", "unknown")
        cerebro_status = read_value(snapshot.cerebro_status, "status", "unknown")
    return (
        f"Empresa IA local: {governance_status}; CEREBRO {cerebro_status}; "
        f"NUBE {nube_public}; costos {nube_cost}."
    )


def build_morning_view(snapshot: CeoSnapshot | None = None) -> CeoDailyView:
    snapshot = build_ceo_snapshot() if snapshot is None else snapshot
    decisions = snapshot.decisions
    opportunities = opportunity_items(snapshot.routes)
    risks = risk_items(snapshot.governance_report, allow_fetch=False)
    tasks = task_items(snapshot.tasks)
    routes = route_items(snapshot.routes)
    blockages = blockage_items(snapshot.governance_report, snapshot.routes, snapshot.tasks, allow_fetch=False)
    recommendation = (
        "CEO, esto requiere tu decisión: revisar decisiones pendientes y mantener bloqueadas apps protegidas."
        if decisions or blockages
        else "CEO, no hay decisión crítica pendiente; CEREBRO puede preparar nuevas tareas internas."
    )
    return CeoDailyView(
        type="morning",
        headline="Centro Diario del CEO - Mañana",
        summary="Lectura rápida de decisiones, riesgos, oportunidades, tareas y bloqueos antes de operar.",
        state_general=state_general(snapshot),
        decisions=decision_items(decisions),
        opportunities=opportunities,
        risks=risks,
        tasks=tasks,
        internal_routes=routes,
        blockages=blockages,
        cerebro_recommendation=recommendation,
        generated_at=utc_now(),
    )


def build_evening_view(snapshot: CeoSnapshot | None = None) -> CeoDailyView:
    snapshot = build_ceo_snapshot() if snapshot is None else snapshot
    tasks = task_items(snapshot.tasks)
    done = [
        task
        for task in tasks
        if task.status in {"delegated", "completed"}
    ]
    blockages = blockage_items(snapshot.governance_report, snapshot.routes, snapshot.tasks, allow_fetch=False)
    decisions = snapshot.decisions
    auditoria_done = auditoria_items({"approved", "observed"}, snapshot.auditoria_reviews)
    nube = snapshot.nube_status
    summary = (
        f"Qué reportó NUBE: producción {read_value(nube, 'production_public_status')}, "
        f"DB {read_value(nube, 'database')}, costos {read_value(nube, 'cost_status')}."
    )
    recommendation = (
        "CEO, prepara mañana con CEREBRO: cerrar decisiones pendientes y revisar bloqueos."
        if decisions or blockages
        else "CEO, el cierre de tarde no muestra bloqueos críticos nuevos."
    )
    return CeoDailyView(
        type="evening",
        headline="Centro Diario del CEO - Tarde",
        summary=summary,
        state_general=state_general(snapshot),
        decisions=decision_items(decisions),
        opportunities=auditoria_done,
        risks=risk_items(snapshot.governance_report, allow_fetch=False),
        tasks=done or tasks,
        internal_routes=route_items(snapshot.routes),
        blockages=blockages,
        cerebro_recommendation=recommendation,
        generated_at=utc_now(),
    )


def ceo_actions() -> list[CeoDailyAction]:
    return [
        CeoDailyAction(
            id="approve_internal_decision",
            label="Aprobar decisión interna",
            method="POST",
            endpoint="/api/v1/ceo/decisions/{id}/approve",
            allowed=True,
            description="Aprueba una decisión interna si no toca productos protegidos ni runtime externo.",
        ),
        CeoDailyAction(
            id="reject_internal_decision",
            label="Rechazar decisión interna",
            method="POST",
            endpoint="/api/v1/ceo/decisions/{id}/reject",
            allowed=True,
            description="Rechaza una decisión interna con razón auditable.",
        ),
        CeoDailyAction(
            id="request_auditoria",
            label="Pedir auditoría",
            method="POST",
            endpoint="/api/v1/auditoria/reviews",
            allowed=True,
            description="Solicita revisión interna a AUDITORIA; sin conexión externa.",
        ),
        CeoDailyAction(
            id="request_cerebro_report",
            label="Pedir reporte a CEREBRO",
            method="GET",
            endpoint="/api/v1/ceo/daily-center",
            allowed=True,
            description="Actualiza el centro diario con CEREBRO, AUDITORIA, NUBE y governance.",
        ),
        CeoDailyAction(
            id="forbidden_activate_protected",
            label="Activar producto protegido",
            method="BLOCKED",
            endpoint="blocked",
            allowed=False,
            description="DCFT, SENTINELA, ARSENAL, SUNAT, Local Agent, deploy directo y APIs externas siguen bloqueados.",
            blocked_reason="protected_or_external_action",
        ),
    ]


def get_ceo_daily_center() -> CeoDailyCenter:
    snapshot = build_ceo_snapshot()
    morning = build_morning_view(snapshot)
    evening = build_evening_view(snapshot)
    decisions = snapshot.decisions
    risks = risk_items(snapshot.governance_report, allow_fetch=False)
    opportunities = opportunity_items(snapshot.routes)
    blockages = blockage_items(snapshot.governance_report, snapshot.routes, snapshot.tasks, allow_fetch=False)
    tasks = task_items(snapshot.tasks)
    cerebro = snapshot.cerebro_status
    bus_status = snapshot.bus_status
    governance_report = snapshot.governance_report
    auditoria = snapshot.auditoria_status
    nube = snapshot.nube_status
    next_action = morning.cerebro_recommendation
    pending_count = (
        len(getattr(governance_report, "pending_decisions", []))
        if governance_report is not None
        else len(decisions)
    )
    blocked_apps_count = (
        len(getattr(governance_report, "blocked_apps", []))
        if governance_report is not None
        else 3
    )
    critical_risks_count = (
        len(getattr(governance_report, "critical_risks", []))
        if governance_report is not None
        else 0
    )
    return CeoDailyCenter(
        status="ceo_daily_center_operational_internal",
        mode="degraded" if snapshot.warnings else "ok",
        degraded=bool(snapshot.warnings),
        warnings=snapshot.warnings,
        generated_at=utc_now(),
        executive_summary=(
            f"{len(decisions)} decisiones esperando CEO, {len(risks)} riesgos abiertos, "
            f"{len(opportunities)} oportunidades preparadas, {len(blockages)} bloqueos activos. "
            f"Tiempo interno aproximado: {snapshot.elapsed_ms} ms."
        ),
        morning=morning,
        evening=evening,
        decisions=decisions,
        decisions_waiting_ceo=len(decisions),
        active_tasks=len([task for task in tasks if not task.blocked]),
        blocked_items=len(blockages),
        opportunities=len(opportunities),
        risks=len(risks),
        cerebro=cerebro,
        bus=bus_status,
        governance={
            "status": read_value(governance_report, "status", "governance_degraded"),
            "pending_decisions": pending_count,
            "blocked_apps": blocked_apps_count,
            "critical_risks": critical_risks_count,
            "external_connections_enabled": False,
        },
        auditoria=auditoria,
        nube=nube,
        protected_apps=["DCFT", "SENTINELA", "ARSENAL", "SUNAT", "Local Agent"],
        actions=ceo_actions(),
        next_action=next_action,
        external_connection_enabled=False,
        runtime_connected=False,
        sunat_enabled=False,
        local_agent_enabled=False,
    )


def is_prohibited_decision(decision: GovernanceDecision) -> tuple[bool, str]:
    metadata = decision.metadata or {}
    metadata_text = normalize(json.dumps(metadata, sort_keys=True))
    target = normalize(metadata.get("target_id") or metadata.get("target") or metadata.get("app_id"))
    action = normalize(metadata.get("action") or metadata.get("requested_action") or "")
    if target in PROTECTED_TARGETS:
        return True, f"protected_target:{target}"
    if action in PROHIBITED_ACTIONS:
        return True, f"prohibited_action:{action}"
    if metadata.get("external_connection_enabled") is True or metadata.get("runtime_connected") is True:
        return True, "external_runtime_requested"
    if any(prohibited in metadata_text for prohibited in PROHIBITED_ACTIONS):
        return True, "prohibited_action_in_metadata"
    return False, "allowed_internal_decision"


def approve_ceo_decision(
    decision_id: str,
    request: CeoDecisionActionRequest,
    role_id: GovernanceRole,
) -> GovernanceDecision:
    decision = get_decision(decision_id)
    if decision is None:
        raise GovernanceError(404, {"error": "decision_not_found", "decision_id": decision_id})
    prohibited, reason = is_prohibited_decision(decision)
    if prohibited:
        audit_event_id = record_ceo_event(
            action="approve_decision",
            status="blocked",
            detail=f"CEO Daily Center blocked prohibited decision {decision_id}.",
            severity=AuditSeverity.high,
            metadata={"decision_id": decision_id, "reason": reason},
        )
        raise GovernanceError(
            403,
            {
                "error": "ceo_action_prohibited",
                "decision_id": decision_id,
                "reason": reason,
                "audit_event_id": audit_event_id,
            },
        )
    approved = approve_decision(
        decision_id,
        DecisionTransitionRequest(
            role_id=role_id,
            evidence=request.evidence or "Evidencia CEO desde Centro Diario.",
        ),
    )
    record_ceo_event(
        action="approve_decision",
        status="approved",
        detail=f"CEO Daily Center approved internal decision {decision_id}.",
        metadata={"decision_id": decision_id, "role_id": role_id.value},
    )
    return approved


def reject_ceo_decision(
    decision_id: str,
    request: CeoDecisionActionRequest,
    role_id: GovernanceRole,
) -> GovernanceDecision:
    rejected = reject_decision(
        decision_id,
        DecisionTransitionRequest(
            role_id=role_id,
            reason=request.reason or "Rechazo CEO desde Centro Diario.",
        ),
    )
    record_ceo_event(
        action="reject_decision",
        status="rejected",
        detail=f"CEO Daily Center rejected internal decision {decision_id}.",
        severity=AuditSeverity.medium,
        metadata={"decision_id": decision_id, "role_id": role_id.value},
    )
    return rejected


def list_ceo_decisions() -> list[GovernanceDecision]:
    return pending_governance_decisions()


def get_recent_ceo_audit_actions() -> list[dict[str, object]]:
    return [
        {
            "action": event.action,
            "status": event.status,
            "detail": event.detail,
            "created_at": event.created_at,
        }
        for event in list_bus_audit()[:5]
    ]
