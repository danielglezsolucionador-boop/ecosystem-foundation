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
