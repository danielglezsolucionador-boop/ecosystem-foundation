from enum import StrEnum

from pydantic import BaseModel, Field


class RevenueOpportunityStatus(StrEnum):
    prepared = "prepared"
    evaluated = "evaluated"
    needs_more_data = "needs_more_data"
    waiting_ceo_approval = "waiting_ceo_approval"
    approval_requested = "approval_requested"
    rejected = "rejected"


class RevenueSprintRouteStatus(StrEnum):
    opportunity = "opportunity"
    prioritized = "prioritized"
    mission_created = "mission_created"
    needs_more_data = "needs_more_data"
    waiting_ceo_approval = "waiting_ceo_approval"
    blocked = "blocked"


class RevenueSprintEvidenceStatus(StrEnum):
    missing = "missing"
    partial = "partial"
    available = "available"


class RevenueSprintStatusValue(StrEnum):
    prepared = "prepared"
    running = "running"
    reported = "reported"


class RevenueEconomicMatrix(BaseModel):
    currency: str = Field(default="USD", min_length=1, max_length=12)
    investment_usd: float | None = Field(default=None, ge=0)
    expected_revenue_usd: float | None = Field(default=None, ge=0)
    expected_net_profit_usd: float | None = None
    probability_percent: float | None = Field(default=None, ge=0, le=100)
    weighted_expected_revenue_usd: float | None = None
    roi_percent: float | None = None
    payback_time: str = Field(default="not_estimated", min_length=1, max_length=160)
    risk: str = Field(default="controlled", min_length=1, max_length=120)
    monthly_goal_usd: float = Field(default=6000, gt=0)
    monthly_goal_contribution_percent: float | None = None
    ecommerce_goal_usd: float = Field(default=10000, gt=0)
    ecommerce_goal_contribution_percent: float | None = None
    status: str = Field(default="needs_more_data", min_length=1)
    recommendation: str = Field(min_length=1)


class RevenueGoal(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    monthly_target_usd: float = Field(gt=0)
    scope: str = Field(pattern="^(global|ecommerce)$")
    separated_from_global: bool
    actual_revenue_usd: float = Field(default=0, ge=0)
    actual_revenue_status: str = Field(default="no_real_revenue_reported", min_length=1)
    estimated_pipeline_usd: float = Field(default=0, ge=0)
    status: str = Field(default="active", min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class RevenueGoalCreate(BaseModel):
    id: str | None = Field(default=None, min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=180)
    monthly_target_usd: float = Field(gt=0)
    scope: str = Field(pattern="^(global|ecommerce)$")
    separated_from_global: bool = False
    status: str = Field(default="active", min_length=1, max_length=60)


class RevenueOpportunityCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    origin: str = Field(default="ceo_or_cerebro", min_length=1, max_length=120)
    department: str = Field(default="CEREBRO", min_length=1, max_length=120)
    related_product: str | None = Field(default=None, max_length=160)
    action_type: str = Field(default="organic", min_length=1, max_length=120)
    investment_usd: float | None = Field(default=None, ge=0)
    expected_revenue_usd: float | None = Field(default=None, ge=0)
    expected_net_profit_usd: float | None = None
    probability_percent: float | None = Field(default=None, ge=0, le=100)
    risk: str = Field(default="controlled", min_length=1, max_length=120)
    payback_time: str = Field(default="not_estimated", min_length=1, max_length=160)
    ecommerce_separate: bool = False
    recommendation: str | None = Field(default=None, max_length=800)
    status: RevenueOpportunityStatus | None = None


class RevenueOpportunityEvaluateRequest(BaseModel):
    investment_usd: float | None = Field(default=None, ge=0)
    expected_revenue_usd: float | None = Field(default=None, ge=0)
    expected_net_profit_usd: float | None = None
    probability_percent: float | None = Field(default=None, ge=0, le=100)
    risk: str | None = Field(default=None, max_length=120)
    payback_time: str | None = Field(default=None, max_length=160)
    recommendation: str | None = Field(default=None, max_length=800)


class RevenueOpportunity(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    origin: str = Field(min_length=1)
    department: str = Field(min_length=1)
    related_product: str | None = None
    action_type: str = Field(min_length=1)
    investment_usd: float | None = None
    expected_revenue_usd: float | None = None
    expected_net_profit_usd: float | None = None
    probability_percent: float | None = None
    risk: str = Field(min_length=1)
    payback_time: str = Field(min_length=1)
    ecommerce_separate: bool = False
    contributes_to_global_goal: bool
    contributes_to_ecommerce_goal: bool
    requires_ceo_approval: bool
    status: RevenueOpportunityStatus
    economic_matrix: RevenueEconomicMatrix
    approval_request_id: str | None = None
    cerebro_approval_request_id: str | None = None
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    real_revenue_confirmed: bool = False
    created_by: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class RevenueApprovalRequest(BaseModel):
    id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    department: str = Field(min_length=1)
    action_type: str = Field(min_length=1)
    status: str = Field(default="pending_ceo", min_length=1)
    economic_matrix: RevenueEconomicMatrix
    recommendation: str = Field(min_length=1)
    cerebro_approval_request_id: str | None = None
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class RevenueDepartmentContribution(BaseModel):
    department_id: str = Field(min_length=1)
    department_name: str = Field(min_length=1)
    revenue_role: str = Field(min_length=1)
    contribution_type: str = Field(min_length=1)
    target_scope: str = Field(pattern="^(global|ecommerce|indirect)$")
    estimated_pipeline_usd: float = Field(default=0, ge=0)
    opportunities: int = Field(default=0, ge=0)
    approval_requests: int = Field(default=0, ge=0)
    requires_ceo_approval_for_money: bool = True
    external_connection_enabled: bool = False
    runtime_connected: bool = False


class RevenueStatus(BaseModel):
    status: str = Field(min_length=1)
    mode: str = Field(min_length=1)
    global_goal: RevenueGoal
    ecommerce_goal: RevenueGoal
    actual_revenue_usd: float = Field(default=0, ge=0)
    actual_revenue_status: str = Field(default="no_real_revenue_reported", min_length=1)
    estimated_global_pipeline_usd: float = Field(default=0, ge=0)
    estimated_ecommerce_pipeline_usd: float = Field(default=0, ge=0)
    global_progress_percent: float = 0
    ecommerce_progress_percent: float = 0
    opportunities: int = Field(default=0, ge=0)
    opportunities_needing_data: int = Field(default=0, ge=0)
    approval_requests: int = Field(default=0, ge=0)
    top_opportunities: list[RevenueOpportunity] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False
    generated_at: str = Field(min_length=1)


class RevenueDailyReport(BaseModel):
    status: str = Field(min_length=1)
    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    global_goal_usd: float
    ecommerce_goal_usd: float
    global_pipeline_usd: float
    ecommerce_pipeline_usd: float
    approvals_pending: int
    opportunities_needing_data: int
    recommended_actions: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    generated_at: str = Field(min_length=1)


class RevenueSprintRouteCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    owner: str = Field(min_length=1, max_length=120)
    hypothesis: str = Field(min_length=1, max_length=800)
    next_actions: list[str] = Field(default_factory=list)
    investment_required_usd: float = Field(default=0, ge=0)
    action_type: str = Field(default="organic_validation", max_length=120)
    potential_estimated_usd: float | None = Field(default=None, ge=0)
    evidence_available: list[str] = Field(default_factory=list)
    evidence_missing: list[str] = Field(default_factory=list)
    evidence_status: RevenueSprintEvidenceStatus | None = None
    ecommerce_separate: bool = False
    priority: str | None = Field(default=None, pattern="^p[0-3]$")
    risk: str = Field(default="controlled", max_length=240)


class RevenueSprintMissionCreate(BaseModel):
    route_id: str = Field(min_length=1, max_length=160)
    title: str | None = Field(default=None, max_length=180)
    departments: list[str] = Field(default_factory=list)
    action_type: str = Field(default="organic_validation", max_length=120)
    expected_output: str = Field(default="Validar demanda y preparar evidencia sin venta real.", max_length=800)


class RevenueSprintReportCreate(BaseModel):
    summary: str = Field(min_length=1, max_length=1500)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)


class RevenueSprintRoute(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    status: RevenueSprintRouteStatus
    owner: str = Field(min_length=1)
    hypothesis: str = Field(min_length=1)
    next_actions: list[str] = Field(default_factory=list)
    investment_required_usd: float = Field(default=0, ge=0)
    approval_required: bool = False
    action_type: str = Field(default="organic_validation", min_length=1)
    potential_estimated_usd: float | None = None
    evidence_available: list[str] = Field(default_factory=list)
    evidence_missing: list[str] = Field(default_factory=list)
    evidence_status: RevenueSprintEvidenceStatus
    ecommerce_separate: bool = False
    priority: str = Field(default="p1", pattern="^p[0-3]$")
    roi_status: str = Field(default="not_estimated", min_length=1)
    risk: str = Field(default="controlled", min_length=1)
    real_revenue_confirmed: bool = False
    paid_campaign_launched: bool = False
    payment_connected: bool = False
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class RevenueSprintApprovalNeeded(BaseModel):
    status: str = Field(default="ok", min_length=1)
    mode: str = Field(default="prepared", min_length=1)
    approval_required: bool = False
    items: list[RevenueSprintRoute] = Field(default_factory=list)
    count: int = Field(default=0, ge=0)
    requires_ceo_action: bool = False
    message: str = Field(default="No revenue sprint approval requests pending.", min_length=1)
    fallback: bool = False
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    real_revenue_confirmed: bool = False


class RevenueSprintMission(BaseModel):
    id: str = Field(min_length=1)
    route_id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    departments: list[str] = Field(default_factory=list)
    status: str = Field(min_length=1)
    approval_required: bool = False
    ecommerce_separate: bool = False
    expected_output: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False


class RevenueSprintDaily(BaseModel):
    status: str = Field(min_length=1)
    day: int = Field(default=1, ge=1, le=30)
    headline: str = Field(min_length=1)
    plan_30_days: list[dict] = Field(default_factory=list)
    today_focus: list[str] = Field(default_factory=list)
    daily_tracking: list[str] = Field(default_factory=list)
    generated_at: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False


class RevenueSprintReport(BaseModel):
    id: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    actual_revenue_usd: float = Field(default=0, ge=0)
    real_revenue_confirmed: bool = False
    created_at: str = Field(min_length=1)


class RevenueSprintStatus(BaseModel):
    status: str = Field(min_length=1)
    sprint_status: RevenueSprintStatusValue
    global_goal_usd: float = Field(default=6000, gt=0)
    ecommerce_goal_usd: float = Field(default=10000, gt=0)
    actual_revenue_usd: float = Field(default=0, ge=0)
    actual_revenue_status: str = Field(default="no_real_revenue_reported", min_length=1)
    routes: int = Field(default=0, ge=0)
    prioritized_routes: int = Field(default=0, ge=0)
    missions: int = Field(default=0, ge=0)
    approval_needed: int = Field(default=0, ge=0)
    missing_evidence: int = Field(default=0, ge=0)
    ecommerce_routes: int = Field(default=0, ge=0)
    paid_campaigns_launched: int = Field(default=0, ge=0)
    top_routes: list[RevenueSprintRoute] = Field(default_factory=list)
    plan_30_days: list[dict] = Field(default_factory=list)
    next_action: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    generated_at: str = Field(min_length=1)
