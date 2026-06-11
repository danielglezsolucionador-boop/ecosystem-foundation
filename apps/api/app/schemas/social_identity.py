from enum import StrEnum

from pydantic import BaseModel, Field


class SocialIdentityState(StrEnum):
    unknown = "unknown"
    existing_unconfirmed = "existing_unconfirmed"
    confirmed_existing = "confirmed_existing"
    proposed_new = "proposed_new"
    prepared = "prepared"
    needs_ceo_definition = "needs_ceo_definition"
    needs_credentials = "needs_credentials"
    needs_account_creation = "needs_account_creation"
    blocked = "blocked"


class SocialIdentityRisk(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    sensitive = "sensitive"


class SocialIdentityAccount(BaseModel):
    id: str = Field(min_length=1)
    area: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    current_account: str = Field(default="unknown")
    proposed_account: str = Field(default="pending_ceo")
    state: SocialIdentityState = SocialIdentityState.unknown
    evidence: str = Field(default="missing", min_length=1)
    owner_internal: str = Field(min_length=1)
    requires_ceo: bool = False
    requires_credentials: bool = False
    requires_account_creation: bool = False
    risk: SocialIdentityRisk = SocialIdentityRisk.medium
    recommended_action: str = Field(min_length=1)
    can_continue_prepared: bool = True
    notes: str = Field(default="", max_length=1200)
    account_connected: bool = False
    real_publication_enabled: bool = False
    external_connection_enabled: bool = False
    credentials_stored: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class SocialIdentityStatus(BaseModel):
    status: str = Field(default="social_identity_map_prepared", min_length=1)
    mode: str = Field(default="prepared_local", min_length=1)
    total_accounts: int = Field(default=0, ge=0)
    unknown: int = Field(default=0, ge=0)
    existing_unconfirmed: int = Field(default=0, ge=0)
    confirmed_existing: int = Field(default=0, ge=0)
    proposed_new: int = Field(default=0, ge=0)
    prepared: int = Field(default=0, ge=0)
    needs_ceo: int = Field(default=0, ge=0)
    needs_credentials: int = Field(default=0, ge=0)
    needs_account_creation: int = Field(default=0, ge=0)
    high_risk: int = Field(default=0, ge=0)
    sensitive: int = Field(default=0, ge=0)
    approval_needed_count: int = Field(default=0, ge=0)
    platforms: list[str] = Field(default_factory=list)
    areas: list[str] = Field(default_factory=list)
    next_steps: list[str] = Field(default_factory=list)
    accounts_snapshot: list[SocialIdentityAccount] = Field(default_factory=list)
    account_connected: bool = False
    real_publication_enabled: bool = False
    external_connection_enabled: bool = False
    credentials_stored: bool = False
    generated_at: str = Field(min_length=1)
