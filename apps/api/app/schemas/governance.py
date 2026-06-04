from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from app.schemas.audit import AuditEvent


class GovernanceRole(StrEnum):
    ceo = "ceo"
    admin = "admin"
    operator = "operator"
    auditor = "auditor"
    service = "service"


class DecisionStatus(StrEnum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    blocked = "blocked"
    cancelled = "cancelled"


class ApprovalStatus(StrEnum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"
    expired = "expired"
    cancelled = "cancelled"


class ApprovalType(StrEnum):
    decision = "decision"
    integration_discovery = "integration_discovery"
    integration_connection = "integration_connection"
    policy_exception = "policy_exception"
    risk_acceptance = "risk_acceptance"
    deployment = "deployment"


class IntegrationGateState(StrEnum):
    blocked = "blocked"
    not_ready = "not_ready"
    pending_approval = "pending_approval"
    approved_for_discovery = "approved_for_discovery"
    approved_for_connection = "approved_for_connection"
    connected = "connected"
    suspended = "suspended"


class RiskType(StrEnum):
    technical = "technical"
    security = "security"
    operational = "operational"
    data = "data"
    integration = "integration"
    deployment = "deployment"


class RiskSeverity(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RiskStatus(StrEnum):
    open = "open"
    mitigated = "mitigated"
    closed = "closed"
    accepted = "accepted"


class GovernanceDecisionCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    requested_by: GovernanceRole = GovernanceRole.operator
    status: DecisionStatus = DecisionStatus.pending_review
    evidence: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceDecision(BaseModel):
    id: str
    title: str
    description: str
    requested_by: GovernanceRole
    status: DecisionStatus
    evidence: str | None
    reason: str | None = None
    approved_by: GovernanceRole | None = None
    rejected_by: GovernanceRole | None = None
    blocked_by: GovernanceRole | None = None
    audit_event_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class DecisionTransitionRequest(BaseModel):
    role_id: GovernanceRole = GovernanceRole.ceo
    reason: str | None = Field(default=None)
    evidence: str | None = Field(default=None)


class GovernanceApprovalCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    approval_type: ApprovalType
    requested_by: GovernanceRole = GovernanceRole.operator
    target_id: str = Field(min_length=1)
    expires_at: str | None = Field(default=None)
    evidence: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceApproval(BaseModel):
    id: str
    title: str
    description: str
    approval_type: ApprovalType
    requested_by: GovernanceRole
    target_id: str
    status: ApprovalStatus
    expires_at: str | None
    evidence: str | None
    reason: str | None = None
    approved_by: GovernanceRole | None = None
    rejected_by: GovernanceRole | None = None
    audit_event_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class ApprovalTransitionRequest(BaseModel):
    role_id: GovernanceRole = GovernanceRole.ceo
    reason: str | None = Field(default=None)
    evidence: str | None = Field(default=None)


class IntegrationGate(BaseModel):
    app_id: str
    app_name: str
    state: IntegrationGateState
    protected: bool
    requested_by: GovernanceRole | None = None
    approved_by: GovernanceRole | None = None
    reason: str | None = None
    evidence: str | None = None
    approval_id: str | None = None
    audit_event_ids: list[str] = Field(default_factory=list)
    updated_at: str


class IntegrationGateTransitionRequest(BaseModel):
    role_id: GovernanceRole = GovernanceRole.ceo
    reason: str | None = Field(default=None)
    evidence: str | None = Field(default=None)


class GovernancePolicy(BaseModel):
    id: str
    title: str
    status: str = Field(min_length=1)
    enforced: bool
    rules: list[str]


class PolicyEvaluationRequest(BaseModel):
    role_id: GovernanceRole
    action: str = Field(min_length=1)
    resource: str = Field(min_length=1)
    evidence: str | None = Field(default=None)


class PolicyEvaluationResult(BaseModel):
    id: str
    role_id: GovernanceRole
    action: str
    resource: str
    allowed: bool
    reason: str
    requires_human_approval: bool
    audit_event_id: str
    evaluated_at: str


class GovernanceRiskCreate(BaseModel):
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    risk_type: RiskType
    severity: RiskSeverity
    owner: GovernanceRole = GovernanceRole.operator
    evidence: str | None = Field(default=None)
    metadata: dict[str, Any] = Field(default_factory=dict)


class GovernanceRiskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1)
    description: str | None = Field(default=None, min_length=1)
    risk_type: RiskType | None = None
    severity: RiskSeverity | None = None
    owner: GovernanceRole | None = None
    evidence: str | None = None
    metadata: dict[str, Any] | None = None


class GovernanceRisk(BaseModel):
    id: str
    title: str
    description: str
    risk_type: RiskType
    severity: RiskSeverity
    status: RiskStatus
    owner: GovernanceRole
    evidence: str | None
    mitigation: str | None = None
    closure_evidence: str | None = None
    audit_event_ids: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)
    created_at: str
    updated_at: str


class RiskMitigationRequest(BaseModel):
    role_id: GovernanceRole = GovernanceRole.operator
    mitigation: str = Field(min_length=1)
    evidence: str | None = None


class RiskCloseRequest(BaseModel):
    role_id: GovernanceRole = GovernanceRole.ceo
    evidence: str | None = Field(default=None)


class GovernanceReport(BaseModel):
    status: str
    generated_at: str
    pending_decisions: list[GovernanceDecision]
    pending_approvals: list[GovernanceApproval]
    blocked_apps: list[IntegrationGate]
    ready_for_discovery: list[IntegrationGate]
    open_risks: list[GovernanceRisk]
    critical_risks: list[GovernanceRisk]
    decision_audit: list[AuditEvent]
    approval_history: list[AuditEvent]
    protected_apps_blocked: bool
    external_connections_enabled: bool


class GovernanceOverview(BaseModel):
    status: str
    generated_at: str
    decisions: int
    pending_decisions: int
    approvals: int
    pending_approvals: int
    blocked_apps: int
    ready_for_discovery: int
    open_risks: int
    critical_risks: int
    protected_apps_blocked: bool
    external_connections_enabled: bool
