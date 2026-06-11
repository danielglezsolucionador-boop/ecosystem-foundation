from enum import StrEnum

from pydantic import BaseModel, Field


class RealWorldConnectionType(StrEnum):
    social_account = "social_account"
    publishing_account = "publishing_account"
    analytics_account = "analytics_account"
    payment_provider = "payment_provider"
    marketplace = "marketplace"
    app_store = "app_store"
    cloud_provider = "cloud_provider"
    external_api = "external_api"
    marketing_platform = "marketing_platform"
    ecommerce_platform = "ecommerce_platform"
    security_feed = "security_feed"
    tax_regulatory_source = "tax/regulatory_source"
    content_tool = "content_tool"
    ai_tool = "ai_tool"
    email_tool = "email_tool"
    crm_tool = "crm_tool"


class RealWorldConnectionState(StrEnum):
    unknown = "unknown"
    not_connected = "not_connected"
    prepared = "prepared"
    needs_ceo_definition = "needs_ceo_definition"
    needs_credentials = "needs_credentials"
    needs_paid_approval = "needs_paid_approval"
    needs_account_creation = "needs_account_creation"
    needs_legal_review = "needs_legal_review"
    connected_manual = "connected_manual"
    connected_api = "connected_api"
    blocked = "blocked"
    deprecated = "deprecated"


class RealWorldRiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    sensitive = "sensitive"


class RealWorldActionRequest(BaseModel):
    note: str | None = Field(default=None, max_length=1200)
    evidence: str | None = Field(default=None, max_length=1200)
    reason: str | None = Field(default=None, max_length=1200)


class RealWorldConnection(BaseModel):
    id: str = Field(min_length=1)
    area: str = Field(min_length=1)
    connection: str = Field(min_length=1)
    connection_type: RealWorldConnectionType
    state: RealWorldConnectionState = RealWorldConnectionState.unknown
    evidence: str = Field(default="missing", min_length=1)
    requires_ceo: bool = False
    requires_credentials: bool = False
    requires_money: bool = False
    risk: RealWorldRiskLevel = RealWorldRiskLevel.medium
    recommended_action: str = Field(min_length=1)
    related_block: str = Field(default="S.1", min_length=1)
    owner_internal: str = Field(min_length=1)
    can_continue_prepared: bool = True
    notes: str = Field(default="", max_length=1200)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    real_publication_enabled: bool = False
    paid_campaign_launched: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False
    secrets_stored: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class RealWorldStatus(BaseModel):
    status: str = Field(default="real_world_connection_readiness_prepared", min_length=1)
    mode: str = Field(default="prepared_local", min_length=1)
    total_connections: int = Field(default=0, ge=0)
    connected: int = Field(default=0, ge=0)
    prepared: int = Field(default=0, ge=0)
    unknown: int = Field(default=0, ge=0)
    needs_ceo: int = Field(default=0, ge=0)
    needs_credentials: int = Field(default=0, ge=0)
    needs_paid_approval: int = Field(default=0, ge=0)
    high_risk: int = Field(default=0, ge=0)
    sensitive: int = Field(default=0, ge=0)
    can_continue_prepared: int = Field(default=0, ge=0)
    approval_needed_count: int = Field(default=0, ge=0)
    next_steps: list[str] = Field(default_factory=list)
    connections_snapshot: list[RealWorldConnection] = Field(default_factory=list)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    real_publication_enabled: bool = False
    paid_campaign_launched: bool = False
    payment_connected: bool = False
    sunat_enabled: bool = False
    secrets_stored: bool = False
    generated_at: str = Field(min_length=1)
