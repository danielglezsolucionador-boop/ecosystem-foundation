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
