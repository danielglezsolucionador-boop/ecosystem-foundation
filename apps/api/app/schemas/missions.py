from enum import StrEnum

from pydantic import BaseModel, Field


class MissionLoopStatus(StrEnum):
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


class MissionLoopStep(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    owner_department: str = Field(min_length=1)
    status: str = Field(default="pending", min_length=1)
    notes: str | None = None
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class MissionLoopEvent(BaseModel):
    id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    type: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    department: str = Field(default="CEREBRO", min_length=1)
    message: str = Field(min_length=1)
    status: str = Field(min_length=1)
    audit_event_id: str | None = None
    created_at: str = Field(min_length=1)


class MissionAssignment(BaseModel):
    id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    department: str = Field(min_length=1)
    instruction: str = Field(min_length=1)
    status: str = Field(default="assigned", min_length=1)
    created_at: str = Field(min_length=1)


class MissionAuditReviewLink(BaseModel):
    id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    review_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class MissionForgeRequest(BaseModel):
    id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    task_id: str = Field(min_length=1)
    status: str = Field(default="prepared", min_length=1)
    technical_status: str = Field(default="prepared", min_length=1)
    created_at: str = Field(min_length=1)


class MissionRevenueLink(BaseModel):
    id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    opportunity_id: str = Field(min_length=1)
    goal_scope: str = Field(default="global", min_length=1)
    economic_impact: str = Field(default="unknown", min_length=1)
    created_at: str = Field(min_length=1)


class MissionReport(BaseModel):
    id: str = Field(min_length=1)
    mission_id: str = Field(min_length=1)
    type: str = Field(default="ceo_report", min_length=1)
    summary: str = Field(min_length=1)
    status: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class MissionLoopCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    objective: str | None = Field(default=None, max_length=1500)
    ceo_instruction: str = Field(min_length=1, max_length=1500)
    source: str = Field(default="ceo_instruction", max_length=120)
    leader_department: str = Field(default="CEREBRO", max_length=120)
    involved_departments: list[str] = Field(default_factory=list)
    priority: str = Field(default="p1", pattern="^p[0-3]$")
    action_type: str = Field(default="internal_mission", max_length=120)
    expected_business_impact: str = Field(default="unknown", max_length=500)
    revenue_goal_link: str | None = Field(default=None, max_length=120)
    ecommerce_goal_link: str | None = Field(default=None, max_length=120)
    requires_money: bool = False
    requires_ceo_approval: bool | None = None
    approval_reason: str | None = Field(default=None, max_length=500)
    deadline: str | None = Field(default=None, max_length=120)
    investment_required: float = Field(default=0, ge=0)
    expected_revenue: float | None = Field(default=None, ge=0)
    ecommerce_separate: bool = False
    risk: str = Field(default="controlled", max_length=120)


class MissionLoopPlanRequest(BaseModel):
    steps: list[str] = Field(default_factory=list)
    involved_departments: list[str] = Field(default_factory=list)
    next_action: str | None = Field(default=None, max_length=500)


class MissionLoopAssignRequest(BaseModel):
    department: str | None = Field(default=None, min_length=1, max_length=120)
    departments: list[str] = Field(default_factory=list)
    instruction: str = Field(min_length=1, max_length=1000)


class MissionLoopDispatchRequest(BaseModel):
    department: str = Field(min_length=1, max_length=120)
    instruction: str = Field(min_length=1, max_length=1000)


class MissionLoopUpdateRequest(BaseModel):
    message: str = Field(min_length=1, max_length=1200)
    department: str = Field(default="CEREBRO", max_length=120)
    status: MissionLoopStatus | None = None
    next_action: str | None = Field(default=None, max_length=500)


class MissionLoopBlockRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)
    blocked_by: str = Field(default="CEREBRO", max_length=120)


class MissionLoopAuditRequest(BaseModel):
    reason: str = Field(default="Revisión interna solicitada por CEREBRO.", max_length=1000)
    priority: str = Field(default="p2", pattern="^p[0-3]$")
    criteria: list[str] = Field(default_factory=list)


class MissionLoopForjaRequest(BaseModel):
    instruction: str = Field(min_length=1, max_length=1000)
    title: str | None = Field(default=None, max_length=180)
    priority: str = Field(default="p1", pattern="^p[0-3]$")


class MissionLoopCompleteRequest(BaseModel):
    summary: str = Field(min_length=1, max_length=1500)
    evidence: str | None = Field(default=None, max_length=1000)


class MissionLoopMission(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    objective: str = Field(min_length=1)
    ceo_instruction: str = Field(min_length=1)
    source: str = Field(min_length=1)
    leader_department: str = Field(min_length=1)
    involved_departments: list[str] = Field(default_factory=list)
    priority: str = Field(pattern="^p[0-3]$")
    action_type: str = Field(min_length=1)
    expected_business_impact: str = Field(default="unknown", min_length=1)
    revenue_goal_link: str | None = None
    ecommerce_goal_link: str | None = None
    requires_money: bool = False
    requires_ceo_approval: bool = False
    approval_reason: str = Field(default="not_required", min_length=1)
    status: MissionLoopStatus
    current_phase: str = Field(min_length=1)
    next_action: str = Field(min_length=1)
    deadline: str | None = None
    steps: list[MissionLoopStep] = Field(default_factory=list)
    assignments: list[MissionAssignment] = Field(default_factory=list)
    events: list[MissionLoopEvent] = Field(default_factory=list)
    audit_reviews: list[MissionAuditReviewLink] = Field(default_factory=list)
    forge_requests: list[MissionForgeRequest] = Field(default_factory=list)
    revenue_links: list[MissionRevenueLink] = Field(default_factory=list)
    reports: list[MissionReport] = Field(default_factory=list)
    audit_trail: list[str] = Field(default_factory=list)
    technical_status: str = Field(default="prepared", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False
    local_agent_enabled: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class MissionDailyReport(BaseModel):
    status: str = Field(min_length=1)
    active_missions: int
    waiting_audit: int
    waiting_forge: int
    waiting_ceo_approval: int
    completed_today: int
    economic_impact_unknown: int
    morning_summary: str = Field(min_length=1)
    midday_summary: str = Field(min_length=1)
    evening_summary: str = Field(min_length=1)
    missions: list[MissionLoopMission] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    generated_at: str = Field(min_length=1)


class MissionTimeline(BaseModel):
    mission_id: str = Field(min_length=1)
    timeline: list[dict] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    generated_at: str = Field(min_length=1)
