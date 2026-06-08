from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ControlCenterState(StrEnum):
    healthy = "healthy"
    degraded = "degraded"
    blocked = "blocked"
    unknown = "unknown"


class AlertSeverity(StrEnum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class ControlCenterEvidence(BaseModel):
    source: str = Field(min_length=1)
    status: ControlCenterState
    detail: str = Field(min_length=1)


class ControlCenterMetric(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    value: int | str | bool
    unit: str | None = None
    status: ControlCenterState
    source: str = Field(min_length=1)


class ControlCenterAction(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    priority: str = Field(pattern="^p[0-3]$")
    blocked: bool
    owner_view: str = Field(pattern="^(ceo|operational)$")
    reason: str = Field(min_length=1)


class ControlCenterApplicationStatus(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    registry_status: str = Field(min_length=1)
    status: ControlCenterState
    depends_on: list[str] = Field(default_factory=list)
    touch_policy: str = Field(min_length=1)
    role: str | None = None
    commercial_role: str | None = None
    controlled_state: str | None = None
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    requires_ceo_approval: bool = True
    governance_execution_blocked: bool = True
    secrets_required: bool = False
    human_cabin_complete: bool = True
    evidence: list[ControlCenterEvidence] = Field(default_factory=list)


class ControlCenterServiceStatus(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    category: str = Field(min_length=1)
    status: ControlCenterState
    detail: str = Field(min_length=1)
    evidence: list[ControlCenterEvidence] = Field(default_factory=list)


class ControlCenterDependencyStatus(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: str = Field(min_length=1)
    required: bool
    status: ControlCenterState
    detail: str = Field(min_length=1)
    evidence: list[ControlCenterEvidence] = Field(default_factory=list)


class ControlCenterRuntimeStatus(BaseModel):
    status: ControlCenterState
    service: str = Field(min_length=1)
    environment: str = Field(min_length=1)
    version: str = Field(min_length=1)
    commit: str = Field(min_length=1)
    database_backend: str = Field(min_length=1)
    database_persistent: bool
    database_source: str = Field(min_length=1)
    external_connections_enabled: bool = False
    generated_at: str = Field(min_length=1)


class ExecutiveSummary(BaseModel):
    status: ControlCenterState
    headline: str = Field(min_length=1)
    summary: str = Field(min_length=1)
    decision_required: bool
    focus: list[str] = Field(default_factory=list)


class OperationalSummary(BaseModel):
    status: ControlCenterState
    active_services: int
    degraded_services: int
    blocked_items: int
    unknown_items: int
    external_connections_enabled: bool = False
    notes: list[str] = Field(default_factory=list)


class AlertSummary(BaseModel):
    id: str = Field(min_length=1)
    severity: AlertSeverity
    status: ControlCenterState
    message: str = Field(min_length=1)
    source: str = Field(min_length=1)
    action_required: bool


class ReadinessCheck(BaseModel):
    id: str = Field(min_length=1)
    label: str = Field(min_length=1)
    status: ControlCenterState
    required: bool
    detail: str = Field(min_length=1)


class ReadinessSummary(BaseModel):
    status: ControlCenterState
    ready_for_external_connections: bool
    checks: list[ReadinessCheck]


class ControlCenterOverview(BaseModel):
    status: ControlCenterState
    registry_source: str
    external_connections_enabled: bool
    executive_summary: ExecutiveSummary
    operational_summary: OperationalSummary
    metrics: list[ControlCenterMetric]
    next_actions: list[ControlCenterAction]
    risks: list[str]


class ControlCenterStatus(BaseModel):
    status: ControlCenterState
    runtime: ControlCenterRuntimeStatus
    applications: list[ControlCenterApplicationStatus]
    services: list[ControlCenterServiceStatus]
    dependencies: list[ControlCenterDependencyStatus]


class ControlCenterAuditEvent(BaseModel):
    id: str
    event_type: str
    status: ControlCenterState
    payload: dict[str, Any]
    created_at: str


class ControlCenterResponse(BaseModel):
    status: ControlCenterState
    generated_at: str
    audit_event_id: str | None
    overview: ControlCenterOverview
    status_summary: ControlCenterStatus
    applications: list[ControlCenterApplicationStatus]
    services: list[ControlCenterServiceStatus]
    dependencies: list[ControlCenterDependencyStatus]
    metrics: list[ControlCenterMetric]
    alerts: list[AlertSummary]
    readiness: ReadinessSummary
    executive_view: ExecutiveSummary
    operational_view: OperationalSummary
