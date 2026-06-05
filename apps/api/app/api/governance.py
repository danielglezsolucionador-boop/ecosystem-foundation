from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.audit import AuditEvent
from app.schemas.governance import (
    ApprovalTransitionRequest,
    DecisionTransitionRequest,
    GovernanceAuthBoundary,
    GovernanceApproval,
    GovernanceApprovalCreate,
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
    IntegrationGateTransitionRequest,
    PolicyEvaluationRequest,
    PolicyEvaluationResult,
    RiskCloseRequest,
    RiskMitigationRequest,
)
from app.services.governance import (
    GovernanceError,
    approve_approval,
    approve_decision,
    approve_gate_connection,
    approve_gate_discovery,
    block_decision,
    block_gate,
    close_risk,
    create_approval,
    create_decision,
    create_risk,
    evaluate_policy,
    escalate_approval,
    get_approval,
    get_decision,
    get_governance_auth_boundary,
    get_governance_overview,
    get_governance_report,
    get_integration_gate,
    get_risk,
    list_approvals,
    list_decisions,
    list_governance_audit_events,
    list_integration_gates,
    list_pending_approvals,
    list_policies,
    list_risks,
    mitigate_risk,
    reject_approval,
    reject_decision,
    request_gate_discovery,
    suspend_gate,
    update_risk,
)
from app.schemas.auth import AuthenticatedUser
from app.services.auth import get_current_user, governance_role, require_control_center_user

router = APIRouter(
    prefix="/api/v1/governance",
    tags=["governance"],
    dependencies=[Depends(require_control_center_user)],
)


def raise_governance_error(error: GovernanceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


def role_from_user(user: AuthenticatedUser) -> GovernanceRole:
    return GovernanceRole(governance_role(user.role))


@router.get("", response_model=GovernanceOverview)
def read_governance_overview() -> GovernanceOverview:
    return get_governance_overview()


@router.get("/auth-boundary", response_model=GovernanceAuthBoundary)
def read_governance_auth_boundary(
    role_id: GovernanceRole = GovernanceRole.ceo,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceAuthBoundary:
    return get_governance_auth_boundary(role_from_user(current_user))


@router.get("/decisions", response_model=list[GovernanceDecision])
def read_decisions() -> list[GovernanceDecision]:
    return list_decisions()


@router.post(
    "/decisions",
    response_model=GovernanceDecision,
    status_code=status.HTTP_201_CREATED,
)
def write_decision(
    request: GovernanceDecisionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceDecision:
    try:
        request = request.model_copy(update={"requested_by": role_from_user(current_user)})
        return create_decision(request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.get("/decisions/{decision_id}", response_model=GovernanceDecision)
def read_decision(decision_id: str) -> GovernanceDecision:
    decision = get_decision(decision_id)
    if decision is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "decision_not_found", "decision_id": decision_id},
        )
    return decision


@router.post("/decisions/{decision_id}/approve", response_model=GovernanceDecision)
def approve_governance_decision(
    decision_id: str,
    request: DecisionTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceDecision:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return approve_decision(decision_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/decisions/{decision_id}/reject", response_model=GovernanceDecision)
def reject_governance_decision(
    decision_id: str,
    request: DecisionTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceDecision:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return reject_decision(decision_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/decisions/{decision_id}/block", response_model=GovernanceDecision)
def block_governance_decision(
    decision_id: str,
    request: DecisionTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceDecision:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return block_decision(decision_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.get("/approvals", response_model=list[GovernanceApproval])
def read_approvals() -> list[GovernanceApproval]:
    return list_approvals()


@router.post(
    "/approvals",
    response_model=GovernanceApproval,
    status_code=status.HTTP_201_CREATED,
)
def write_approval(
    request: GovernanceApprovalCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceApproval:
    try:
        request = request.model_copy(update={"requested_by": role_from_user(current_user)})
        return create_approval(request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.get("/approvals/pending", response_model=list[GovernanceApproval])
def read_pending_approvals() -> list[GovernanceApproval]:
    return list_pending_approvals()


@router.get("/approvals/{approval_id}", response_model=GovernanceApproval)
def read_approval(approval_id: str) -> GovernanceApproval:
    approval = get_approval(approval_id)
    if approval is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "approval_not_found", "approval_id": approval_id},
        )
    return approval


@router.post("/approvals/{approval_id}/approve", response_model=GovernanceApproval)
def approve_governance_approval(
    approval_id: str,
    request: ApprovalTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceApproval:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return approve_approval(approval_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/approvals/{approval_id}/reject", response_model=GovernanceApproval)
def reject_governance_approval(
    approval_id: str,
    request: ApprovalTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceApproval:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return reject_approval(approval_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/approvals/{approval_id}/escalate", response_model=GovernanceApproval)
def escalate_governance_approval(
    approval_id: str,
    request: ApprovalTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceApproval:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return escalate_approval(approval_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.get("/integration-gates", response_model=list[IntegrationGate])
def read_integration_gates() -> list[IntegrationGate]:
    return list_integration_gates()


@router.get("/integration-gates/{app_id}", response_model=IntegrationGate)
def read_integration_gate(app_id: str) -> IntegrationGate:
    gate = get_integration_gate(app_id)
    if gate is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "integration_gate_not_found", "app_id": app_id},
        )
    return gate


@router.post("/integration-gates/{app_id}/request-discovery", response_model=IntegrationGate)
def request_integration_gate_discovery(
    app_id: str,
    request: IntegrationGateTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationGate:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return request_gate_discovery(app_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/integration-gates/{app_id}/approve-discovery", response_model=IntegrationGate)
def approve_integration_gate_discovery(
    app_id: str,
    request: IntegrationGateTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationGate:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return approve_gate_discovery(app_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/integration-gates/{app_id}/approve-connection", response_model=IntegrationGate)
def approve_integration_gate_connection(
    app_id: str,
    request: IntegrationGateTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationGate:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return approve_gate_connection(app_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/integration-gates/{app_id}/block", response_model=IntegrationGate)
def block_integration_gate(
    app_id: str,
    request: IntegrationGateTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationGate:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return block_gate(app_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/integration-gates/{app_id}/suspend", response_model=IntegrationGate)
def suspend_integration_gate(
    app_id: str,
    request: IntegrationGateTransitionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> IntegrationGate:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return suspend_gate(app_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.get("/policies", response_model=list[GovernancePolicy])
def read_policies() -> list[GovernancePolicy]:
    return list_policies()


@router.post("/policies/evaluate", response_model=PolicyEvaluationResult)
def evaluate_governance_policy(
    request: PolicyEvaluationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PolicyEvaluationResult:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return evaluate_policy(request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.get("/risks", response_model=list[GovernanceRisk])
def read_risks() -> list[GovernanceRisk]:
    return list_risks()


@router.post(
    "/risks",
    response_model=GovernanceRisk,
    status_code=status.HTTP_201_CREATED,
)
def write_risk(
    request: GovernanceRiskCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceRisk:
    try:
        request = request.model_copy(update={"owner": role_from_user(current_user)})
        return create_risk(request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.get("/risks/{risk_id}", response_model=GovernanceRisk)
def read_risk(risk_id: str) -> GovernanceRisk:
    risk = get_risk(risk_id)
    if risk is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "risk_not_found", "risk_id": risk_id},
        )
    return risk


@router.put("/risks/{risk_id}", response_model=GovernanceRisk)
def update_governance_risk(
    risk_id: str,
    request: GovernanceRiskUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceRisk:
    try:
        if request.owner is not None:
            request = request.model_copy(update={"owner": role_from_user(current_user)})
        return update_risk(risk_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/risks/{risk_id}/mitigate", response_model=GovernanceRisk)
def mitigate_governance_risk(
    risk_id: str,
    request: RiskMitigationRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceRisk:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return mitigate_risk(risk_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/risks/{risk_id}/close", response_model=GovernanceRisk)
def close_governance_risk(
    risk_id: str,
    request: RiskCloseRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceRisk:
    try:
        request = request.model_copy(update={"role_id": role_from_user(current_user)})
        return close_risk(risk_id, request)
    except GovernanceError as error:
        raise_governance_error(error)


@router.get("/audit", response_model=list[AuditEvent])
def read_governance_audit() -> list[AuditEvent]:
    return list_governance_audit_events()


@router.get("/reports", response_model=GovernanceReport)
def read_governance_report() -> GovernanceReport:
    return get_governance_report()
