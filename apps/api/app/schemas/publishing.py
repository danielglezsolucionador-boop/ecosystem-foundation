from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field


class PublishingAccountStatus(StrEnum):
    connected = "connected"
    not_connected = "not_connected"
    unknown = "unknown"


class PublishingMode(StrEnum):
    prepared = "prepared"
    organic = "organic"
    paid = "paid"


class PublishingContentStatus(StrEnum):
    draft = "draft"
    prepared = "prepared"
    scheduled = "scheduled"
    published = "published"
    waiting_ceo_approval = "waiting_ceo_approval"
    blocked = "blocked"


class PublishingEvidenceStatus(StrEnum):
    missing = "missing"
    partial = "partial"
    available = "available"


class PublishingChannelCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    platform: str | None = Field(default=None, max_length=120)
    account_name: str | None = Field(default=None, max_length=160)
    account_status: PublishingAccountStatus = PublishingAccountStatus.not_connected
    official_account: bool = False
    api_connected: bool = False
    organic_enabled: bool = False
    new_external_account_requested: bool = False


class PublishingChannel(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    account_name: str | None = None
    account_status: PublishingAccountStatus
    publication_mode: PublishingMode
    official_account: bool = False
    api_connected: bool = False
    organic_enabled: bool = False
    requires_approval: bool = False
    approval_reason: str = Field(default="none", min_length=1)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class PublishingContentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    format: str = Field(default="post", min_length=1, max_length=120)
    department_owner: str = Field(default="PLUMA", min_length=1, max_length=120)
    channel: str = Field(default="Blog/Web", min_length=1, max_length=120)
    account_status: PublishingAccountStatus | None = None
    language: str = Field(default="es", min_length=1, max_length=16)
    niche: str | None = Field(default=None, max_length=160)
    niche_status: str | None = Field(default=None, max_length=120)
    status: PublishingContentStatus | None = None
    scheduled_at: str | None = Field(default=None, max_length=80)
    publication_mode: PublishingMode = PublishingMode.prepared
    requires_approval: bool | None = None
    revenue_link: str | None = Field(default=None, max_length=160)
    metrics: dict[str, Any] = Field(default_factory=dict)
    campaign_id: str | None = Field(default=None, max_length=160)
    content_brief: str = Field(default="Preparar pieza organica sin publicacion real.", max_length=1000)


class PublishingScheduleRequest(BaseModel):
    scheduled_at: str = Field(min_length=1, max_length=80)
    channel: str | None = Field(default=None, max_length=120)
    publication_mode: PublishingMode | None = None


class PublishingMarkPublishedRequest(BaseModel):
    evidence: str | None = Field(default=None, max_length=800)
    metrics: dict[str, Any] = Field(default_factory=dict)


class PublishingGrowthMetricCreate(BaseModel):
    content_id: str | None = Field(default=None, max_length=160)
    channel: str = Field(default="Blog/Web", min_length=1, max_length=120)
    metric_name: str = Field(default="views", min_length=1, max_length=120)
    value: float = Field(default=0, ge=0)
    evidence: str | None = Field(default=None, max_length=800)
    evidence_status: PublishingEvidenceStatus | None = None


class PublishingContentItem(BaseModel):
    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    format: str = Field(min_length=1)
    department_owner: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    account_status: PublishingAccountStatus
    language: str = Field(min_length=1)
    niche: str | None = None
    niche_status: str = Field(default="defined", min_length=1)
    status: PublishingContentStatus
    scheduled_at: str | None = None
    publication_mode: PublishingMode
    publication_status: str = Field(default="prepared", min_length=1)
    requires_approval: bool = False
    approval_reason: str = Field(default="none", min_length=1)
    revenue_link: str | None = None
    metrics: dict[str, Any] = Field(default_factory=dict)
    metrics_status: PublishingEvidenceStatus = PublishingEvidenceStatus.missing
    campaign_id: str | None = None
    content_brief: str = Field(min_length=1)
    actual_publication_confirmed: bool = False
    paid_campaign_launched: bool = False
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class PublishingCalendarEntry(BaseModel):
    id: str = Field(min_length=1)
    content_id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    channel: str = Field(min_length=1)
    scheduled_at: str | None = None
    publication_mode: PublishingMode
    publication_status: str = Field(min_length=1)
    requires_approval: bool = False
    created_at: str = Field(min_length=1)


class PublishingGrowthMetric(BaseModel):
    id: str = Field(min_length=1)
    content_id: str | None = None
    channel: str = Field(min_length=1)
    metric_name: str = Field(min_length=1)
    value: float = Field(ge=0)
    evidence: str | None = None
    evidence_status: PublishingEvidenceStatus
    real_metric_confirmed: bool = False
    created_at: str = Field(min_length=1)


class PublishingStatus(BaseModel):
    status: str = Field(min_length=1)
    mode: str = Field(default="prepared_local", min_length=1)
    channels: int = Field(default=0, ge=0)
    connected_accounts: int = Field(default=0, ge=0)
    not_connected_accounts: int = Field(default=0, ge=0)
    content_items: int = Field(default=0, ge=0)
    prepared_items: int = Field(default=0, ge=0)
    scheduled_items: int = Field(default=0, ge=0)
    published_records: int = Field(default=0, ge=0)
    approvals_needed: int = Field(default=0, ge=0)
    paid_campaigns_launched: int = Field(default=0, ge=0)
    real_metrics_confirmed: int = Field(default=0, ge=0)
    next_content: list[PublishingContentItem] = Field(default_factory=list)
    channels_snapshot: list[PublishingChannel] = Field(default_factory=list)
    cerebro_coordination: dict[str, Any] = Field(default_factory=dict)
    external_connection_enabled: bool = False
    runtime_connected: bool = False
    payment_connected: bool = False
    generated_at: str = Field(min_length=1)
