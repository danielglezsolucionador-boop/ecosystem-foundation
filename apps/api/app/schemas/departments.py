from enum import StrEnum

from pydantic import BaseModel, Field


class CabinStatus(StrEnum):
    complete = "complete"
    partial = "partial"
    missing = "missing"
    unknown = "unknown"


class DepartmentOperationalStatus(StrEnum):
    ready = "ready"
    partial = "partial"
    needs_forge = "needs_forge"
    needs_audit = "needs_audit"
    blocked = "blocked"
    governed = "governed"
    unknown = "unknown"


class DepartmentAuditStatus(StrEnum):
    generated = "generated"
    sent_to_forja = "sent_to_forja"
    sent_to_cerebro = "sent_to_cerebro"
    reviewed = "reviewed"
    blocked = "blocked"


class DepartmentCabinEvidence(BaseModel):
    status: CabinStatus
    sources: list[str] = Field(default_factory=list)
    notes: str = Field(min_length=1)


class DepartmentRecord(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    aliases: list[str] = Field(default_factory=list)
    purpose: str = Field(min_length=1)
    goals: list[str] = Field(default_factory=list)
    expected_functions: list[str] = Field(default_factory=list)
    revenue_relation: str = Field(min_length=1)
    cerebro_relation: str = Field(min_length=1)
    auditoria_relation: str = Field(min_length=1)
    forja_relation: str = Field(min_length=1)
    nube_relation: str = Field(min_length=1)
    heart_cabin: DepartmentCabinEvidence
    technical_cabin: DepartmentCabinEvidence
    human_cabin: DepartmentCabinEvidence
    operational_status: DepartmentOperationalStatus
    risks: list[str] = Field(default_factory=list)
    missing_data: list[str] = Field(default_factory=list)
    commercial_readiness: CabinStatus
    technical_readiness: CabinStatus
    human_readiness: CabinStatus
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    secrets_required: bool = False


class DepartmentAuditCreate(BaseModel):
    requested_by: str = Field(default="CEREBRO", max_length=120)
    instruction: str | None = Field(default=None, max_length=1000)
    create_cerebro_mission: bool = False


class DepartmentAuditActionRequest(BaseModel):
    reason: str | None = Field(default=None, max_length=800)
    evidence: str | None = Field(default=None, max_length=800)


class DepartmentAudit(BaseModel):
    id: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    department_name: str = Field(min_length=1)
    requested_by: str = Field(min_length=1)
    instruction: str | None = None
    sources_reviewed: list[str] = Field(default_factory=list)
    heart_cabin: DepartmentCabinEvidence
    technical_cabin: DepartmentCabinEvidence
    human_cabin: DepartmentCabinEvidence
    gaps: list[str] = Field(default_factory=list)
    suggested_tasks: list[str] = Field(default_factory=list)
    priority: str = Field(default="p1", pattern="^p[0-3]$")
    economic_impact: str = Field(min_length=1)
    risk: str = Field(min_length=1)
    status: DepartmentAuditStatus
    operational_status: DepartmentOperationalStatus
    recommendation: str = Field(min_length=1)
    requires_forja: bool = False
    requires_ceo: bool = False
    forja_task_id: str | None = None
    cerebro_mission_id: str | None = None
    audit_trail: list[str] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
