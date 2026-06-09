from enum import StrEnum

from pydantic import BaseModel, Field


class UpgradePackageStatus(StrEnum):
    created = "created"
    prioritized = "prioritized"
    sent_to_forja = "sent_to_forja"
    waiting_implementation = "waiting_implementation"
    implemented_pending_audit = "implemented_pending_audit"
    waiting_audit = "waiting_audit"
    approved = "approved"
    rejected = "rejected"
    blocked = "blocked"


class UpgradeForgeStatus(StrEnum):
    not_sent = "not_sent"
    prepared = "prepared"
    pending_execution = "pending_execution"
    implemented_with_evidence = "implemented_with_evidence"


class UpgradeAuditStatus(StrEnum):
    not_requested = "not_requested"
    pending_review = "pending_review"
    in_review = "in_review"
    approved = "approved"
    rejected = "rejected"
    observed = "observed"


class UpgradeTechnicalStatus(StrEnum):
    prepared = "prepared"
    pending_execution = "pending_execution"
    evidence_recorded_pending_audit = "evidence_recorded_pending_audit"
    audit_approved = "audit_approved"
    audit_rejected = "audit_rejected"
    governed_pending_execution = "governed_pending_execution"


class UpgradePackageCreate(BaseModel):
    department_id: str = Field(min_length=1, max_length=120)
    source_audit_id: str | None = Field(default=None, max_length=180)
    gaps: list[str] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)
    priority: str | None = Field(default=None, pattern="^p[0-3]$")
    business_impact: str | None = Field(default=None, max_length=1000)
    revenue_link: str | None = Field(default=None, max_length=180)
    risk: str = Field(default="controlled", max_length=160)
    ceo_visibility: bool = True


class UpgradeForjaRequest(BaseModel):
    instruction: str | None = Field(default=None, max_length=1000)


class UpgradeImplementedRequest(BaseModel):
    evidence: str | None = Field(default=None, max_length=1200)
    implemented_by: str = Field(default="FORJA preparada", max_length=160)


class UpgradeReviewRequest(BaseModel):
    reason: str = Field(default="Revisión posterior de paquete de mejora.", max_length=1000)


class UpgradeDecisionRequest(BaseModel):
    reason: str = Field(min_length=1, max_length=1000)
    auditoria_review_id: str | None = Field(default=None, max_length=180)


class DepartmentGap(BaseModel):
    id: str = Field(min_length=1)
    package_id: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    gap: str = Field(min_length=1)
    source_audit_id: str | None = None
    created_at: str = Field(min_length=1)


class UpgradeEvidence(BaseModel):
    id: str = Field(min_length=1)
    package_id: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
    implemented_by: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class UpgradeStatusHistory(BaseModel):
    id: str = Field(min_length=1)
    package_id: str = Field(min_length=1)
    status: str = Field(min_length=1)
    message: str = Field(min_length=1)
    actor: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class ForgeWorkOrder(BaseModel):
    id: str = Field(min_length=1)
    package_id: str = Field(min_length=1)
    task_id: str | None = None
    status: UpgradeForgeStatus
    instruction: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class UpgradeReviewLink(BaseModel):
    id: str = Field(min_length=1)
    package_id: str = Field(min_length=1)
    review_id: str = Field(min_length=1)
    status: UpgradeAuditStatus
    created_at: str = Field(min_length=1)


class UpgradePackage(BaseModel):
    id: str = Field(min_length=1)
    department: str = Field(min_length=1)
    department_id: str = Field(min_length=1)
    department_status: str = Field(min_length=1)
    source_audit_id: str | None = None
    gaps: list[str] = Field(default_factory=list)
    required_changes: list[str] = Field(default_factory=list)
    priority: str = Field(pattern="^p[0-3]$")
    business_impact: str = Field(min_length=1)
    revenue_link: str | None = None
    risk: str = Field(min_length=1)
    forge_status: UpgradeForgeStatus
    audit_status: UpgradeAuditStatus
    ceo_visibility: bool = True
    technical_status: UpgradeTechnicalStatus
    status: UpgradePackageStatus
    forge_task_id: str | None = None
    audit_review_id: str | None = None
    evidence: list[UpgradeEvidence] = Field(default_factory=list)
    history: list[UpgradeStatusHistory] = Field(default_factory=list)
    work_orders: list[ForgeWorkOrder] = Field(default_factory=list)
    review_links: list[UpgradeReviewLink] = Field(default_factory=list)
    requires_ceo_approval: bool = False
    governance_status: str = Field(default="standard", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class UpgradeStatus(BaseModel):
    status: str = Field(min_length=1)
    packages: int = 0
    open_gaps: int = 0
    waiting_forge: int = 0
    waiting_audit: int = 0
    approved: int = 0
    rejected: int = 0
    governed_packages: int = 0
    supported_departments: list[str] = Field(default_factory=list)
    top_packages: list[UpgradePackage] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False
    generated_at: str = Field(min_length=1)
