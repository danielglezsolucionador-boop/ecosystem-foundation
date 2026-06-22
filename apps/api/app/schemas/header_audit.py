from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.arsenal import ArsenalOffice


class HeaderAuditClassification(StrEnum):
    defensive = "defensivo"
    pending_evidence = "pendiente_evidencia"
    discarded = "descartado"
    potential_review = "potencial_revision"


class HeaderAuditMode(StrEnum):
    localhost = "localhost"
    own_domain = "own_domain"
    authorized_scope = "authorized_scope"


class HeaderAuditEventMetadata(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_id: str | None = Field(
        default=None,
        min_length=3,
        max_length=180,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{2,179}$",
    )
    source: str | None = Field(
        default=None,
        min_length=2,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{1,79}$",
    )
    classification: str | None = Field(
        default=None,
        min_length=2,
        max_length=80,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{1,79}$",
    )


class HeaderAuditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    url: str = Field(min_length=8, max_length=2048)
    mode: HeaderAuditMode
    requesting_office: ArsenalOffice
    authorization_reference: str | None = Field(
        default=None,
        min_length=3,
        max_length=180,
        pattern=r"^[A-Za-z0-9][A-Za-z0-9_.:/-]{2,179}$",
    )
    event_metadata: HeaderAuditEventMetadata | None = None
    timeout_seconds: float = Field(default=8, ge=1, le=15)


class HeaderAuditFinding(BaseModel):
    id: str = Field(min_length=1)
    header: str = Field(min_length=1)
    classification: HeaderAuditClassification
    severity: str = Field(pattern="^(info|low|medium|high)$")
    summary: str = Field(min_length=1, max_length=500)
    evidence: str = Field(min_length=1, max_length=500)
    recommendation: str = Field(min_length=1, max_length=800)


class HeaderAuditReport(BaseModel):
    id: str = Field(min_length=1)
    resource_id: str = Field(min_length=1)
    resource_version: str = Field(min_length=1)
    target_url: str = Field(min_length=1)
    final_url: str = Field(min_length=1)
    host: str = Field(min_length=1)
    requesting_office: ArsenalOffice
    mode: HeaderAuditMode
    authorization_reference: str | None = None
    event_metadata: HeaderAuditEventMetadata | None = None
    http_status: int | None = Field(default=None, ge=100, le=599)
    request_method: str = Field(pattern="^(HEAD|GET|NONE)$")
    overall_classification: HeaderAuditClassification
    findings: list[HeaderAuditFinding] = Field(default_factory=list)
    classification_counts: dict[str, int] = Field(default_factory=dict)
    json_output: dict[str, Any] = Field(default_factory=dict)
    markdown_output: str = Field(min_length=1)
    audit_event_id: str = Field(min_length=1)
    network_request_executed: bool = False
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    secrets_stored: bool = False
    created_at: str = Field(min_length=1)
