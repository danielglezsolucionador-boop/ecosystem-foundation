from __future__ import annotations

from datetime import datetime
import json
from zoneinfo import ZoneInfo
from uuid import uuid4

from app.core.database import connect, sql_placeholder
from app.core.safe_data import safe_payload
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser, ControlCenterRole, UserPublic, UserStatus
from app.schemas.workday import (
    WorkdayAlert,
    WorkdayAlertCategory,
    WorkdayAlertEvaluateRequest,
    WorkdayCheckpoint,
    WorkdayPhase,
    WorkdayPriorityChange,
    WorkdayPriorityChangeCreate,
    WorkdayReport,
    WorkdaySchedule,
    WorkdaySession,
    WorkdayStartRequest,
    WorkdayStatus,
)
from app.services.audit import create_audit_event, get_auditoria_status
from app.services.departments import list_departments
from app.services.missions import active_loop_missions, get_mission_daily_report
from app.services.nube import get_nube_status
from app.services.revenue import get_daily_report as get_revenue_daily_report
from app.services.revenue import get_revenue_status

PERU_TZ = ZoneInfo("America/Lima")
WORKDAY_TABLES = {
    "workday_sessions",
    "workday_checkpoints",
    "workday_events",
    "workday_priority_changes",
    "workday_alerts",
    "workday_department_updates",
    "workday_revenue_updates",
    "workday_reports",
}
HIGH_SIGNAL_CATEGORIES = {
    WorkdayAlertCategory.revenue_opportunity,
    WorkdayAlertCategory.trend,
    WorkdayAlertCategory.security_risk,
    WorkdayAlertCategory.legal_tax_risk,
    WorkdayAlertCategory.production_down,
    WorkdayAlertCategory.critical_blocker,
    WorkdayAlertCategory.temporary_opportunity,
    WorkdayAlertCategory.revenue_goal,
}


class WorkdayError(Exception):
    def __init__(self, status_code: int, detail: dict):
        super().__init__(str(detail))
        self.status_code = status_code
        self.detail = detail


def lima_now() -> datetime:
    return datetime.now(PERU_TZ)


def now_iso() -> str:
    return lima_now().isoformat()


def today_lima() -> str:
    return lima_now().strftime("%Y-%m-%d")


def workday_id(date: str) -> str:
    return f"workday_{date.replace('-', '')}"


def placeholder() -> str:
    return sql_placeholder()


def ensure_table_name(table_name: str) -> None:
    if table_name not in WORKDAY_TABLES:
        raise WorkdayError(500, {"error": "invalid_workday_table", "table": table_name})


def ensure_workday_schema() -> None:
    with connect() as connection:
        for table_name in WORKDAY_TABLES:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        connection.commit()


def upsert_payload(table_name: str, item_id: str, payload: dict) -> None:
    ensure_table_name(table_name)
    ensure_workday_schema()
    ph = placeholder()
    now = now_iso()
    payload_json = json.dumps(payload, ensure_ascii=False)
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({ph}, {ph}, {ph}, {ph})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (item_id, payload_json, now, now),
        )
        connection.commit()


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_table_name(table_name)
    ensure_workday_schema()
    ph = placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {ph}",
            (item_id,),
        ).fetchone()
    return safe_payload(row) if row else None


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_table_name(table_name)
    ensure_workday_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            ORDER BY created_at DESC
            """
        ).fetchall()
    payloads: list[dict] = []
    for row in rows:
        payload = safe_payload(row)
        if payload is not None:
            payloads.append(payload)
    return payloads


def actor_name(actor: AuthenticatedUser | None) -> str:
    if actor is None:
        return "CEREBRO"
    return actor.name or actor.email or actor.role.value


def system_actor() -> AuthenticatedUser:
    now = now_iso()
    return AuthenticatedUser(
        id="workday-system",
        email="workday-system@local.internal",
        name="CEREBRO Workday OS",
        role=ControlCenterRole.service,
        status=UserStatus.active,
        created_at=now,
        updated_at=now,
        session_id="workday-system-session",
    )


def record_workday_audit(
    *,
    action: str,
    status: str,
    detail: str,
    actor: AuthenticatedUser | None = None,
    severity: AuditSeverity = AuditSeverity.info,
    metadata: dict | None = None,
) -> str:
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.runtime,
            severity=severity,
            source="workday.autonomous_os",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "actor": actor_name(actor),
                "external_connection_enabled": False,
                "runtime_connected": False,
                "payment_connected": False,
                "sunat_enabled": False,
                **(metadata or {}),
            },
        )
    )
    return event.id


def safe_model_dump(value) -> dict:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return value
    return {}


def revenue_progress_snapshot() -> tuple[dict, dict]:
    status = get_revenue_status()
    return (
        {
            "goal_usd": status.global_goal.monthly_target_usd,
            "pipeline_usd": status.estimated_global_pipeline_usd,
            "progress_percent": status.global_progress_percent,
            "actual_revenue_usd": status.actual_revenue_usd,
            "actual_revenue_status": status.actual_revenue_status,
        },
        {
            "goal_usd": status.ecommerce_goal.monthly_target_usd,
            "pipeline_usd": status.estimated_ecommerce_pipeline_usd,
            "progress_percent": status.ecommerce_progress_percent,
            "separated_from_global": status.ecommerce_goal.separated_from_global,
        },
    )


def active_mission_payloads() -> list[dict]:
    return [mission.model_dump(mode="json") for mission in active_loop_missions()[:12]]


def relevant_alert_payloads(session_id: str) -> list[dict]:
    return [
        payload
        for payload in fetch_payloads("workday_alerts")
        if payload.get("workday_id") == session_id and payload.get("included_in_ceo_feed") is True
    ][:12]


def priority_change_payloads(session_id: str) -> list[dict]:
    return [
        payload
        for payload in fetch_payloads("workday_priority_changes")
        if payload.get("workday_id") == session_id
    ][:12]


def default_blockers(missions: list[dict], revenue: dict) -> list[str]:
    blockers: list[str] = []
    waiting_ceo = [mission for mission in missions if mission.get("status") == "waiting_ceo_approval"]
    if waiting_ceo:
        blockers.append(f"{len(waiting_ceo)} misiones esperan decisión CEO.")
    if revenue.get("actual_revenue_status") == "no_real_revenue_reported":
        blockers.append("No hay ingresos reales reportados; Revenue OS solo estima pipeline.")
    blockers.append("Scheduler real no existe: disparo manual preparado.")
    return blockers


def default_ceo_requests(missions: list[dict], revenue: dict, alerts: list[dict]) -> list[str]:
    requests: list[str] = []
    if any(mission.get("requires_ceo_approval") for mission in missions):
        requests.append("CEO, revisar misiones con dinero, riesgo o producto protegido.")
    if any(alert.get("requires_ceo_approval") for alert in alerts):
        requests.append("CEO, revisar alertas con dinero real o riesgo sensible.")
    if revenue.get("actual_revenue_status") == "no_real_revenue_reported":
        requests.append("CEO, confirmar si hay evidencia de ingresos reales antes de declararlos.")
    return requests


def build_session_payload(date: str | None = None, timezone: str = "America/Lima") -> dict:
    date = date or today_lima()
    session_id = workday_id(date)
    now = now_iso()
    revenue, ecommerce = revenue_progress_snapshot()
    missions = active_mission_payloads()
    alerts = relevant_alert_payloads(session_id)
    priority_changes = priority_change_payloads(session_id)
    blockers = default_blockers(missions, revenue)
    ceo_requests = default_ceo_requests(missions, revenue, alerts)
    existing = fetch_payload("workday_sessions", session_id) or {}
    return {
        "id": session_id,
        "date": date,
        "timezone": timezone,
        "morning_plan": existing.get("morning_plan") or {},
        "midday_status": existing.get("midday_status") or {},
        "evening_report": existing.get("evening_report") or {},
        "active_missions": missions,
        "priority_changes": priority_changes,
        "alerts": alerts,
        "revenue_progress": revenue,
        "ecommerce_progress": ecommerce,
        "blockers": blockers,
        "CEO_requests": ceo_requests,
        "scheduler_status": "prepared",
        "manual_trigger_available": True,
        "generated_at": now,
        "created_at": existing.get("created_at") or now,
        "updated_at": now,
        "external_connection_enabled": False,
        "runtime_connected": False,
        "payment_connected": False,
        "sunat_enabled": False,
    }


def save_session(payload: dict) -> WorkdaySession:
    payload["updated_at"] = now_iso()
    upsert_payload("workday_sessions", payload["id"], payload)
    try:
        return WorkdaySession(**payload)
    except Exception:
        fallback = build_session_payload(date=today_lima())
        fallback["blockers"] = ["Safe fallback because source data is missing or incomplete."]
        upsert_payload("workday_sessions", fallback["id"], fallback)
        return WorkdaySession(**fallback)


def start_workday(
    request: WorkdayStartRequest | None = None,
    actor: AuthenticatedUser | None = None,
) -> WorkdaySession:
    request = request or WorkdayStartRequest()
    payload = build_session_payload(date=request.date, timezone=request.timezone)
    record_workday_audit(
        action="start_workday",
        status="prepared",
        detail="CEREBRO started or refreshed Autonomous Workday OS without external scheduler.",
        actor=actor,
        metadata={"workday_id": payload["id"], "timezone": payload["timezone"]},
    )
    return save_session(payload)


def current_session() -> WorkdaySession:
    return save_session(build_session_payload())


def checkpoint_id(date: str, phase: WorkdayPhase) -> str:
    return f"workday_checkpoint_{date.replace('-', '')}_{phase.value}"


def collect_department_names() -> list[str]:
    names = []
    for department in list_departments()[:12]:
        if department.name not in names:
            names.append(department.name)
    for required in ["CEREBRO", "AUDITORIA", "NUBE"]:
        if required not in names:
            names.append(required)
    return names[:12]


def top_opportunities() -> list[str]:
    status = get_revenue_status()
    opportunities = [
        f"{opportunity.title}: USD {opportunity.economic_matrix.expected_net_profit_usd or 0} neto estimado"
        for opportunity in status.top_opportunities[:4]
    ]
    if not opportunities:
        opportunities.append("Revenue OS debe calcular oportunidades sin inventar ingresos reales.")
    return opportunities


def mission_priorities(missions: list[dict]) -> list[str]:
    priorities = [
        f"{mission.get('title')}: {mission.get('next_action') or mission.get('status')}"
        for mission in missions[:5]
    ]
    return priorities or ["CEREBRO debe crear o refrescar misiones internas útiles."]


def checkpoint_common(phase: WorkdayPhase, session: WorkdaySession) -> dict:
    missions = session.active_missions
    revenue = session.revenue_progress
    ecommerce = session.ecommerce_progress
    return {
        "workday_id": session.id,
        "date": session.date,
        "timezone": session.timezone,
        "active_missions": missions,
        "priorities": mission_priorities(missions),
        "departments": collect_department_names(),
        "opportunities": top_opportunities(),
        "risks": [
            "No declarar ingresos reales sin evidencia.",
            "No ejecutar dinero real ni campañas pagadas sin CEO.",
            "No activar SUNAT real ni Local Agent runtime.",
        ],
        "blockers": session.blockers,
        "estimated_economic_impact": (
            f"Pipeline global USD {revenue.get('pipeline_usd', 0)} / "
            f"e-commerce USD {ecommerce.get('pipeline_usd', 0)}."
        ),
        "external_connection_enabled": False,
        "runtime_connected": False,
        "sunat_enabled": False,
    }


def save_checkpoint(checkpoint: WorkdayCheckpoint, session: WorkdaySession) -> WorkdayCheckpoint:
    payload = checkpoint.model_dump(mode="json")
    upsert_payload("workday_checkpoints", checkpoint.id, payload)
    session_payload = session.model_dump(mode="json")
    if checkpoint.phase == WorkdayPhase.morning:
        session_payload["morning_plan"] = payload
    elif checkpoint.phase == WorkdayPhase.midday:
        session_payload["midday_status"] = payload
    else:
        session_payload["evening_report"] = payload
        upsert_payload("workday_reports", f"workday_report_{session.date.replace('-', '')}", payload)
    save_session(session_payload)
    upsert_payload(
        "workday_events",
        f"workday_event_{uuid4()}",
        {
            "id": f"workday_event_{uuid4()}",
            "workday_id": session.id,
            "phase": checkpoint.phase.value,
            "status": "generated",
            "message": checkpoint.headline,
            "created_at": now_iso(),
            "external_connection_enabled": False,
            "runtime_connected": False,
        },
    )
    return checkpoint


def generate_morning(actor: AuthenticatedUser | None = None) -> WorkdayCheckpoint:
    session = start_workday(actor=actor)
    common = checkpoint_common(WorkdayPhase.morning, session)
    checkpoint = WorkdayCheckpoint(
        id=checkpoint_id(session.date, WorkdayPhase.morning),
        phase=WorkdayPhase.morning,
        schedule_time="08:00",
        headline="Planificación de mañana CEREBRO",
        summary=(
            "CEREBRO inicia el día con metas USD 6,000 global y USD 10,000 e-commerce, "
            "misiones activas, oportunidades, riesgos y bloqueos."
        ),
        decisions_by_cerebro=[
            "Priorizar misiones internas con impacto económico o desbloqueo operativo.",
            "Mantener productos protegidos sin ejecución real.",
        ],
        requires_ceo=session.CEO_requests,
        action_plan=[
            "Revisar misiones activas.",
            "Pedir auditoría si hay riesgo o bloqueo.",
            "Enviar a FORJA solo solicitudes internas preparadas.",
            "Registrar oportunidades en Revenue OS sin declarar venta real.",
        ],
        report="CEO, este es el plan de mañana. Trabajo interno preparado y trazable.",
        generated_at=now_iso(),
        **common,
    )
    record_workday_audit(
        action="generate_morning",
        status="prepared",
        detail="CEREBRO generated morning workday checkpoint.",
        actor=actor,
        metadata={"workday_id": session.id},
    )
    return save_checkpoint(checkpoint, session)


def generate_midday(actor: AuthenticatedUser | None = None) -> WorkdayCheckpoint:
    session = start_workday(actor=actor)
    common = checkpoint_common(WorkdayPhase.midday, session)
    checkpoint = WorkdayCheckpoint(
        id=checkpoint_id(session.date, WorkdayPhase.midday),
        phase=WorkdayPhase.midday,
        schedule_time="13:00",
        headline="Checkpoint de mediodía CEREBRO",
        summary="CEREBRO revisa avances, cambios de prioridad, alertas relevantes y bloqueos.",
        decisions_by_cerebro=[
            "Cambiar prioridad del día si aparece oportunidad o riesgo fuerte.",
            "No interrumpir al CEO por señales bajas.",
        ],
        requires_ceo=session.CEO_requests,
        action_plan=[
            "Actualizar misiones en progreso.",
            "Revisar alertas con score alto.",
            "Registrar cambio de prioridad si el valor del día cambió.",
        ],
        report=(
            f"Mediodía: {len(session.priority_changes)} cambios de prioridad, "
            f"{len(session.alerts)} alertas relevantes, {len(session.active_missions)} misiones activas."
        ),
        generated_at=now_iso(),
        **common,
    )
    record_workday_audit(
        action="generate_midday",
        status="prepared",
        detail="CEREBRO generated midday workday checkpoint.",
        actor=actor,
        metadata={"workday_id": session.id},
    )
    return save_checkpoint(checkpoint, session)


def generate_evening(actor: AuthenticatedUser | None = None) -> WorkdayCheckpoint:
    session = start_workday(actor=actor)
    common = checkpoint_common(WorkdayPhase.evening, session)
    mission_report = get_mission_daily_report()
    revenue_report = get_revenue_daily_report()
    nube = safe_model_dump(get_nube_status())
    auditoria = safe_model_dump(get_auditoria_status())
    forge_requests = sum(len(mission.get("forge_requests") or []) for mission in session.active_missions)
    checkpoint = WorkdayCheckpoint(
        id=checkpoint_id(session.date, WorkdayPhase.evening),
        phase=WorkdayPhase.evening,
        schedule_time="19:00",
        headline="Reporte tarde/noche CEREBRO",
        summary=(
            "CEREBRO resume lo hecho, lo no hecho, lo bloqueado, oportunidades, auditoría, "
            "NUBE, Revenue OS y plan de mañana."
        ),
        decisions_by_cerebro=[
            f"{mission_report.active_missions} misiones activas revisadas.",
            f"{forge_requests} solicitudes FORJA preparadas, sin tocar FORJA externa.",
            f"AUDITORIA status: {auditoria.get('status', 'unknown')}.",
            f"NUBE status: {nube.get('status', 'unknown')}.",
        ],
        requires_ceo=session.CEO_requests,
        action_plan=[
            "Cerrar o bloquear misiones con evidencia.",
            "Completar ROI de oportunidades sin datos.",
            "Preparar plan de mañana a las 08:00.",
        ],
        report=(
            f"Hecho: seguimiento de misiones y revenue. No hecho: ejecución externa. "
            f"Bloqueado: dinero real, SUNAT, cuentas externas. "
            f"Global USD {revenue_report.global_pipeline_usd}/{revenue_report.global_goal_usd}; "
            f"e-commerce USD {revenue_report.ecommerce_pipeline_usd}/{revenue_report.ecommerce_goal_usd}. "
            "Dinero solicitado espera CEO si existe."
        ),
        generated_at=now_iso(),
        **common,
    )
    record_workday_audit(
        action="generate_evening",
        status="prepared",
        detail="CEREBRO generated evening workday report.",
        actor=actor,
        metadata={"workday_id": session.id},
    )
    return save_checkpoint(checkpoint, session)


def get_checkpoint(phase: WorkdayPhase, actor: AuthenticatedUser | None = None) -> WorkdayCheckpoint:
    session = current_session()
    payload = fetch_payload("workday_checkpoints", checkpoint_id(session.date, phase))
    if payload:
        try:
            return WorkdayCheckpoint(**payload)
        except Exception:
            pass
    if phase == WorkdayPhase.morning:
        return generate_morning(actor)
    if phase == WorkdayPhase.midday:
        return generate_midday(actor)
    return generate_evening(actor)


def alert_relevance(request: WorkdayAlertEvaluateRequest) -> tuple[int, bool, bool]:
    score = request.relevance_score
    if request.category in HIGH_SIGNAL_CATEGORIES:
        score = max(score, 72)
    if request.economic_impact_usd and request.economic_impact_usd >= 500:
        score = max(score, 76)
    high_risk = request.risk_level.lower() in {"high", "critical", "legal", "tax", "tributary"}
    interrupt = score >= 70 or request.category in HIGH_SIGNAL_CATEGORIES or high_risk
    requires_ceo = request.requires_money or high_risk or request.category == WorkdayAlertCategory.legal_tax_risk
    return min(score, 100), interrupt, requires_ceo


def evaluate_alert(
    request: WorkdayAlertEvaluateRequest,
    actor: AuthenticatedUser | None = None,
) -> WorkdayAlert:
    session = start_workday(actor=actor)
    score, interrupt, requires_ceo = alert_relevance(request)
    audit_event_id = record_workday_audit(
        action="evaluate_alert",
        status="interrupt_ceo" if interrupt else "noise_filtered",
        detail="CEREBRO evaluated a workday alert without external execution.",
        actor=actor,
        severity=AuditSeverity.high if requires_ceo else AuditSeverity.info,
        metadata={
            "workday_id": session.id,
            "category": request.category.value,
            "relevance_score": score,
            "requires_ceo_approval": requires_ceo,
        },
    )
    alert = WorkdayAlert(
        id=f"workday_alert_{uuid4()}",
        workday_id=session.id,
        title=request.title,
        summary=request.summary,
        category=request.category,
        relevance_score=score,
        interrupt_ceo=interrupt,
        why_it_matters=request.why_it_matters or (
            "Tiene relación directa con ingresos, riesgo o continuidad."
            if interrupt
            else "Señal baja; se registra sin interrumpir."
        ),
        opportunity=request.opportunity,
        threat=request.threat,
        recommended_action=request.recommended_action,
        departments_involved=request.departments_involved,
        dafo=request.dafo or {
            "strength": "CEREBRO filtra ruido.",
            "weakness": "Impacto puede requerir más datos.",
            "opportunity": request.opportunity or "No cuantificada.",
            "threat": request.threat or "No crítica.",
        },
        economic_impact_usd=request.economic_impact_usd,
        requires_money=request.requires_money,
        requires_ceo_approval=requires_ceo,
        included_in_ceo_feed=interrupt,
        audit_event_id=audit_event_id,
        created_at=now_iso(),
    )
    upsert_payload("workday_alerts", alert.id, alert.model_dump(mode="json"))
    save_session(build_session_payload(session.date, session.timezone))
    return alert


def list_alerts() -> list[WorkdayAlert]:
    session = current_session()
    alerts: list[WorkdayAlert] = []
    for payload in relevant_alert_payloads(session.id):
        try:
            alerts.append(WorkdayAlert(**payload))
        except Exception:
            continue
    return alerts


def create_priority_change(
    request: WorkdayPriorityChangeCreate,
    actor: AuthenticatedUser | None = None,
) -> WorkdayPriorityChange:
    session = start_workday(actor=actor)
    audit_event_id = record_workday_audit(
        action="change_priority",
        status="no_ceo_approval_required",
        detail="CEREBRO changed workday priority and will report it to CEO.",
        actor=actor,
        metadata={
            "workday_id": session.id,
            "previous_priority": request.previous_priority,
            "new_priority": request.new_priority,
            "departments_affected": request.departments_affected,
        },
    )
    change = WorkdayPriorityChange(
        id=f"workday_priority_change_{uuid4()}",
        workday_id=session.id,
        previous_priority=request.previous_priority,
        new_priority=request.new_priority,
        reason=request.reason,
        opportunity_or_risk=request.opportunity_or_risk,
        economic_impact_usd=request.economic_impact_usd,
        departments_affected=request.departments_affected,
        moment=now_iso(),
        report_to_ceo=request.report_to_ceo,
        requires_ceo_approval=False,
        audit_event_id=audit_event_id,
    )
    upsert_payload("workday_priority_changes", change.id, change.model_dump(mode="json"))
    save_session(build_session_payload(session.date, session.timezone))
    return change


def list_priority_changes() -> list[WorkdayPriorityChange]:
    session = current_session()
    changes: list[WorkdayPriorityChange] = []
    for payload in priority_change_payloads(session.id):
        try:
            changes.append(WorkdayPriorityChange(**payload))
        except Exception:
            continue
    return changes


def get_workday_status() -> WorkdayStatus:
    session = current_session()
    return WorkdayStatus(
        status="autonomous_workday_os_prepared_internal",
        date=session.date,
        timezone=session.timezone,
        schedule=WorkdaySchedule(),
        scheduler_status="prepared",
        manual_trigger_available=True,
        active_missions=len(session.active_missions),
        priority_changes=len(session.priority_changes),
        relevant_alerts=len(session.alerts),
        revenue_progress=session.revenue_progress,
        ecommerce_progress=session.ecommerce_progress,
        blockers=session.blockers,
        CEO_requests=session.CEO_requests,
        generated_at=now_iso(),
    )


def get_workday_report() -> WorkdayReport:
    session = current_session()
    return WorkdayReport(
        status="workday_report_prepared_internal",
        session=session,
        morning=session.morning_plan,
        midday=session.midday_status,
        evening=session.evening_report,
        alerts=session.alerts,
        priority_changes=session.priority_changes,
        generated_at=now_iso(),
    )
