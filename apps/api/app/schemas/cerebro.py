from enum import StrEnum

from pydantic import BaseModel, Field


class CerebroState(StrEnum):
    draft = "draft"
    proposed = "proposed"
    waiting_ceo = "waiting_ceo"
    approved = "approved"
    blocked = "blocked"
    delegated = "delegated"
    completed = "completed"
    rejected = "rejected"


class CerebroDecisionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1, max_length=1200)
    priority: str = Field(default="p1", pattern="^p[0-3]$")
    state: CerebroState = CerebroState.proposed
    reason: str | None = Field(default=None, max_length=500)
    requires_ceo_approval: bool = True


class CerebroDecision(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: str = Field(pattern="^p[0-3]$")
    state: CerebroState
    requested_by: str = Field(min_length=1)
    actor_role: str = Field(min_length=1)
    reason: str | None = None
    requires_ceo_approval: bool
    audit_event_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CerebroTaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1, max_length=1200)
    destination: str = Field(min_length=1, max_length=120)
    priority: str = Field(default="p1", pattern="^p[0-3]$")
    state: CerebroState | None = None
    reason: str | None = Field(default=None, max_length=500)
    requires_ceo_approval: bool | None = None


class CerebroTaskStateUpdate(BaseModel):
    state: CerebroState
    reason: str | None = Field(default=None, max_length=500)


class CerebroDepartmentRequest(BaseModel):
    destination: str = Field(min_length=1)
    destination_label: str = Field(min_length=1)
    allowed: bool
    state: CerebroState
    reason: str = Field(min_length=1)
    requires_ceo_approval: bool


class CerebroTask(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    destination: str = Field(min_length=1)
    destination_label: str = Field(min_length=1)
    priority: str = Field(pattern="^p[0-3]$")
    state: CerebroState
    blocked: bool
    reason: str = Field(min_length=1)
    requested_by: str = Field(min_length=1)
    actor_role: str = Field(min_length=1)
    requires_ceo_approval: bool
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    route_dispatched: bool = False
    bus_route_id: str | None = None
    bus_dispatch_id: str | None = None
    handler_result: dict = Field(default_factory=dict)
    audit_event_id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CerebroDailyBrief(BaseModel):
    type: str = Field(pattern="^(morning|evening|executive)$")
    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    decisions: list[CerebroDecision] = Field(default_factory=list)
    tasks: list[CerebroTask] = Field(default_factory=list)
    blocked: list[CerebroTask] = Field(default_factory=list)
    allowed_departments: list[str] = Field(default_factory=list)
    protected_targets: list[str] = Field(default_factory=list)
    requires_ceo_approval: bool
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    generated_at: str = Field(min_length=1)


class CerebroStatus(BaseModel):
    status: str = Field(min_length=1)
    mode: str = Field(min_length=1)
    role: str = Field(min_length=1)
    allowed_departments: list[str]
    protected_targets: list[str]
    decisions: int
    tasks: int
    blocked_tasks: int
    pending_decisions: int
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    local_agent_enabled: bool = False
    generated_at: str = Field(min_length=1)


class CerebroMissionState(StrEnum):
    created = "created"
    planned = "planned"
    assigned = "assigned"
    in_progress = "in_progress"
    waiting_department = "waiting_department"
    waiting_audit = "waiting_audit"
    waiting_forge = "waiting_forge"
    waiting_external_approval = "waiting_external_approval"
    waiting_ceo_approval = "waiting_ceo_approval"
    needs_clarification = "needs_clarification"
    completed = "completed"
    blocked = "blocked"
    rejected = "rejected"
    failed = "failed"


class CerebroAuthorityLevel(StrEnum):
    no_approval_required = "NO_APPROVAL_REQUIRED"
    ceo_approval_required = "CEO_APPROVAL_REQUIRED"


class CerebroEconomicMatrix(BaseModel):
    currency: str = "USD"
    investment_required: float = Field(default=0, ge=0)
    expected_revenue: float = Field(default=0, ge=0)
    expected_net_profit: float = 0
    monthly_goal: float = Field(default=6000, gt=0)
    monthly_goal_contribution_percent: float = 0
    return_time: str = Field(default="not_estimated", min_length=1)
    recommendation: str = Field(default="Preparar sin gasto real.", min_length=1)
    ecommerce_separate: bool = False


class CerebroDafo(BaseModel):
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)
    opportunities: list[str] = Field(default_factory=list)
    threats: list[str] = Field(default_factory=list)


class CerebroCompanyGoal(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    monthly_target_usd: float = Field(gt=0)
    ecommerce_separate: bool = False
    status: str = Field(default="active", min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CerebroCompanyGoalCreate(BaseModel):
    id: str | None = Field(default=None, min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1, max_length=1000)
    monthly_target_usd: float = Field(gt=0)
    ecommerce_separate: bool = False
    status: str = Field(default="active", max_length=60)


class CerebroDepartmentGoal(BaseModel):
    id: str = Field(min_length=1)
    department: str = Field(min_length=1)
    goal: str = Field(min_length=1)
    revenue_role: str = Field(min_length=1)
    operating_mode: str = Field(default="prepared_no_runtime", min_length=1)
    monthly_target_usd: float | None = Field(default=None, ge=0)
    requires_ceo_approval_for_money: bool = True
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CerebroDepartmentGoalCreate(BaseModel):
    id: str | None = Field(default=None, min_length=1, max_length=120)
    department: str = Field(min_length=1, max_length=120)
    goal: str = Field(min_length=1, max_length=1000)
    revenue_role: str = Field(min_length=1, max_length=500)
    operating_mode: str = Field(default="prepared_no_runtime", max_length=120)
    monthly_target_usd: float | None = Field(default=None, ge=0)
    requires_ceo_approval_for_money: bool = True


class CerebroMissionStep(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    owner_department: str = Field(min_length=1)
    status: str = Field(default="pending", min_length=1)
    notes: str | None = None
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CerebroMissionCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    objective: str = Field(min_length=1, max_length=1500)
    origin: str = Field(default="ceo_instruction", max_length=120)
    leader_department: str = Field(default="CEREBRO", max_length=120)
    involved_departments: list[str] = Field(default_factory=list)
    priority: str = Field(default="p1", pattern="^p[0-3]$")
    action_type: str = Field(default="internal_mission", max_length=120)
    estimated_economic_impact: float = Field(default=0, ge=0)
    relation_to_monthly_goal: str | None = Field(default=None, max_length=500)
    state: CerebroMissionState | None = None
    risks: list[str] = Field(default_factory=list)
    requires_money: bool = False
    requires_ceo_approval: bool | None = None
    expected_report: str = Field(default="Reporte ejecutivo a CEO.", max_length=800)
    investment_required: float = Field(default=0, ge=0)
    expected_revenue: float = Field(default=0, ge=0)
    ecommerce_separate: bool = False


class CerebroMissionUpdateCreate(BaseModel):
    status: str = Field(min_length=1, max_length=120)
    message: str = Field(min_length=1, max_length=1000)
    department: str = Field(default="CEREBRO", max_length=120)
    state: CerebroMissionState | None = None


class CerebroMissionDispatchRequest(BaseModel):
    department: str = Field(min_length=1, max_length=120)
    instruction: str = Field(min_length=1, max_length=1000)


class CerebroMissionUpdate(BaseModel):
    id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    department: str = Field(min_length=1)
    status: str = Field(min_length=1)
    message: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class CerebroMission(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    leader_department: str = Field(min_length=1)
    involved_departments: list[str] = Field(default_factory=list)
    priority: str = Field(pattern="^p[0-3]$")
    action_type: str = Field(min_length=1)
    authority_level: CerebroAuthorityLevel
    authority_reason: str = Field(min_length=1)
    estimated_economic_impact: float = 0
    relation_to_monthly_goal: str = Field(min_length=1)
    state: CerebroMissionState
    steps: list[CerebroMissionStep] = Field(default_factory=list)
    updates: list[CerebroMissionUpdate] = Field(default_factory=list)
    executed_actions: list[str] = Field(default_factory=list)
    pending_actions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    requires_money: bool = False
    requires_ceo_approval: bool
    expected_report: str = Field(min_length=1)
    economic_matrix: CerebroEconomicMatrix
    technical_status: str = Field(default="prepared", min_length=1)
    audit_trail: list[str] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    local_agent_enabled: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CerebroAlertCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    summary: str = Field(min_length=1, max_length=1000)
    source: str = Field(default="CEREBRO", max_length=120)
    relevance_score: int = Field(default=70, ge=0, le=100)
    risk_level: str = Field(default="medium", max_length=40)
    economic_impact: float = Field(default=0, ge=0)
    dafo: CerebroDafo = Field(default_factory=CerebroDafo)


class CerebroAlert(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    source: str = Field(min_length=1)
    relevance_score: int = Field(ge=0, le=100)
    relevance: str = Field(min_length=1)
    interrupt_ceo: bool = False
    risk_level: str = Field(min_length=1)
    economic_impact: float = 0
    dafo: CerebroDafo
    created_at: str = Field(min_length=1)


class CerebroRevenueOpportunityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1, max_length=1200)
    department: str = Field(default="CEREBRO", max_length=120)
    investment_required: float = Field(default=0, ge=0)
    expected_revenue: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", max_length=12)
    return_time: str = Field(default="not_estimated", max_length=120)
    risk: str = Field(default="controlled", max_length=120)
    ecommerce_separate: bool = False
    recommendation: str = Field(default="Preparar sin gasto real.", max_length=800)
    requires_ceo_approval: bool | None = None


class CerebroRevenueOpportunity(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    department: str = Field(min_length=1)
    economic_matrix: CerebroEconomicMatrix
    risk: str = Field(min_length=1)
    requires_ceo_approval: bool
    status: str = Field(default="prepared", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    created_at: str = Field(min_length=1)


class CerebroApprovalRequestCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    description: str = Field(min_length=1, max_length=1200)
    action_type: str = Field(min_length=1, max_length=120)
    requested_by_department: str = Field(default="CEREBRO", max_length=120)
    investment_required: float = Field(default=0, ge=0)
    expected_revenue: float = Field(default=0, ge=0)
    currency: str = Field(default="USD", max_length=12)
    return_time: str = Field(default="not_estimated", max_length=120)
    risk: str = Field(default="controlled", max_length=120)
    recommendation: str = Field(default="CEREBRO recomienda preparar sin gasto real.", max_length=800)
    ecommerce_separate: bool = False


class CerebroApprovalActionRequest(BaseModel):
    evidence: str | None = Field(default=None, max_length=800)
    reason: str | None = Field(default=None, max_length=800)


class CerebroApprovalRequest(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    requested_by_department: str = Field(min_length=1)
    authority_level: CerebroAuthorityLevel
    economic_matrix: CerebroEconomicMatrix
    risk: str = Field(min_length=1)
    recommendation: str = Field(min_length=1)
    status: str = Field(default="pending_ceo", min_length=1)
    requires_ceo_approval: bool = True
    approved_by: str | None = None
    rejected_by: str | None = None
    audit_trail: list[str] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CerebroCheckpoint(BaseModel):
    id: str = Field(min_length=1)
    type: str = Field(pattern="^(morning|midday|evening)$")
    title: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    timezone: str = "America/Lima"
    generated_at: str = Field(min_length=1)
    goals: list[CerebroCompanyGoal] = Field(default_factory=list)
    missions: list[CerebroMission] = Field(default_factory=list)
    alerts: list[CerebroAlert] = Field(default_factory=list)
    approval_requests: list[CerebroApprovalRequest] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False


class CerebroAuthorityRule(BaseModel):
    action_type: str = Field(min_length=1)
    level: CerebroAuthorityLevel
    reason: str = Field(min_length=1)
    technical_status: str = Field(default="prepared", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False


class CerebroChiefOfStaffStatus(BaseModel):
    status: str = Field(min_length=1)
    mode: str = Field(default="prepared", min_length=1)
    fallback: bool = False
    count: int = Field(default=0, ge=0)
    requires_ceo_action: bool = False
    message: str = Field(default="CEREBRO Chief of Staff status prepared.", min_length=1)
    role: str = Field(min_length=1)
    motto: str = Field(min_length=1)
    autonomy_policy: str = Field(default="prepared_no_external_runtime", min_length=1)
    autonomy_summary: str = Field(min_length=1)
    pending_definitions_status: str = Field(default="tracked_or_unknown", min_length=1)
    company_goals: list[CerebroCompanyGoal] = Field(default_factory=list)
    department_goals: list[CerebroDepartmentGoal] = Field(default_factory=list)
    active_missions: list[CerebroMission] = Field(default_factory=list)
    alerts: list[CerebroAlert] = Field(default_factory=list)
    approval_requests: list[CerebroApprovalRequest] = Field(default_factory=list)
    authority_matrix: list[CerebroAuthorityRule] = Field(default_factory=list)
    checkpoints: list[CerebroCheckpoint] = Field(default_factory=list)
    memory_policy: str = Field(min_length=1)
    business_memory: list[str] = Field(default_factory=list)
    bus_status: str = Field(default="prepared", min_length=1)
    auditoria_status: str = Field(default="prepared", min_length=1)
    forja_status: str = Field(default="prepared", min_length=1)
    nube_status: str = Field(default="prepared", min_length=1)
    centro_ceo_status: str = Field(default="integrated", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    local_agent_enabled: bool = False
    generated_at: str = Field(min_length=1)
