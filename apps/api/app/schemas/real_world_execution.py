from enum import StrEnum

from pydantic import BaseModel, Field


class RealWorldExecutionState(StrEnum):
    prepared = "prepared"
    ready_internal = "ready_internal"
    waiting_ceo = "waiting_ceo"
    waiting_credentials = "waiting_credentials"
    waiting_paid_approval = "waiting_paid_approval"
    waiting_account_creation = "waiting_account_creation"
    waiting_legal_review = "waiting_legal_review"
    blocked = "blocked"
    executed_manual_confirmed = "executed_manual_confirmed"
    executed_api_confirmed = "executed_api_confirmed"


class RealWorldExecutionPriority(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class RealWorldExecutionRisk(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    sensitive = "sensitive"


class RealWorldExecutionActionRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1200)
    evidence: str | None = Field(default=None, max_length=1200)
    reason: str | None = Field(default=None, max_length=1200)


class RealWorldExecutionQueueCreate(BaseModel):
    action: str = Field(min_length=1, max_length=220)
    area: str = Field(min_length=1, max_length=120)
    owner: str = Field(min_length=1, max_length=120)
    priority: RealWorldExecutionPriority = RealWorldExecutionPriority.medium
    state: RealWorldExecutionState = RealWorldExecutionState.prepared
    requires_ceo: bool = False
    requires_money: bool = False
    requires_credentials: bool = False
    requires_external_account: bool = False
    requires_legal_review: bool = False
    risk: RealWorldExecutionRisk = RealWorldExecutionRisk.medium
    economic_impact: str = Field(default="unknown", max_length=500)
    dependency: str = Field(default="none", max_length=500)
    evidence: str = Field(default="missing", max_length=1000)
    next_action: str = Field(default="Preparar internamente; no ejecutar accion real.", max_length=1000)
    target_date: str = Field(default="TBD", max_length=80)
    related_mission_id: str | None = Field(default=None, max_length=120)
    revenue_link: str | None = Field(default=None, max_length=160)
    workday_link: str | None = Field(default=None, max_length=160)


class RealWorldExecutionQueueItem(RealWorldExecutionQueueCreate):
    id: str = Field(min_length=1)
    can_execute_internally: bool = False
    ready_for_manual_execution: bool = False
    external_execution_enabled: bool = False
    payment_executed: bool = False
    publication_executed: bool = False
    account_created: bool = False
    credentials_stored: bool = False
    api_execution_confirmed: bool = False
    manual_execution_confirmed: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class RealWorldExecutionStatus(BaseModel):
    status: str = Field(default="real_world_execution_queue_prepared", min_length=1)
    mode: str = Field(default="prepared_local", min_length=1)
    total_items: int = Field(default=0, ge=0)
    prepared: int = Field(default=0, ge=0)
    ready_internal: int = Field(default=0, ge=0)
    waiting_ceo: int = Field(default=0, ge=0)
    waiting_credentials: int = Field(default=0, ge=0)
    waiting_paid_approval: int = Field(default=0, ge=0)
    waiting_account_creation: int = Field(default=0, ge=0)
    waiting_legal_review: int = Field(default=0, ge=0)
    blocked: int = Field(default=0, ge=0)
    approval_needed: int = Field(default=0, ge=0)
    money_needed: int = Field(default=0, ge=0)
    credentials_needed: int = Field(default=0, ge=0)
    high_risk: int = Field(default=0, ge=0)
    sensitive: int = Field(default=0, ge=0)
    manual_ready: int = Field(default=0, ge=0)
    next_steps: list[str] = Field(default_factory=list)
    queue_snapshot: list[RealWorldExecutionQueueItem] = Field(default_factory=list)
    external_execution_enabled: bool = False
    payment_executed: bool = False
    publication_executed: bool = False
    account_created: bool = False
    credentials_stored: bool = False
    generated_at: str = Field(min_length=1)
