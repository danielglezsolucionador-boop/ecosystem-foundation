from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import AuditCategory, AuditEvent, AuditEventCreate, AuditSeverity
from app.schemas.governance import (
    ApprovalStatus,
    ApprovalTransitionRequest,
    DecisionTransitionRequest,
    DecisionStatus,
    GovernanceApproval,
    GovernanceApprovalCreate,
    GovernanceActionDefinition,
    GovernanceAuthBoundary,
    GovernanceDecision,
    GovernanceDecisionCreate,
    GovernanceOverview,
    GovernancePolicy,
    GovernanceReport,
    GovernanceRisk,
    GovernanceRiskCreate,
    GovernanceRiskUpdate,
    GovernanceRole,
    IntegrationGate,
    IntegrationGateState,
    IntegrationGateTransitionRequest,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    RiskCloseRequest,
    RiskMitigationRequest,
    RiskSeverity,
    RiskStatus,
)
from app.services.app_registry import get_registered_app, list_registered_apps
from app.services.audit import create_audit_event, list_audit_events

DECISIONS_TABLE = "governance_decisions"
APPROVALS_TABLE = "governance_approvals"
GATES_TABLE = "governance_integration_gates"
RISKS_TABLE = "governance_risks"
PROTECTED_APP_IDS = {"doctor_contable_financiero_tributario", "centinela"}
PLANNED_BLOCKED_APP_IDS = {"arsenal"}
APP_ALIASES = {
    "dcft": "doctor_contable_financiero_tributario",
    "sentinela": "centinela",
}
APPROVER_ROLES = {GovernanceRole.ceo, GovernanceRole.admin}
ACTION_ROLES: dict[str, set[GovernanceRole]] = {
    "create_decision": {GovernanceRole.ceo, GovernanceRole.admin, GovernanceRole.operator},
    "approve_decision": {GovernanceRole.ceo, GovernanceRole.admin},
    "reject_decision": {GovernanceRole.ceo, GovernanceRole.admin},
    "block_decision": {GovernanceRole.ceo, GovernanceRole.admin},
    "create_approval": {GovernanceRole.ceo, GovernanceRole.admin, GovernanceRole.operator},
    "approve_approval": {GovernanceRole.ceo, GovernanceRole.admin},
    "reject_approval": {GovernanceRole.ceo, GovernanceRole.admin},
    "escalate_approval": {GovernanceRole.ceo, GovernanceRole.admin, GovernanceRole.operator},
    "request_discovery": {GovernanceRole.ceo, GovernanceRole.admin, GovernanceRole.operator},
    "approve_discovery": {GovernanceRole.ceo, GovernanceRole.admin},
    "approve_connection": {GovernanceRole.ceo, GovernanceRole.admin},
    "block_gate": {GovernanceRole.ceo, GovernanceRole.admin},
    "suspend_gate": {GovernanceRole.ceo, GovernanceRole.admin},
    "create_risk": {GovernanceRole.ceo, GovernanceRole.admin, GovernanceRole.operator},
    "mitigate_risk": {GovernanceRole.ceo, GovernanceRole.admin, GovernanceRole.operator},
    "close_risk": {GovernanceRole.ceo, GovernanceRole.admin},
    "evaluate_policy": {
        GovernanceRole.ceo,
        GovernanceRole.admin,
        GovernanceRole.operator,
        GovernanceRole.auditor,
        GovernanceRole.service,
    },
}
ROLE_VIEWS: dict[GovernanceRole, list[str]] = {
    GovernanceRole.ceo: ["ceo", "governance", "operator", "auditor", "system"],
    GovernanceRole.admin: ["ceo", "governance", "operator", "auditor", "system"],
    GovernanceRole.operator: ["operator", "system", "governance"],
    GovernanceRole.auditor: ["auditor", "governance", "system"],
    GovernanceRole.service: ["system"],
}
ACTION_CATALOG: tuple[dict[str, object], ...] = (
    {
        "id": "create_decision",
        "label": "Crear decision",
        "description": "Registra una decision humana para revision controlada.",
        "section": "Decision Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/decisions",
        "payload_template": {
            "title": "Decision operativa de prueba",
            "description": "Decision creada desde Control Center con boundary de rol.",
            "requested_by": "{role_id}",
            "evidence": "Evidencia generada desde la cabina.",
        },
    },
    {
        "id": "approve_decision",
        "label": "Aprobar decision",
        "description": "Aprueba una decision pendiente con rol autorizado.",
        "section": "Decision Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/decisions/{decision_id}/approve",
        "requires_evidence": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "evidence": "Evidencia de aprobacion."},
    },
    {
        "id": "reject_decision",
        "label": "Rechazar decision",
        "description": "Rechaza una decision y exige razon humana.",
        "section": "Decision Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/decisions/{decision_id}/reject",
        "requires_reason": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "reason": "Razon de rechazo."},
    },
    {
        "id": "block_decision",
        "label": "Bloquear decision",
        "description": "Bloquea una decision con razon auditable.",
        "section": "Decision Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/decisions/{decision_id}/block",
        "requires_reason": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "reason": "Riesgo detectado."},
    },
    {
        "id": "create_approval",
        "label": "Crear solicitud",
        "description": "Crea una solicitud de aprobacion humana.",
        "section": "Approval Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/approvals",
        "payload_template": {
            "title": "Solicitud de governance",
            "description": "Solicitud creada desde Control Center.",
            "approval_type": "integration_discovery",
            "requested_by": "{role_id}",
            "target_id": "pluma",
            "evidence": "Evidencia inicial.",
        },
    },
    {
        "id": "approve_approval",
        "label": "Aprobar solicitud",
        "description": "Aprueba una solicitud pendiente.",
        "section": "Approval Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/approvals/{approval_id}/approve",
        "requires_evidence": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "evidence": "Aprobacion validada."},
    },
    {
        "id": "reject_approval",
        "label": "Rechazar solicitud",
        "description": "Rechaza una solicitud pendiente con razon.",
        "section": "Approval Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/approvals/{approval_id}/reject",
        "requires_reason": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "reason": "Solicitud no aprobada."},
    },
    {
        "id": "escalate_approval",
        "label": "Escalar solicitud",
        "description": "Escala una solicitud pendiente para atencion ejecutiva.",
        "section": "Approval Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/approvals/{approval_id}/escalate",
        "requires_reason": True,
        "payload_template": {"role_id": "{role_id}", "reason": "Requiere criterio ejecutivo."},
    },
    {
        "id": "request_discovery",
        "label": "Solicitar discovery",
        "description": "Solicita discovery de una app no protegida sin conectar apps reales.",
        "section": "Integration Gates",
        "method": "POST",
        "endpoint": "/api/v1/governance/integration-gates/{app_id}/request-discovery",
        "payload_template": {"role_id": "{role_id}", "reason": "Discovery solicitado desde cabina."},
    },
    {
        "id": "approve_discovery",
        "label": "Aprobar discovery",
        "description": "Aprueba discovery con evidencia sin abrir conexion real.",
        "section": "Integration Gates",
        "method": "POST",
        "endpoint": "/api/v1/governance/integration-gates/{app_id}/approve-discovery",
        "requires_evidence": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "evidence": "Discovery validado."},
    },
    {
        "id": "approve_connection",
        "label": "Aprobar conexion futura",
        "description": "Marca una conexion como aprobada para fase futura; no conecta apps reales.",
        "section": "Integration Gates",
        "method": "POST",
        "endpoint": "/api/v1/governance/integration-gates/{app_id}/approve-connection",
        "requires_evidence": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "evidence": "Conexion futura aprobada."},
    },
    {
        "id": "block_gate",
        "label": "Bloquear app",
        "description": "Bloquea una app dentro de governance.",
        "section": "Integration Gates",
        "method": "POST",
        "endpoint": "/api/v1/governance/integration-gates/{app_id}/block",
        "requires_reason": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "reason": "Bloqueo preventivo."},
    },
    {
        "id": "suspend_gate",
        "label": "Suspender app",
        "description": "Suspende una app no protegida por razon humana.",
        "section": "Integration Gates",
        "method": "POST",
        "endpoint": "/api/v1/governance/integration-gates/{app_id}/suspend",
        "requires_reason": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "reason": "Suspension temporal."},
    },
    {
        "id": "create_risk",
        "label": "Crear riesgo",
        "description": "Crea un riesgo controlado en Risk Center.",
        "section": "Risk Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/risks",
        "payload_template": {
            "title": "Riesgo operativo de prueba",
            "description": "Riesgo creado desde Control Center.",
            "risk_type": "operational",
            "severity": "medium",
            "owner": "{role_id}",
            "evidence": "Evidencia inicial.",
        },
    },
    {
        "id": "mitigate_risk",
        "label": "Mitigar riesgo",
        "description": "Registra mitigacion sobre un riesgo abierto.",
        "section": "Risk Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/risks/{risk_id}/mitigate",
        "payload_template": {"role_id": "{role_id}", "mitigation": "Mitigacion aplicada desde cabina."},
    },
    {
        "id": "close_risk",
        "label": "Cerrar riesgo",
        "description": "Cierra un riesgo con evidencia verificable.",
        "section": "Risk Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/risks/{risk_id}/close",
        "requires_evidence": True,
        "critical": True,
        "payload_template": {"role_id": "{role_id}", "evidence": "Riesgo cerrado con evidencia."},
    },
    {
        "id": "evaluate_policy",
        "label": "Evaluar politica",
        "description": "Evalua si un rol puede realizar una accion sobre un recurso.",
        "section": "Policy Center",
        "method": "POST",
        "endpoint": "/api/v1/governance/policies/evaluate",
        "payload_template": {"role_id": "{role_id}", "action": "approve", "resource": "platform"},
    },
)


class GovernanceError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_id(value: str) -> str:
    normalized = value.strip().lower()
    return APP_ALIASES.get(normalized, normalized)


def ensure_governance_schema() -> None:
    initialize_database()

    with connect() as connection:
        for table_name in [DECISIONS_TABLE, APPROVALS_TABLE, GATES_TABLE, RISKS_TABLE]:
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

    seed_integration_gates()


def insert_or_replace_payload(table_name: str, item_id: str, payload_json: str) -> None:
    placeholder = sql_placeholder()
    now = utc_now()

    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (item_id, payload_json, now, now),
        )
        connection.commit()


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_governance_schema()
    placeholder = sql_placeholder()

    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()

    return json.loads(row["payload_json"]) if row else None


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_governance_schema()

    with connect() as connection:
        rows = connection.execute(
            f"SELECT payload_json FROM {table_name} ORDER BY updated_at DESC"
        ).fetchall()

    return [json.loads(row["payload_json"]) for row in rows]


def audit_governance(
    source: str,
    action: str,
    status: str,
    detail: str,
    metadata: dict[str, object] | None = None,
    severity: AuditSeverity = AuditSeverity.info,
) -> AuditEvent:
    return create_audit_event(
        AuditEventCreate(
            category=AuditCategory.permission,
            severity=severity,
            source=source,
            action=action,
            status=status,
            detail=detail,
            metadata=metadata or {},
        )
    )


def append_audit_id(item, event: AuditEvent) -> None:
    item.audit_event_ids.append(event.id)


def require_approval_role(role_id: GovernanceRole, action: str) -> None:
    if role_id not in APPROVER_ROLES:
        event = audit_governance(
            source="governance.policy",
            action=action,
            status="denied",
            detail=f"Role {role_id.value} is not authorized for {action}.",
            metadata={"role_id": role_id.value},
            severity=AuditSeverity.medium,
        )
        raise GovernanceError(
            status_code=403,
            detail={
                "error": "role_not_authorized",
                "role_id": role_id.value,
                "action": action,
                "audit_event_id": event.id,
            },
        )


def action_allowed(role_id: GovernanceRole, action: str) -> bool:
    return role_id in ACTION_ROLES.get(action, set())


def action_denied_reason(role_id: GovernanceRole, action: str) -> str:
    if role_id == GovernanceRole.service and action not in {"evaluate_policy"}:
        return "service_role_has_no_human_ui_authority"
    if action in {"approve_connection", "approve_discovery", "block_gate", "suspend_gate"}:
        return "integration_gate_action_requires_ceo_or_admin"
    if action.startswith("approve") or action.startswith("reject") or action.startswith("block"):
        return "human_governance_action_requires_ceo_or_admin"
    return "role_not_authorized_for_action"


def require_action_role(role_id: GovernanceRole, action: str) -> None:
    if action_allowed(role_id, action):
        return

    reason = action_denied_reason(role_id, action)
    event = audit_governance(
        source="governance.auth_boundary",
        action=action,
        status="denied",
        detail=f"Role {role_id.value} is not authorized for {action}.",
        metadata={"role_id": role_id.value, "reason": reason},
        severity=AuditSeverity.medium,
    )
    raise GovernanceError(
        status_code=403,
        detail={
            "error": "role_not_authorized",
            "role_id": role_id.value,
            "action": action,
            "reason": reason,
            "audit_event_id": event.id,
        },
    )


def render_action_template(value: object, role_id: GovernanceRole) -> object:
    if isinstance(value, dict):
        return {key: render_action_template(nested, role_id) for key, nested in value.items()}
    if isinstance(value, list):
        return [render_action_template(item, role_id) for item in value]
    if value == "{role_id}":
        return role_id.value
    return value


def get_governance_auth_boundary(role_id: GovernanceRole) -> GovernanceAuthBoundary:
    actions: list[GovernanceActionDefinition] = []
    for item in ACTION_CATALOG:
        action_id = str(item["id"])
        allowed = action_allowed(role_id, action_id)
        reason = "allowed" if allowed else action_denied_reason(role_id, action_id)
        actions.append(
            GovernanceActionDefinition(
                id=action_id,
                label=str(item["label"]),
                description=str(item["description"]),
                section=str(item["section"]),
                method=str(item["method"]),
                endpoint=str(item["endpoint"]),
                allowed=allowed,
                reason=reason,
                requires_reason=bool(item.get("requires_reason", False)),
                requires_evidence=bool(item.get("requires_evidence", False)),
                critical=bool(item.get("critical", False)),
                payload_template=render_action_template(
                    item.get("payload_template", {}),
                    role_id,
                ),
            )
        )

    return GovernanceAuthBoundary(
        role_id=role_id,
        role_label=role_id.value.upper(),
        views_allowed=ROLE_VIEWS.get(role_id, []),
        actions=actions,
        denied_message="Tu rol puede ver esta informacion, pero no ejecutar esta accion.",
        external_connections_enabled=False,
        evaluated_at=utc_now(),
    )


def require_reason(reason: str | None, action: str) -> str:
    if not reason or not reason.strip():
        event = audit_governance(
            source="governance.validation",
            action=action,
            status="rejected",
            detail=f"{action} requires a human reason.",
            severity=AuditSeverity.medium,
        )
        raise GovernanceError(
            status_code=400,
            detail={
                "error": "reason_required",
                "action": action,
                "audit_event_id": event.id,
            },
        )

    return reason.strip()


def require_evidence(evidence: str | None, action: str) -> str:
    if not evidence or not evidence.strip():
        event = audit_governance(
            source="governance.validation",
            action=action,
            status="rejected",
            detail=f"{action} requires evidence.",
            severity=AuditSeverity.medium,
        )
        raise GovernanceError(
            status_code=400,
            detail={
                "error": "evidence_required",
                "action": action,
                "audit_event_id": event.id,
            },
        )

    return evidence.strip()


def default_gate_reason(protected: bool, planned_blocked: bool) -> str:
    if protected:
        return "Protected app remains blocked until explicit future governance phase."
    if planned_blocked:
        return "Planned app remains blocked until explicit CEO approval and a future integration phase."
    return "Application is registered but not ready for discovery."


def seed_integration_gates() -> None:
    placeholder = sql_placeholder()
    now = utc_now()

    with connect() as connection:
        for app in list_registered_apps():
            protected = app.id in PROTECTED_APP_IDS
            planned_blocked = app.id in PLANNED_BLOCKED_APP_IDS
            blocked_by_policy = protected or planned_blocked
            default_reason = default_gate_reason(protected, planned_blocked)
            state = (
                IntegrationGateState.blocked
                if blocked_by_policy
                else IntegrationGateState.not_ready
            )
            row = connection.execute(
                f"SELECT payload_json FROM {GATES_TABLE} WHERE id = {placeholder}",
                (app.id,),
            ).fetchone()

            if row:
                gate = IntegrationGate(**json.loads(row["payload_json"]))
                changed = False
                if gate.protected != protected:
                    gate.protected = protected
                    changed = True
                    if protected:
                        gate.state = IntegrationGateState.blocked
                        gate.reason = default_reason
                    elif gate.state == IntegrationGateState.blocked:
                        gate.state = IntegrationGateState.not_ready
                        gate.reason = default_reason
                if gate.app_name != app.name:
                    gate.app_name = app.name
                    changed = True
                if blocked_by_policy and gate.state != IntegrationGateState.blocked:
                    gate.state = IntegrationGateState.blocked
                    gate.reason = default_reason
                    changed = True
                if blocked_by_policy and gate.reason != default_reason:
                    gate.reason = default_reason
                    changed = True
                if changed:
                    gate.updated_at = now
                else:
                    continue
            else:
                gate = IntegrationGate(
                    app_id=app.id,
                    app_name=app.name,
                    state=state,
                    protected=protected,
                    reason=default_reason,
                    updated_at=now,
                )

            connection.execute(
                f"""
                INSERT INTO {GATES_TABLE} (id, payload_json, created_at, updated_at)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
                ON CONFLICT(id) DO UPDATE SET
                    payload_json = excluded.payload_json,
                    updated_at = excluded.updated_at
                """,
                (app.id, gate.model_dump_json(), now, now),
            )
        connection.commit()


def save_decision(decision: GovernanceDecision) -> GovernanceDecision:
    decision.updated_at = utc_now()
    insert_or_replace_payload(DECISIONS_TABLE, decision.id, decision.model_dump_json())
    return decision


def create_decision(request: GovernanceDecisionCreate) -> GovernanceDecision:
    ensure_governance_schema()
    require_action_role(request.requested_by, "create_decision")
    now = utc_now()
    decision = GovernanceDecision(
        id=str(uuid4()),
        title=request.title,
        description=request.description,
        requested_by=request.requested_by,
        status=request.status,
        evidence=request.evidence,
        metadata=request.metadata,
        created_at=now,
        updated_at=now,
    )
    event = audit_governance(
        source="governance.decisions",
        action="create_decision",
        status=decision.status.value,
        detail=f"Decision created: {decision.title}",
        metadata={"decision_id": decision.id},
    )
    append_audit_id(decision, event)
    return save_decision(decision)


def list_decisions() -> list[GovernanceDecision]:
    return [GovernanceDecision(**payload) for payload in fetch_payloads(DECISIONS_TABLE)]


def get_decision(decision_id: str) -> GovernanceDecision | None:
    payload = fetch_payload(DECISIONS_TABLE, decision_id)
    return GovernanceDecision(**payload) if payload else None


def require_decision(decision_id: str) -> GovernanceDecision:
    decision = get_decision(decision_id)
    if decision is None:
        raise GovernanceError(
            status_code=404,
            detail={"error": "decision_not_found", "decision_id": decision_id},
        )
    return decision


def approve_decision(
    decision_id: str,
    request: DecisionTransitionRequest,
) -> GovernanceDecision:
    require_action_role(request.role_id, "approve_decision")
    require_approval_role(request.role_id, "approve_decision")
    decision = require_decision(decision_id)
    decision.status = DecisionStatus.approved
    decision.approved_by = request.role_id
    decision.evidence = request.evidence or decision.evidence
    event = audit_governance(
        source="governance.decisions",
        action="approve_decision",
        status="approved",
        detail=f"Decision approved by {request.role_id.value}: {decision.title}",
        metadata={"decision_id": decision.id, "role_id": request.role_id.value},
    )
    append_audit_id(decision, event)
    return save_decision(decision)


def reject_decision(
    decision_id: str,
    request: DecisionTransitionRequest,
) -> GovernanceDecision:
    reason = require_reason(request.reason, "reject_decision")
    require_action_role(request.role_id, "reject_decision")
    require_approval_role(request.role_id, "reject_decision")
    decision = require_decision(decision_id)
    decision.status = DecisionStatus.rejected
    decision.rejected_by = request.role_id
    decision.reason = reason
    event = audit_governance(
        source="governance.decisions",
        action="reject_decision",
        status="rejected",
        detail=f"Decision rejected by {request.role_id.value}: {reason}",
        metadata={"decision_id": decision.id, "role_id": request.role_id.value},
        severity=AuditSeverity.medium,
    )
    append_audit_id(decision, event)
    return save_decision(decision)


def block_decision(
    decision_id: str,
    request: DecisionTransitionRequest,
) -> GovernanceDecision:
    reason = require_reason(request.reason, "block_decision")
    require_action_role(request.role_id, "block_decision")
    require_approval_role(request.role_id, "block_decision")
    decision = require_decision(decision_id)
    decision.status = DecisionStatus.blocked
    decision.blocked_by = request.role_id
    decision.reason = reason
    event = audit_governance(
        source="governance.decisions",
        action="block_decision",
        status="blocked",
        detail=f"Decision blocked by {request.role_id.value}: {reason}",
        metadata={"decision_id": decision.id, "role_id": request.role_id.value},
        severity=AuditSeverity.high,
    )
    append_audit_id(decision, event)
    return save_decision(decision)


def save_approval(approval: GovernanceApproval) -> GovernanceApproval:
    approval.updated_at = utc_now()
    insert_or_replace_payload(APPROVALS_TABLE, approval.id, approval.model_dump_json())
    return approval


def create_approval(request: GovernanceApprovalCreate) -> GovernanceApproval:
    ensure_governance_schema()
    require_action_role(request.requested_by, "create_approval")
    now = utc_now()
    approval = GovernanceApproval(
        id=str(uuid4()),
        title=request.title,
        description=request.description,
        approval_type=request.approval_type,
        requested_by=request.requested_by,
        target_id=normalize_id(request.target_id),
        status=ApprovalStatus.pending,
        expires_at=request.expires_at,
        evidence=request.evidence,
        metadata=request.metadata,
        created_at=now,
        updated_at=now,
    )
    event = audit_governance(
        source="governance.approvals",
        action="create_approval",
        status="pending",
        detail=f"Approval created: {approval.title}",
        metadata={"approval_id": approval.id, "target_id": approval.target_id},
    )
    append_audit_id(approval, event)
    return save_approval(approval)


def maybe_expire_approval(approval: GovernanceApproval) -> GovernanceApproval:
    if approval.status != ApprovalStatus.pending or not approval.expires_at:
        return approval

    try:
        expires_at = datetime.fromisoformat(approval.expires_at.replace("Z", "+00:00"))
    except ValueError:
        return approval

    if expires_at <= datetime.now(UTC):
        approval.status = ApprovalStatus.expired
        event = audit_governance(
            source="governance.approvals",
            action="expire_approval",
            status="expired",
            detail=f"Approval expired: {approval.title}",
            metadata={"approval_id": approval.id},
        )
        append_audit_id(approval, event)
        return save_approval(approval)

    return approval


def list_approvals() -> list[GovernanceApproval]:
    return [
        maybe_expire_approval(GovernanceApproval(**payload))
        for payload in fetch_payloads(APPROVALS_TABLE)
    ]


def list_pending_approvals() -> list[GovernanceApproval]:
    return [
        approval
        for approval in list_approvals()
        if approval.status == ApprovalStatus.pending
    ]


def get_approval(approval_id: str) -> GovernanceApproval | None:
    payload = fetch_payload(APPROVALS_TABLE, approval_id)
    return maybe_expire_approval(GovernanceApproval(**payload)) if payload else None


def require_approval(approval_id: str) -> GovernanceApproval:
    approval = get_approval(approval_id)
    if approval is None:
        raise GovernanceError(
            status_code=404,
            detail={"error": "approval_not_found", "approval_id": approval_id},
        )
    return approval


def approve_approval(
    approval_id: str,
    request: ApprovalTransitionRequest,
) -> GovernanceApproval:
    require_action_role(request.role_id, "approve_approval")
    require_approval_role(request.role_id, "approve_approval")
    approval = require_approval(approval_id)
    if approval.status != ApprovalStatus.pending:
        raise GovernanceError(
            status_code=409,
            detail={
                "error": "approval_not_pending",
                "approval_id": approval.id,
                "status": approval.status.value,
            },
        )
    approval.status = ApprovalStatus.approved
    approval.approved_by = request.role_id
    approval.evidence = request.evidence or approval.evidence
    event = audit_governance(
        source="governance.approvals",
        action="approve_approval",
        status="approved",
        detail=f"Approval granted by {request.role_id.value}: {approval.title}",
        metadata={"approval_id": approval.id, "role_id": request.role_id.value},
    )
    append_audit_id(approval, event)
    return save_approval(approval)


def reject_approval(
    approval_id: str,
    request: ApprovalTransitionRequest,
) -> GovernanceApproval:
    reason = require_reason(request.reason, "reject_approval")
    require_action_role(request.role_id, "reject_approval")
    require_approval_role(request.role_id, "reject_approval")
    approval = require_approval(approval_id)
    approval.status = ApprovalStatus.rejected
    approval.rejected_by = request.role_id
    approval.reason = reason
    event = audit_governance(
        source="governance.approvals",
        action="reject_approval",
        status="rejected",
        detail=f"Approval rejected by {request.role_id.value}: {reason}",
        metadata={"approval_id": approval.id, "role_id": request.role_id.value},
        severity=AuditSeverity.medium,
    )
    append_audit_id(approval, event)
    return save_approval(approval)


def escalate_approval(
    approval_id: str,
    request: ApprovalTransitionRequest,
) -> GovernanceApproval:
    reason = require_reason(request.reason, "escalate_approval")
    require_action_role(request.role_id, "escalate_approval")
    approval = require_approval(approval_id)
    if approval.status != ApprovalStatus.pending:
        raise GovernanceError(
            status_code=409,
            detail={
                "error": "approval_not_pending",
                "approval_id": approval.id,
                "status": approval.status.value,
            },
        )
    approval.status = ApprovalStatus.escalated
    approval.reason = reason
    approval.metadata["escalated_by"] = request.role_id.value
    event = audit_governance(
        source="governance.approvals",
        action="escalate_approval",
        status="escalated",
        detail=f"Approval escalated by {request.role_id.value}: {reason}",
        metadata={"approval_id": approval.id, "role_id": request.role_id.value},
        severity=AuditSeverity.medium,
    )
    append_audit_id(approval, event)
    return save_approval(approval)


def save_gate(gate: IntegrationGate) -> IntegrationGate:
    gate.updated_at = utc_now()
    insert_or_replace_payload(GATES_TABLE, gate.app_id, gate.model_dump_json())
    return gate


def list_integration_gates() -> list[IntegrationGate]:
    gates = [IntegrationGate(**payload) for payload in fetch_payloads(GATES_TABLE)]
    return sorted(gates, key=lambda gate: (gate.protected is False, gate.app_name.lower()))


def get_integration_gate(app_id: str) -> IntegrationGate | None:
    normalized_id = normalize_id(app_id)
    if get_registered_app(normalized_id) is None:
        return None
    payload = fetch_payload(GATES_TABLE, normalized_id)
    return IntegrationGate(**payload) if payload else None


def require_gate(app_id: str) -> IntegrationGate:
    gate = get_integration_gate(app_id)
    if gate is None:
        raise GovernanceError(
            status_code=404,
            detail={"error": "integration_gate_not_found", "app_id": app_id},
        )
    return gate


def require_not_planned_blocked(gate: IntegrationGate, action: str, error_code: str) -> None:
    if gate.app_id not in PLANNED_BLOCKED_APP_IDS:
        return

    gate.state = IntegrationGateState.blocked
    gate.reason = default_gate_reason(protected=False, planned_blocked=True)
    event = audit_governance(
        source="governance.integration_gates",
        action=action,
        status="blocked",
        detail=f"{gate.app_name} is planned only and remains blocked.",
        metadata={"app_id": gate.app_id, "state": gate.state.value},
        severity=AuditSeverity.high,
    )
    append_audit_id(gate, event)
    save_gate(gate)
    raise GovernanceError(
        status_code=400,
        detail={
            "error": error_code,
            "app_id": gate.app_id,
            "state": gate.state.value,
            "reason": "planned_pending_integration_no_runtime",
        },
    )


def request_gate_discovery(
    app_id: str,
    request: IntegrationGateTransitionRequest,
) -> IntegrationGate:
    require_action_role(request.role_id, "request_discovery")
    gate = require_gate(app_id)
    if gate.protected:
        event = audit_governance(
            source="governance.integration_gates",
            action="request_discovery",
            status="blocked",
            detail=f"{gate.app_name} is protected and remains blocked.",
            metadata={"app_id": gate.app_id},
            severity=AuditSeverity.high,
        )
        append_audit_id(gate, event)
        save_gate(gate)
        raise GovernanceError(
            status_code=400,
            detail={
                "error": "protected_app_discovery_blocked",
                "app_id": gate.app_id,
                "state": gate.state.value,
            },
        )

    require_not_planned_blocked(gate, "request_discovery", "planned_app_discovery_blocked")

    gate.state = IntegrationGateState.pending_approval
    gate.requested_by = request.role_id
    gate.reason = request.reason or "Discovery requested for registered app."
    event = audit_governance(
        source="governance.integration_gates",
        action="request_discovery",
        status="pending_approval",
        detail=f"Discovery approval requested for {gate.app_name}.",
        metadata={"app_id": gate.app_id, "role_id": request.role_id.value},
    )
    append_audit_id(gate, event)
    approval = create_approval(
        GovernanceApprovalCreate(
            title=f"Approve discovery for {gate.app_name}",
            description="Human approval required before discovery can start.",
            approval_type="integration_discovery",
            requested_by=request.role_id,
            target_id=gate.app_id,
            evidence=request.evidence,
        )
    )
    gate.approval_id = approval.id
    return save_gate(gate)


def approve_gate_discovery(
    app_id: str,
    request: IntegrationGateTransitionRequest,
) -> IntegrationGate:
    evidence = require_evidence(request.evidence, "approve_gate_discovery")
    require_action_role(request.role_id, "approve_discovery")
    require_approval_role(request.role_id, "approve_gate_discovery")
    gate = require_gate(app_id)
    if gate.protected:
        raise GovernanceError(
            status_code=400,
            detail={
                "error": "protected_app_discovery_blocked",
                "app_id": gate.app_id,
                "state": gate.state.value,
            },
        )

    require_not_planned_blocked(gate, "approve_discovery", "planned_app_discovery_blocked")

    gate.state = IntegrationGateState.approved_for_discovery
    gate.approved_by = request.role_id
    gate.evidence = evidence
    event = audit_governance(
        source="governance.integration_gates",
        action="approve_discovery",
        status="approved_for_discovery",
        detail=f"Discovery approved for {gate.app_name}.",
        metadata={"app_id": gate.app_id, "role_id": request.role_id.value},
    )
    append_audit_id(gate, event)
    return save_gate(gate)


def approve_gate_connection(
    app_id: str,
    request: IntegrationGateTransitionRequest,
) -> IntegrationGate:
    evidence = require_evidence(request.evidence, "approve_gate_connection")
    require_action_role(request.role_id, "approve_connection")
    require_approval_role(request.role_id, "approve_gate_connection")
    gate = require_gate(app_id)
    if gate.protected:
        raise GovernanceError(
            status_code=400,
            detail={
                "error": "protected_app_connection_blocked",
                "app_id": gate.app_id,
                "state": gate.state.value,
            },
        )

    require_not_planned_blocked(gate, "approve_connection", "planned_app_connection_blocked")

    gate.state = IntegrationGateState.approved_for_connection
    gate.approved_by = request.role_id
    gate.evidence = evidence
    event = audit_governance(
        source="governance.integration_gates",
        action="approve_connection",
        status="approved_for_connection",
        detail=(
            f"Connection was approved for {gate.app_name}, but no real app "
            "connection is executed in Governance V1."
        ),
        metadata={"app_id": gate.app_id, "role_id": request.role_id.value},
    )
    append_audit_id(gate, event)
    return save_gate(gate)


def block_gate(app_id: str, request: IntegrationGateTransitionRequest) -> IntegrationGate:
    reason = require_reason(request.reason, "block_integration_gate")
    require_action_role(request.role_id, "block_gate")
    require_approval_role(request.role_id, "block_integration_gate")
    gate = require_gate(app_id)
    gate.state = IntegrationGateState.blocked
    gate.reason = reason
    event = audit_governance(
        source="governance.integration_gates",
        action="block_gate",
        status="blocked",
        detail=f"Integration gate blocked for {gate.app_name}: {reason}",
        metadata={"app_id": gate.app_id, "role_id": request.role_id.value},
        severity=AuditSeverity.high,
    )
    append_audit_id(gate, event)
    return save_gate(gate)


def suspend_gate(
    app_id: str,
    request: IntegrationGateTransitionRequest,
) -> IntegrationGate:
    reason = require_reason(request.reason, "suspend_integration_gate")
    require_action_role(request.role_id, "suspend_gate")
    require_approval_role(request.role_id, "suspend_integration_gate")
    gate = require_gate(app_id)
    gate.state = IntegrationGateState.suspended
    gate.reason = reason
    event = audit_governance(
        source="governance.integration_gates",
        action="suspend_gate",
        status="suspended",
        detail=f"Integration gate suspended for {gate.app_name}: {reason}",
        metadata={"app_id": gate.app_id, "role_id": request.role_id.value},
        severity=AuditSeverity.high,
    )
    append_audit_id(gate, event)
    return save_gate(gate)


def list_policies() -> list[GovernancePolicy]:
    return [
        GovernancePolicy(
            id="human_approval_required",
            title="Human approval required for governance actions",
            status="active",
            enforced=True,
            rules=[
                "CEO and ADMIN may approve or reject human governance items.",
                "OPERATOR may request work but cannot approve it.",
                "AUDITOR may inspect evidence and audit history.",
                "SERVICE roles cannot make human decisions.",
            ],
        ),
        GovernancePolicy(
            id="protected_apps_blocked",
            title="DCFT, SENTINELA and ARSENAL remain blocked; discovery stays controlled",
            status="active",
            enforced=True,
            rules=[
                "DCFT remains protected and cannot be discovered or connected in this block.",
                "SENTINELA remains protected pending review and cannot be discovered or connected in this block.",
                "ARSENAL remains planned/pending integration and cannot be discovered, connected or executed in this block.",
                "FORJA and CEREBRO may be prepared for discovery only after human evidence approval.",
                "No runtime calls are made to external applications.",
            ],
        ),
        GovernancePolicy(
            id="evidence_required",
            title="Evidence required for approvals and risk closure",
            status="active",
            enforced=True,
            rules=[
                "Integration approval requires evidence.",
                "Risk closure requires evidence.",
                "Rejecting or blocking requires a reason.",
            ],
        ),
    ]


def evaluate_policy(request: PolicyEvaluationRequest) -> PolicyEvaluationResult:
    require_action_role(request.role_id, "evaluate_policy")
    action = request.action.strip().lower()
    resource = normalize_id(request.resource)
    allowed = False
    reason = "policy_denied"
    requires_human_approval = True

    if request.role_id == GovernanceRole.service and action in {
        "approve",
        "reject",
        "block",
        "connect",
    }:
        reason = "service_role_cannot_make_human_decisions"
    elif resource in PROTECTED_APP_IDS and "connect" in action:
        reason = "protected_app_connection_blocked"
    elif resource in PLANNED_BLOCKED_APP_IDS and any(
        keyword in action
        for keyword in ("connect", "discover", "execute", "activate", "runtime")
    ):
        reason = "planned_app_connection_blocked"
    elif action in {"approve", "reject", "block", "suspend"}:
        allowed = request.role_id in APPROVER_ROLES
        reason = "authorized_human_role" if allowed else "role_not_authorized"
    elif action in {"view", "read", "audit"}:
        allowed = True
        reason = "read_allowed"
        requires_human_approval = False
    elif action in {"request", "prepare"}:
        allowed = request.role_id in {
            GovernanceRole.ceo,
            GovernanceRole.admin,
            GovernanceRole.operator,
        }
        reason = "request_allowed" if allowed else "role_not_authorized"

    event = audit_governance(
        source="governance.policies",
        action="evaluate_policy",
        status="allowed" if allowed else "denied",
        detail=f"Policy evaluation for {request.role_id.value}:{action}:{resource}.",
        metadata={
            "role_id": request.role_id.value,
            "action": action,
            "resource": resource,
            "reason": reason,
        },
        severity=AuditSeverity.info if allowed else AuditSeverity.medium,
    )

    return PolicyEvaluationResult(
        id=str(uuid4()),
        role_id=request.role_id,
        action=action,
        resource=resource,
        allowed=allowed,
        reason=reason,
        requires_human_approval=requires_human_approval,
        audit_event_id=event.id,
        evaluated_at=utc_now(),
    )


def save_risk(risk: GovernanceRisk) -> GovernanceRisk:
    risk.updated_at = utc_now()
    insert_or_replace_payload(RISKS_TABLE, risk.id, risk.model_dump_json())
    return risk


def create_risk(request: GovernanceRiskCreate) -> GovernanceRisk:
    ensure_governance_schema()
    require_action_role(request.owner, "create_risk")
    now = utc_now()
    risk = GovernanceRisk(
        id=str(uuid4()),
        title=request.title,
        description=request.description,
        risk_type=request.risk_type,
        severity=request.severity,
        status=RiskStatus.open,
        owner=request.owner,
        evidence=request.evidence,
        metadata=request.metadata,
        created_at=now,
        updated_at=now,
    )
    event = audit_governance(
        source="governance.risks",
        action="create_risk",
        status="open",
        detail=f"Risk created: {risk.title}",
        metadata={"risk_id": risk.id, "severity": risk.severity.value},
        severity=(
            AuditSeverity.critical
            if risk.severity == RiskSeverity.critical
            else AuditSeverity.medium
        ),
    )
    append_audit_id(risk, event)
    return save_risk(risk)


def list_risks() -> list[GovernanceRisk]:
    return [GovernanceRisk(**payload) for payload in fetch_payloads(RISKS_TABLE)]


def get_risk(risk_id: str) -> GovernanceRisk | None:
    payload = fetch_payload(RISKS_TABLE, risk_id)
    return GovernanceRisk(**payload) if payload else None


def require_risk(risk_id: str) -> GovernanceRisk:
    risk = get_risk(risk_id)
    if risk is None:
        raise GovernanceError(
            status_code=404,
            detail={"error": "risk_not_found", "risk_id": risk_id},
        )
    return risk


def update_risk(risk_id: str, request: GovernanceRiskUpdate) -> GovernanceRisk:
    risk = require_risk(risk_id)
    update = request.model_dump(exclude_unset=True)
    for key, value in update.items():
        setattr(risk, key, value)

    event = audit_governance(
        source="governance.risks",
        action="update_risk",
        status="updated",
        detail=f"Risk updated: {risk.title}",
        metadata={"risk_id": risk.id},
    )
    append_audit_id(risk, event)
    return save_risk(risk)


def mitigate_risk(risk_id: str, request: RiskMitigationRequest) -> GovernanceRisk:
    require_action_role(request.role_id, "mitigate_risk")
    risk = require_risk(risk_id)
    risk.status = RiskStatus.mitigated
    risk.mitigation = request.mitigation
    risk.evidence = request.evidence or risk.evidence
    event = audit_governance(
        source="governance.risks",
        action="mitigate_risk",
        status="mitigated",
        detail=f"Risk mitigated by {request.role_id.value}: {request.mitigation}",
        metadata={"risk_id": risk.id, "role_id": request.role_id.value},
        severity=AuditSeverity.medium,
    )
    append_audit_id(risk, event)
    return save_risk(risk)


def close_risk(risk_id: str, request: RiskCloseRequest) -> GovernanceRisk:
    require_action_role(request.role_id, "close_risk")
    require_approval_role(request.role_id, "close_risk")
    risk = require_risk(risk_id)
    evidence = require_evidence(request.evidence, "close_risk")
    risk.status = RiskStatus.closed
    risk.closure_evidence = evidence
    event = audit_governance(
        source="governance.risks",
        action="close_risk",
        status="closed",
        detail=f"Risk closed by {request.role_id.value}.",
        metadata={"risk_id": risk.id, "role_id": request.role_id.value},
    )
    append_audit_id(risk, event)
    return save_risk(risk)


def list_governance_audit_events() -> list[AuditEvent]:
    events = list_audit_events()
    return [
        event
        for event in events
        if event.source.startswith("governance.")
        or str(event.metadata.get("governance", "")).lower() == "true"
    ]


def get_governance_report() -> GovernanceReport:
    ensure_governance_schema()
    decisions = list_decisions()
    approvals = list_approvals()
    gates = list_integration_gates()
    risks = list_risks()
    audit_events = list_governance_audit_events()
    pending_decisions = [
        item for item in decisions if item.status == "pending_review"
    ]
    pending_approvals = [
        item for item in approvals if item.status == ApprovalStatus.pending
    ]
    blocked_apps = [
        gate for gate in gates if gate.state == IntegrationGateState.blocked
    ]
    ready_for_discovery = [
        gate
        for gate in gates
        if gate.state == IntegrationGateState.approved_for_discovery
    ]
    open_risks = [risk for risk in risks if risk.status != RiskStatus.closed]
    critical_risks = [
        risk
        for risk in open_risks
        if risk.severity == RiskSeverity.critical
    ]
    protected_apps_blocked = all(
        any(
            gate.app_id == protected_app_id
            and gate.state == IntegrationGateState.blocked
            for gate in gates
        )
        for protected_app_id in PROTECTED_APP_IDS
    )

    return GovernanceReport(
        status=(
            "governance_attention_required"
            if pending_decisions or pending_approvals or critical_risks
            else "governance_ready"
        ),
        generated_at=utc_now(),
        pending_decisions=pending_decisions,
        pending_approvals=pending_approvals,
        blocked_apps=blocked_apps,
        ready_for_discovery=ready_for_discovery,
        open_risks=open_risks,
        critical_risks=critical_risks,
        decision_audit=[
            event
            for event in audit_events
            if event.source == "governance.decisions"
        ],
        approval_history=[
            event
            for event in audit_events
            if event.source == "governance.approvals"
        ],
        protected_apps_blocked=protected_apps_blocked,
        external_connections_enabled=False,
    )


def get_governance_overview() -> GovernanceOverview:
    report = get_governance_report()
    decisions = list_decisions()
    approvals = list_approvals()

    return GovernanceOverview(
        status=report.status,
        generated_at=report.generated_at,
        decisions=len(decisions),
        pending_decisions=len(report.pending_decisions),
        approvals=len(approvals),
        pending_approvals=len(report.pending_approvals),
        blocked_apps=len(report.blocked_apps),
        ready_for_discovery=len(report.ready_for_discovery),
        open_risks=len(report.open_risks),
        critical_risks=len(report.critical_risks),
        protected_apps_blocked=report.protected_apps_blocked,
        external_connections_enabled=False,
    )
