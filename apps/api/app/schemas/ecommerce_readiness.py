from enum import StrEnum

from pydantic import BaseModel, Field


class CommerceReadinessState(StrEnum):
    unknown = "unknown"
    idea = "idea"
    prepared = "prepared"
    needs_market_research = "needs_market_research"
    needs_supplier = "needs_supplier"
    needs_payment_provider = "needs_payment_provider"
    needs_account_creation = "needs_account_creation"
    needs_paid_tool = "needs_paid_tool"
    blocked = "blocked"


class CommerceRiskLevel(StrEnum):
    low = "low"
    medium = "medium"
    high = "high"
    sensitive = "sensitive"


class CommerceOpportunity(BaseModel):
    id: str = Field(min_length=1)
    business_line: str = Field(min_length=1)
    platform: str = Field(min_length=1)
    product_category: str = Field(min_length=1)
    state: CommerceReadinessState
    evidence: str = Field(default="missing", min_length=1)
    investment_needed: str = Field(default="unknown")
    margin_estimated: str = Field(default="unknown_not_estimated")
    requires_ceo: bool = False
    requires_external_account: bool = False
    requires_credentials: bool = False
    requires_supplier: bool = False
    requires_payment_provider: bool = False
    requires_inventory: bool = False
    requires_paid_tool: bool = False
    risk: CommerceRiskLevel = CommerceRiskLevel.medium
    next_action: str = Field(min_length=1)
    can_continue_prepared: bool = True
    target_goal_usd: float = Field(default=10000, ge=0)
    separated_from_global_goal: bool = True
    real_sales_confirmed: bool = False
    real_margin_confirmed: bool = False
    payment_connected: bool = False
    amazon_seller_connected: bool = False
    store_created: bool = False
    inventory_purchased: bool = False
    prohibited_scraping_enabled: bool = False
    external_connection_enabled: bool = False
    credentials_stored: bool = False
    created_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)


class EcommerceReadinessStatus(BaseModel):
    status: str = Field(default="ecommerce_readiness_prepared", min_length=1)
    mode: str = Field(default="prepared_local", min_length=1)
    monthly_goal_usd: float = Field(default=10000, gt=0)
    global_goal_usd: float = Field(default=6000, gt=0)
    separated_from_global_goal: bool = True
    opportunities: int = Field(default=0, ge=0)
    prepared: int = Field(default=0, ge=0)
    unknown: int = Field(default=0, ge=0)
    needs_market_research: int = Field(default=0, ge=0)
    needs_supplier: int = Field(default=0, ge=0)
    needs_payment_provider: int = Field(default=0, ge=0)
    needs_account_creation: int = Field(default=0, ge=0)
    approval_needed: int = Field(default=0, ge=0)
    investment_required: int = Field(default=0, ge=0)
    high_risk: int = Field(default=0, ge=0)
    actual_revenue_usd: float = Field(default=0, ge=0)
    actual_sales_confirmed: bool = False
    margin_invented: bool = False
    payment_connected: bool = False
    store_created: bool = False
    inventory_purchased: bool = False
    external_connection_enabled: bool = False
    credentials_stored: bool = False
    next_steps: list[str] = Field(default_factory=list)
    opportunities_snapshot: list[CommerceOpportunity] = Field(default_factory=list)
    generated_at: str = Field(min_length=1)


class AmazonReadinessStatus(BaseModel):
    status: str = Field(default="amazon_readiness_prepared", min_length=1)
    mode: str = Field(default="radar_prepared_local", min_length=1)
    monthly_goal_usd: float = Field(default=10000, gt=0)
    separated_from_global_goal: bool = True
    opportunities: int = Field(default=0, ge=0)
    prepared: int = Field(default=0, ge=0)
    unknown: int = Field(default=0, ge=0)
    needs_market_research: int = Field(default=0, ge=0)
    needs_paid_tool: int = Field(default=0, ge=0)
    needs_account_creation: int = Field(default=0, ge=0)
    risks: int = Field(default=0, ge=0)
    approval_needed: int = Field(default=0, ge=0)
    amazon_seller_connected: bool = False
    paid_tool_connected: bool = False
    prohibited_scraping_enabled: bool = False
    real_products_declared_winners: bool = False
    real_sales_confirmed: bool = False
    real_margin_confirmed: bool = False
    external_connection_enabled: bool = False
    credentials_stored: bool = False
    next_steps: list[str] = Field(default_factory=list)
    opportunities_snapshot: list[CommerceOpportunity] = Field(default_factory=list)
    generated_at: str = Field(min_length=1)
