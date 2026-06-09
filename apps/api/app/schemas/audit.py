from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class AuditSeverity(StrEnum):
    info = "info"
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class AuditCategory(StrEnum):
    security = "security"
    configuration = "configuration"
    integration = "integration"
    memory = "memory"
    event = "event"
    permission = "permission"
    runtime = "runtime"
    deployment = "deployment"
    data_change = "data_change"
    error = "error"
    trace = "trace"


class AuditoriaReviewStatus(StrEnum):
    pending_review = "pending_review"
    in_review = "in_review"
    approved = "approved"
    observed = "observed"
    rejected = "rejected"
    blocked = "blocked"
    requires_ceo_decision = "requires_ceo_decision"


class AuditoriaObjectType(StrEnum):
    cerebro_task = "cerebro_task"
    bus_route = "bus_route"
    ceo_decision = "ceo_decision"
    report = "report"
    cabin = "cabin"
    department = "department"
    protected_product = "protected_product"
    deploy = "deploy"
    risk = "risk"


class AuditoriaCriterion(StrEnum):
    visual_quality = "visual_quality"
    functional_quality = "functional_quality"
    security = "security"
    costs = "costs"
    human_clarity = "human_clarity"
    ceo_standard = "ceo_standard"
    technical_readiness = "technical_readiness"
    operational_risk = "operational_risk"
    commercial_risk = "commercial_risk"
    legal_tax_risk = "legal_tax_risk"


class AuditCheck(BaseModel):
    id: str = Field(min_length=1)
    status: str = Field(pattern="^(pass|fail)$")
    detail: str = Field(min_length=1)


class AuditReport(BaseModel):
    id: str
    status: str = Field(pattern="^(pass|fail)$")
    checks: list[AuditCheck]
    created_at: str


class AuditEventCreate(BaseModel):
    category: AuditCategory
    severity: AuditSeverity = AuditSeverity.info
    source: str = Field(min_length=1)
    action: str = Field(min_length=1)
    status: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditEvent(BaseModel):
    id: str
    category: AuditCategory
    severity: AuditSeverity
    source: str
    action: str
    status: str
    detail: str
    metadata: dict[str, Any]
    created_at: str


class AuditOverview(BaseModel):
    status: str
    events: int
    reports: int
    severity_summary: dict[str, int]
    categories: list[AuditCategory]
    external_connections_enabled: bool


class AuditReportGenerateRequest(BaseModel):
    scope: str = Field(default="full", min_length=1)


class AuditoriaReviewCreate(BaseModel):
    object_type: AuditoriaObjectType
    reference: str = Field(min_length=1, max_length=240)
    source: str = Field(min_length=1, max_length=120)
    priority: str = Field(default="p2", pattern="^p[0-3]$")
    criteria: list[AuditoriaCriterion] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    blockages: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AuditoriaDecisionRequest(BaseModel):
    decision: AuditoriaReviewStatus
    observations: list[str] = Field(default_factory=list)
    blockages: list[str] = Field(default_factory=list)
    auditor: str = Field(default="auditoria", min_length=1, max_length=160)
    criteria_results: dict[str, str] = Field(default_factory=dict)


class AuditoriaReview(BaseModel):
    id: str
    object_type: AuditoriaObjectType
    reference: str
    source: str
    priority: str
    criteria: list[AuditoriaCriterion]
    status: AuditoriaReviewStatus
    result: AuditoriaReviewStatus
    observations: list[str]
    blockages: list[str]
    decision: AuditoriaReviewStatus | None = None
    auditor: str | None = None
    criteria_results: dict[str, str] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)
    requires_ceo_decision: bool = False
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    audit_event_ids: list[str] = Field(default_factory=list)
    created_at: str
    updated_at: str
    decided_at: str | None = None


class AuditoriaStatus(BaseModel):
    status: str
    pending_reviews: int
    in_review: int
    approved_reviews: int
    observed_reviews: int
    rejected_reviews: int
    blocked_reviews: int
    requires_ceo_decision: int
    queue: int
    criteria: list[AuditoriaCriterion]
    external_connection_enabled: bool = False
    runtime_connected: bool = False
