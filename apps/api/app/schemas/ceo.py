from typing import Any

from pydantic import BaseModel, Field

from app.schemas.governance import GovernanceDecision


class CeoDecisionActionRequest(BaseModel):
    evidence: str | None = Field(default=None, max_length=800)
    reason: str | None = Field(default=None, max_length=800)


class CeoDailyItem(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    body: str = Field(min_length=1)
    status: str = Field(min_length=1)
    source: str = Field(min_length=1)
    meta: str | None = None
    requires_ceo_decision: bool = False
    blocked: bool = False


class CeoDailyAction(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    method: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    allowed: bool
    description: str = Field(min_length=1)
    blocked_reason: str | None = None


class CeoDailyView(BaseModel):
    type: str = Field(pattern="^(morning|evening)$")
    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    state_general: str = Field(min_length=1)
    decisions: list[CeoDailyItem] = Field(default_factory=list)
    opportunities: list[CeoDailyItem] = Field(default_factory=list)
    risks: list[CeoDailyItem] = Field(default_factory=list)
    tasks: list[CeoDailyItem] = Field(default_factory=list)
    internal_routes: list[CeoDailyItem] = Field(default_factory=list)
    blockages: list[CeoDailyItem] = Field(default_factory=list)
    cerebro_recommendation: str = Field(min_length=1)
    generated_at: str = Field(min_length=1)


class CeoDailyCenter(BaseModel):
    status: str = Field(min_length=1)
    mode: str = Field(default="ok", min_length=1)
    degraded: bool = False
    warnings: list[str] = Field(default_factory=list)
    generated_at: str = Field(min_length=1)
    executive_summary: str = Field(min_length=1)
    morning: CeoDailyView
    evening: CeoDailyView
    decisions: list[GovernanceDecision] = Field(default_factory=list)
    decisions_waiting_ceo: int
    active_tasks: int
    blocked_items: int
    opportunities: int
    risks: int
    cerebro: dict[str, Any] = Field(default_factory=dict)
    bus: dict[str, Any] = Field(default_factory=dict)
    governance: dict[str, Any] = Field(default_factory=dict)
    auditoria: dict[str, Any] = Field(default_factory=dict)
    nube: dict[str, Any] = Field(default_factory=dict)
    revenue: dict[str, Any] = Field(default_factory=dict)
    revenue_sprint: dict[str, Any] = Field(default_factory=dict)
    publishing: dict[str, Any] = Field(default_factory=dict)
    product_readiness: dict[str, Any] = Field(default_factory=dict)
    missions: dict[str, Any] = Field(default_factory=dict)
    workday: dict[str, Any] = Field(default_factory=dict)
    upgrades: dict[str, Any] = Field(default_factory=dict)
    protected_apps: list[str] = Field(default_factory=list)
    actions: list[CeoDailyAction] = Field(default_factory=list)
    next_action: str = Field(min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    local_agent_enabled: bool = False
