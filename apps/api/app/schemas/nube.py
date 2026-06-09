from typing import Any

from pydantic import BaseModel, ConfigDict, Field


MASKED_VALUE = "***masked***"


class CloudProvider(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=180)
    provider_type: str = Field(default="hosting", min_length=1, max_length=80)
    status: str = Field(default="registered", min_length=1, max_length=80)
    external_api_connected: bool = False


class CloudDatabase(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=180)
    engine: str = Field(min_length=1, max_length=80)
    status: str = Field(default="registered", min_length=1, max_length=80)
    persistent: bool = True
    temporal: bool = False


class CloudVariableCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=160)
    status: str = Field(default="unknown", min_length=1, max_length=80)
    required: bool = True
    sensitive: bool = True
    notes: str | None = Field(default=None, max_length=300)


class CloudVariable(CloudVariableCreate):
    value: str = MASKED_VALUE


class CloudBackup(BaseModel):
    id: str = Field(min_length=1, max_length=160)
    label: str = Field(min_length=1, max_length=220)
    status: str = Field(default="registered", min_length=1, max_length=80)
    location: str = Field(default="internal_backup_registry", min_length=1, max_length=220)
    created_at: str | None = None


class CloudDomain(BaseModel):
    id: str = Field(min_length=1, max_length=160)
    domain: str = Field(min_length=1, max_length=220)
    status: str = Field(default="registered", min_length=1, max_length=80)
    provider: str | None = Field(default=None, max_length=160)


class CloudProjectCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    id: str | None = Field(default=None, max_length=120)
    name: str = Field(min_length=1, max_length=180)
    production_url: str | None = Field(default=None, max_length=300)
    control_center_url: str | None = Field(default=None, max_length=300)
    provider: str = Field(default="unknown", min_length=1, max_length=120)
    status: str = Field(default="registered", min_length=1, max_length=80)
    last_commit: str | None = Field(default=None, max_length=80)
    tags: list[str] = Field(default_factory=list)
    providers: list[CloudProvider] = Field(default_factory=list)
    databases: list[CloudDatabase] = Field(default_factory=list)
    variables: list[CloudVariableCreate] = Field(default_factory=list)
    backups: list[CloudBackup] = Field(default_factory=list)
    domains: list[CloudDomain] = Field(default_factory=list)
    production_public_status: str = Field(default="unknown", min_length=1, max_length=100)
    production_auth_status: str = Field(default="unknown", min_length=1, max_length=100)
    persistent_session_status: str = Field(default="unknown", min_length=1, max_length=100)
    cost_status: str = Field(default="unknown", min_length=1, max_length=100)
    requires_manual_review: bool = True
    notes: str | None = Field(default=None, max_length=800)


class CloudProject(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    name: str = Field(min_length=1, max_length=180)
    production_url: str | None = None
    control_center_url: str | None = None
    provider: str = Field(min_length=1, max_length=120)
    status: str = Field(min_length=1, max_length=80)
    last_commit: str | None = None
    tags: list[str] = Field(default_factory=list)
    providers: list[CloudProvider] = Field(default_factory=list)
    databases: list[CloudDatabase] = Field(default_factory=list)
    variables: list[CloudVariable] = Field(default_factory=list)
    backups: list[CloudBackup] = Field(default_factory=list)
    domains: list[CloudDomain] = Field(default_factory=list)
    production_public_status: str = Field(min_length=1)
    production_auth_status: str = Field(min_length=1)
    persistent_session_status: str = Field(min_length=1)
    cost_status: str = Field(min_length=1)
    requires_manual_review: bool = True
    notes: str | None = None
    external_connection_enabled: bool = False
    deploy_automation_enabled: bool = False
    vercel_api_connected: bool = False
    local_nube_touched: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CloudDeploymentCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(default="ecosystem-foundation", min_length=1, max_length=120)
    environment: str = Field(default="production", min_length=1, max_length=80)
    url: str | None = Field(default=None, max_length=300)
    provider: str = Field(default="Vercel", min_length=1, max_length=120)
    commit: str | None = Field(default=None, max_length=80)
    status: str = Field(default="registered", min_length=1, max_length=100)
    tags: list[str] = Field(default_factory=list)
    evidence: str | None = Field(default=None, max_length=800)


class CloudDeployment(CloudDeploymentCreate):
    id: str = Field(min_length=1)
    external_connection_enabled: bool = False
    deploy_executed_by_nube: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CloudHealthCheckCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(default="ecosystem-foundation", min_length=1, max_length=120)
    url: str = Field(min_length=1, max_length=300)
    status: str = Field(default="unknown", min_length=1, max_length=100)
    status_code: int | None = Field(default=None, ge=100, le=599)
    source: str = Field(default="manual_record", min_length=1, max_length=160)
    evidence: str | None = Field(default=None, max_length=800)


class CloudHealthCheck(CloudHealthCheckCreate):
    id: str = Field(min_length=1)
    external_monitor_connected: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CloudRiskCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(default="ecosystem-foundation", min_length=1, max_length=120)
    title: str = Field(min_length=1, max_length=220)
    severity: str = Field(default="medium", min_length=1, max_length=80)
    status: str = Field(default="open", min_length=1, max_length=100)
    description: str = Field(min_length=1, max_length=1000)
    requires_manual_review: bool = True


class CloudRisk(CloudRiskCreate):
    id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class CloudCostRecordCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    project_id: str = Field(default="ecosystem-foundation", min_length=1, max_length=120)
    provider: str = Field(default="Vercel", min_length=1, max_length=120)
    cost_status: str = Field(default="unknown", min_length=1, max_length=100)
    estimated_monthly: float | None = Field(default=None, ge=0)
    currency: str = Field(default="USD", min_length=3, max_length=8)
    requires_manual_review: bool = True
    notes: str | None = Field(default=None, max_length=800)


class CloudCostRecord(CloudCostRecordCreate):
    id: str = Field(min_length=1)
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class NubeStatus(BaseModel):
    status: str = Field(min_length=1)
    role: str = Field(min_length=1)
    project_id: str = Field(min_length=1)
    production_url: str | None = None
    control_center_url: str | None = None
    provider: str = Field(min_length=1)
    database: str = Field(min_length=1)
    persistent: bool
    temporal: bool
    last_commit: str | None = None
    tags: list[str] = Field(default_factory=list)
    backups: int
    variables: list[CloudVariable] = Field(default_factory=list)
    risks: int
    cost_status: str = Field(min_length=1)
    projects: int
    deployments: int
    health_checks: int
    production_public_status: str = Field(min_length=1)
    production_auth_status: str = Field(min_length=1)
    persistent_session_status: str = Field(min_length=1)
    requires_manual_review: bool
    external_connection_enabled: bool = False
    deploy_automation_enabled: bool = False
    vercel_api_connected: bool = False
    local_nube_touched: bool = False
    local_nube_path: str = "not_touched"
    generated_at: str = Field(min_length=1)


class NubeEvidence(BaseModel):
    requested_by: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    status: NubeStatus
    latest_deployments: list[CloudDeployment] = Field(default_factory=list)
    latest_health_checks: list[CloudHealthCheck] = Field(default_factory=list)
    risks: list[CloudRisk] = Field(default_factory=list)
    costs: list[CloudCostRecord] = Field(default_factory=list)
    variables_masked: bool = True
    secrets_exposed: bool = False
    external_connection_enabled: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
