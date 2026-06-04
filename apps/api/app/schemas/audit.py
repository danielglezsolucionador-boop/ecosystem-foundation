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
