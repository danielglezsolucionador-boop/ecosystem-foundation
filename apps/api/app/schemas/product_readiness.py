from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class ProductReadinessStatusValue(StrEnum):
    unknown = "unknown"
    requires_validation = "requires_validation"
    prepared = "prepared"
    not_ready = "not_ready"


class ProductReadinessEvidenceStatus(StrEnum):
    missing = "missing"
    partial = "partial"
    available = "available"


class ProductReadinessForgeStatus(StrEnum):
    not_sent = "not_sent"
    prepared = "prepared"


class ProductReadinessAuditRequest(BaseModel):
    evidence: str | None = Field(default=None, max_length=1200)
    source: str | None = Field(default=None, max_length=240)
    notes: str | None = Field(default=None, max_length=1200)


class ProductReadinessForjaRequest(BaseModel):
    instruction: str = Field(
        default="Preparar tarea tecnica sin declarar implementacion ni tocar producto real.",
        max_length=1200,
    )


class ProductReadinessGap(BaseModel):
    id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    area: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = Field(min_length=1)
    severity: str = Field(default="medium", min_length=1)
    status: str = Field(default="open", min_length=1)
    evidence_status: ProductReadinessEvidenceStatus = ProductReadinessEvidenceStatus.missing
    forge_status: ProductReadinessForgeStatus = ProductReadinessForgeStatus.not_sent
    technical_status: str = Field(default="pending_validation", min_length=1)
    requires_validation: bool = True
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class ProductReadinessProduct(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    sales_owner: str = Field(default="MARKETING", min_length=1)
    has_own_sales_goal: bool = False
    marketing_sells: bool = True
    technical_status: ProductReadinessStatusValue = ProductReadinessStatusValue.unknown
    commercial_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    legal_risk_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    app_store_status: ProductReadinessStatusValue = ProductReadinessStatusValue.unknown
    play_store_status: ProductReadinessStatusValue = ProductReadinessStatusValue.unknown
    update_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    landing_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    onboarding_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    pricing_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    support_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    security_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    audit_status: ProductReadinessStatusValue = ProductReadinessStatusValue.requires_validation
    evidence_status: ProductReadinessEvidenceStatus = ProductReadinessEvidenceStatus.missing
    value_proposition: str = Field(min_length=1)
    existing_functionality: list[str] = Field(default_factory=list)
    sources_needed: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    gaps: list[ProductReadinessGap] = Field(default_factory=list)
    marketing_package_status: str = Field(default="requires_validation", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    app_store_publication_enabled: bool = False
    play_store_publication_enabled: bool = False
    paid_campaign_enabled: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class ProductReadinessAuditRecord(BaseModel):
    id: str = Field(min_length=1)
    product_id: str = Field(min_length=1)
    evidence: str | None = None
    source: str | None = None
    notes: str | None = None
    evidence_status: ProductReadinessEvidenceStatus
    result_status: ProductReadinessStatusValue
    created_by: str = Field(min_length=1)
    created_at: str = Field(min_length=1)


class ProductReadinessMarketingItem(BaseModel):
    product_id: str = Field(min_length=1)
    product_name: str = Field(min_length=1)
    sales_owner: str = Field(default="MARKETING", min_length=1)
    has_own_sales_goal: bool = False
    value_proposition: str = Field(min_length=1)
    target_audience: list[str] = Field(default_factory=list)
    objections: list[str] = Field(default_factory=list)
    arguments: list[str] = Field(default_factory=list)
    required_pieces: list[str] = Field(default_factory=list)
    landing_required: bool = True
    pluma_content: list[str] = Field(default_factory=list)
    lente_content: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    readiness_status: str = Field(default="requires_validation", min_length=1)
    claim_status: str = Field(default="requires_validation", min_length=1)


class ProductReadinessMarketingPackage(BaseModel):
    id: str = Field(min_length=1)
    status: str = Field(default="prepared_requires_validation", min_length=1)
    owner: str = Field(default="MARKETING", min_length=1)
    items: list[ProductReadinessMarketingItem] = Field(default_factory=list)
    no_legal_claims_without_source: bool = True
    no_security_claims_without_evidence: bool = True
    paid_campaign_requires_ceo_approval: bool = True
    generated_at: str = Field(min_length=1)
    generated_by: str = Field(min_length=1)


class ProductReadinessStatus(BaseModel):
    status: str = Field(min_length=1)
    mode: str = Field(default="prepared_local", min_length=1)
    products: int = Field(default=0, ge=0)
    dcft_status: str = Field(default="unknown", min_length=1)
    sentinela_status: str = Field(default="unknown", min_length=1)
    marketing_owner: str = Field(default="MARKETING", min_length=1)
    products_with_own_sales_goal: int = Field(default=0, ge=0)
    open_gaps: int = Field(default=0, ge=0)
    gaps_sent_to_forja: int = Field(default=0, ge=0)
    requires_validation: int = Field(default=0, ge=0)
    unknown_items: int = Field(default=0, ge=0)
    marketing_package_status: str = Field(default="requires_validation", min_length=1)
    products_snapshot: list[ProductReadinessProduct] = Field(default_factory=list)
    marketing_package: dict[str, Any] = Field(default_factory=dict)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    sunat_enabled: bool = False
    app_store_publication_enabled: bool = False
    play_store_publication_enabled: bool = False
    paid_campaign_enabled: bool = False
    generated_at: str = Field(min_length=1)
