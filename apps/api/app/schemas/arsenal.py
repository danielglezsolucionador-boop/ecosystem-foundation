from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ArsenalCatalogItemStatus(StrEnum):
    prepared = "prepared"
    evaluated = "evaluated"
    needs_audit = "needs_audit"
    needs_ceo_approval = "needs_ceo_approval"
    blocked = "blocked"


class ArsenalAuditStatus(StrEnum):
    pending = "pending"
    not_required = "not_required"
    requires_auditoria = "requires_auditoria"
    in_review = "in_review"
    approved = "approved"
    blocked = "blocked"


class ArsenalCatalogItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=180)
    item_type: str = Field(min_length=1, max_length=80)
    category: str = Field(min_length=1, max_length=120)
    internal_use: str = Field(min_length=1, max_length=1000)
    sellable_use: str | None = Field(default=None, max_length=1000)
    is_sellable: bool = False
    cost_usd: float = Field(default=0, ge=0)
    requires_secret: bool = False
    requires_external_api: bool = False
    status: ArsenalCatalogItemStatus | None = None
    risk: str = Field(default="controlled", min_length=1, max_length=120)
    monetization: str = Field(default="not_estimated", min_length=1, max_length=800)
    owner: str = Field(default="CEREBRO", min_length=1, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArsenalCatalogItemEvaluateRequest(BaseModel):
    risk: str | None = Field(default=None, max_length=120)
    monetization: str | None = Field(default=None, max_length=800)
    audit_status: ArsenalAuditStatus | None = None
    technical_status: str | None = Field(default=None, max_length=120)
    expected_revenue_usd: float | None = Field(default=None, ge=0)
    probability_percent: float | None = Field(default=None, ge=0, le=100)
    evaluate_revenue_os: bool = False
    send_to_forja: bool = False


class ArsenalCatalogItem(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    item_type: str = Field(min_length=1)
    category: str = Field(min_length=1)
    internal_use: str = Field(min_length=1)
    sellable_use: str | None = None
    is_sellable: bool = False
    cost_usd: float = Field(default=0, ge=0)
    requires_secret: bool = False
    requires_external_api: bool = False
    requires_ceo_approval: bool = False
    requires_auditoria: bool = False
    status: ArsenalCatalogItemStatus
    risk: str = Field(min_length=1)
    monetization: str = Field(min_length=1)
    owner: str = Field(min_length=1)
    audit_status: ArsenalAuditStatus
    technical_status: str = Field(default="blueprint_prepared", min_length=1)
    revenue_opportunity_id: str | None = None
    forja_task_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    secrets_stored: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class ArsenalCategory(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    status: str = Field(default="empty/prepared", min_length=1)
    items: int = Field(default=0, ge=0)
    sellable_items: int = Field(default=0, ge=0)
    external_connection_enabled: bool = False
    runtime_connected: bool = False


class ArsenalRiskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    category: str = Field(default="governance", min_length=1, max_length=120)
    severity: str = Field(default="medium", min_length=1, max_length=40)
    detail: str = Field(min_length=1, max_length=1200)
    mitigation: str = Field(min_length=1, max_length=1200)
    related_item_id: str | None = Field(default=None, max_length=180)


class ArsenalRisk(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    category: str = Field(min_length=1)
    severity: str = Field(min_length=1)
    detail: str = Field(min_length=1)
    mitigation: str = Field(min_length=1)
    related_item_id: str | None = None
    status: str = Field(default="open", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class ArsenalPermissionRule(BaseModel):
    action: str = Field(min_length=1)
    allowed_roles: list[str] = Field(default_factory=list)
    requires_ceo_approval: bool = False
    requires_auditoria: bool = False
    notes: str = Field(min_length=1)


class ArsenalReadiness(BaseModel):
    status: str = Field(min_length=1)
    score: int = Field(ge=0, le=100)
    ready_for_build: bool = False
    blockers: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    categories_total: int = Field(ge=0)
    catalog_items: int = Field(ge=0)
    sellable_items: int = Field(ge=0)
    items_requiring_ceo_approval: int = Field(ge=0)
    risks_open: int = Field(ge=0)
    external_connection_enabled: bool = False
    runtime_connected: bool = False


class ArsenalStatus(BaseModel):
    status: str = Field(min_length=1)
    mode: str = Field(min_length=1)
    purpose: str = Field(min_length=1)
    categories: int = Field(ge=0)
    catalog_items: int = Field(ge=0)
    sellable_items: int = Field(ge=0)
    items_requiring_ceo_approval: int = Field(ge=0)
    risks_open: int = Field(ge=0)
    permissions: list[ArsenalPermissionRule] = Field(default_factory=list)
    readiness: ArsenalReadiness
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    secrets_stored: bool = False
    generated_at: str = Field(min_length=1)


class ArsenalResourceType(StrEnum):
    api = "API"
    tool = "TOOL"
    skill = "SKILL"
    app = "APP"
    module = "MODULE"
    provider = "PROVIDER"
    model = "MODEL"
    integration = "INTEGRATION"


class ArsenalResourceStatus(StrEnum):
    active = "active"
    testing = "testing"
    deprecated = "deprecated"
    replaced = "replaced"
    disabled = "disabled"


class ArsenalOffice(StrEnum):
    cerebro = "CEREBRO"
    sombra = "SOMBRA"
    centinela = "CENTINELA"
    forja = "FORJA"
    pluma = "PLUMA"
    marca_personal = "MARCA_PERSONAL"
    auditoria = "AUDITORIA"
    nube = "NUBE"
    ceo = "CEO"


class ArsenalResourceCreate(BaseModel):
    id: str | None = Field(default=None, min_length=1, max_length=180)
    name: str = Field(min_length=1, max_length=180)
    type: ArsenalResourceType
    category: str = Field(min_length=1, max_length=120)
    version: str = Field(min_length=1, max_length=80)
    status: ArsenalResourceStatus = ArsenalResourceStatus.testing
    owner_office: ArsenalOffice
    allowed_offices: list[ArsenalOffice] = Field(default_factory=list)
    location: str = Field(min_length=1, max_length=300)
    runtime: str = Field(default="metadata_only", min_length=1, max_length=180)
    description: str = Field(min_length=1, max_length=1200)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    replaces: str | None = Field(default=None, max_length=180)
    notes: str = Field(default="", max_length=1200)
    available_for_sombra: bool = False
    readiness: str = Field(default="planned", min_length=1, max_length=120)


class ArsenalResourceDisableRequest(BaseModel):
    reason: str = Field(default="disabled_by_governance", min_length=1, max_length=400)


class ArsenalResource(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    type: ArsenalResourceType
    category: str = Field(min_length=1)
    version: str = Field(min_length=1)
    status: ArsenalResourceStatus
    owner_office: ArsenalOffice
    allowed_offices: list[ArsenalOffice] = Field(default_factory=list)
    location: str = Field(min_length=1)
    runtime: str = Field(min_length=1)
    description: str = Field(min_length=1)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    replaces: str | None = None
    replaced_by: str | None = None
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    notes: str = ""
    available_for_sombra: bool = False
    readiness: str = Field(default="planned", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    secrets_stored: bool = False
    audit_event_ids: list[str] = Field(default_factory=list)


class ArsenalBrokerOffice(StrEnum):
    cerebro = "CEREBRO"
    pluma = "PLUMA"
    marca_personal = "MARCA_PERSONAL"
    centinela = "CENTINELA"
    auditoria = "AUDITORIA"


class ArsenalBrokerCapability(StrEnum):
    redaccion = "redaccion"
    narrativa = "narrativa"
    posts = "posts"
    articulos = "articulos"
    calendario = "calendario"
    adaptacion_posts = "adaptacion_posts"
    linkedin_publicacion = "linkedin_publicacion"
    riesgo = "riesgo"
    alerta = "alerta"
    defensa = "defensa"
    resumen = "resumen"
    evidencias = "evidencias"
    trazabilidad = "trazabilidad"
    registro = "registro"
    orquestacion = "orquestacion"


class ArsenalBrokerRequest(BaseModel):
    office: ArsenalBrokerOffice
    capability: ArsenalBrokerCapability
    prompt: str = Field(min_length=1, max_length=4000)
    provider: str | None = Field(default=None, max_length=80)
    model: str | None = Field(default=None, max_length=120)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArsenalBrokerResponse(BaseModel):
    ok: bool
    status: str = Field(min_length=1)
    office: ArsenalBrokerOffice
    capability: ArsenalBrokerCapability
    provider: str = Field(min_length=1)
    model: str = Field(min_length=1)
    result: str = Field(min_length=1)
    cost_usd: float = Field(default=0, ge=0)
    audit_event_id: str | None = None
    external_call_executed: bool = False
    runtime_connected: bool = False
    secrets_stored: bool = False
    generated_at: str = Field(min_length=1)


class ArsenalBrokerStatus(BaseModel):
    status: str = Field(min_length=1)
    mode: str = Field(min_length=1)
    default_provider: str = Field(min_length=1)
    default_model: str = Field(min_length=1)
    execution_enabled: bool = False
    providers_configured: dict[str, bool] = Field(default_factory=dict)
    permissions: dict[str, list[str]] = Field(default_factory=dict)
    offices: list[str] = Field(default_factory=list)
    external_call_executed: bool = False
    runtime_connected: bool = False
    secrets_stored: bool = False
    generated_at: str = Field(min_length=1)


class ArsenalLinkedInStatus(BaseModel):
    status: str = Field(min_length=1)
    oauth_prepared: bool = True
    client_configured: bool = False
    redirect_configured: bool = False
    access_token_configured: bool = False
    person_urn_configured: bool = False
    posting_requested: bool = False
    posting_enabled: bool = False
    publication_allowed: bool = False
    pending_credentials: list[str] = Field(default_factory=list)
    external_call_executed: bool = False
    runtime_connected: bool = False
    secrets_stored: bool = False
    generated_at: str = Field(min_length=1)


class ArsenalLinkedInOAuthStartResponse(BaseModel):
    status: str = Field(min_length=1)
    authorization_url: str | None = None
    pending_credentials: list[str] = Field(default_factory=list)
    activation_required: bool = True
    external_call_executed: bool = False
    secrets_stored: bool = False


class ArsenalLinkedInPostRequest(BaseModel):
    content: str = Field(min_length=1, max_length=3000)
    publish_now: bool = False
    scheduled_for: str | None = Field(default=None, max_length=80)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ArsenalLinkedInPostResponse(BaseModel):
    ok: bool
    status: str = Field(min_length=1)
    publication_allowed: bool = False
    publish_now_requested: bool = False
    scheduled_for: str | None = None
    audit_event_id: str | None = None
    external_call_executed: bool = False
    runtime_connected: bool = False
    secrets_stored: bool = False
    generated_at: str = Field(min_length=1)
