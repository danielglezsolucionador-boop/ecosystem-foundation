from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.services.auth import get_current_user, require_control_center_user


READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}


def require_read(user: AuthenticatedUser, scope: str) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": f"{scope}_role_not_authorized", "role": user.role.value},
        )


def timestamp() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


publishing_prepared_router = APIRouter(
    prefix="/api/v1/publishing-prepared",
    tags=["publishing-prepared"],
    dependencies=[Depends(require_control_center_user)],
)
marketing_approval_router = APIRouter(
    prefix="/api/v1/marketing-approval",
    tags=["marketing-approval"],
    dependencies=[Depends(require_control_center_user)],
)
commercial_readiness_router = APIRouter(
    prefix="/api/v1/commercial-readiness",
    tags=["commercial-readiness"],
    dependencies=[Depends(require_control_center_user)],
)
analytics_readiness_router = APIRouter(
    prefix="/api/v1/analytics-readiness",
    tags=["analytics-readiness"],
    dependencies=[Depends(require_control_center_user)],
)


def publishing_content() -> list[dict[str, object]]:
    return [
        {
            "id": "s3_pluma_authority_batch",
            "title": "PLUMA authority post batch",
            "format": "posts",
            "department_owner": "PLUMA",
            "channel": "LinkedIn",
            "account_status": "unknown",
            "publication_status": "prepared",
            "publication_mode": "organic_prepared",
            "requires_approval": False,
            "real_publication_enabled": False,
            "published": False,
            "metrics_status": "missing",
            "evidence_status": "missing",
            "next_action": "Confirm official account before any real publication.",
        },
        {
            "id": "s3_lente_short_video_batch",
            "title": "LENTE short video concepts",
            "format": "shorts",
            "department_owner": "LENTE",
            "channel": "YouTube Shorts",
            "account_status": "unknown",
            "publication_status": "prepared",
            "publication_mode": "organic_prepared",
            "requires_approval": False,
            "real_publication_enabled": False,
            "published": False,
            "metrics_status": "missing",
            "evidence_status": "missing",
            "niche_status": "needs_ceo_definition",
            "next_action": "Keep visuals prepared until official channel is confirmed.",
        },
        {
            "id": "s3_marketing_organic_validation",
            "title": "MARKETING organic demand validation",
            "format": "campaign brief",
            "department_owner": "MARKETING",
            "channel": "Blog/Web",
            "account_status": "not_connected",
            "publication_status": "prepared",
            "publication_mode": "organic_prepared",
            "requires_approval": False,
            "real_publication_enabled": False,
            "published": False,
            "metrics_status": "missing",
            "evidence_status": "missing",
            "next_action": "Prepare demand validation copy without launching paid traffic.",
        },
        {
            "id": "s3_marca_personal_ceo_authority",
            "title": "MARCA PERSONAL CEO authority sequence",
            "format": "script sequence",
            "department_owner": "MARCA PERSONAL",
            "channel": "TikTok / Instagram / LinkedIn / X",
            "account_status": "unknown",
            "publication_status": "prepared",
            "publication_mode": "organic_prepared",
            "requires_approval": False,
            "real_publication_enabled": False,
            "published": False,
            "metrics_status": "missing",
            "evidence_status": "missing",
            "next_action": "CEO must confirm official accounts before external publication.",
        },
    ]


def publishing_calendar() -> list[dict[str, object]]:
    return [
        {
            "id": "s3_week_1_organic_preparation",
            "period": "week_1",
            "status": "prepared",
            "publication_status": "not_published",
            "summary": "Prepare organic content inventory and account checklist.",
            "requires_ceo_approval": False,
            "external_connection_enabled": False,
        },
        {
            "id": "s3_week_2_organic_validation",
            "period": "week_2",
            "status": "prepared",
            "publication_status": "not_published",
            "summary": "Validate messages only after official accounts are confirmed.",
            "requires_ceo_approval": False,
            "external_connection_enabled": False,
        },
    ]


def publishing_blocked() -> list[dict[str, object]]:
    return [
        {
            "id": "s3_unknown_accounts_block_real_publish",
            "reason": "official_accounts_unknown",
            "status": "blocked",
            "blocked_action": "real_publication",
            "safe_fallback": "publication_status=prepared",
            "requires_ceo_approval": True,
        },
        {
            "id": "s3_missing_metrics_block_claims",
            "reason": "metrics_missing",
            "status": "blocked",
            "blocked_action": "performance_claims",
            "safe_fallback": "evidence_status=missing",
            "requires_ceo_approval": False,
        },
    ]


@publishing_prepared_router.get("/status")
def read_publishing_prepared_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    require_read(current_user, "publishing_prepared")
    content = publishing_content()
    blocked = publishing_blocked()
    return {
        "block": "S3",
        "status": "prepared_local",
        "mode": "organic_prepared_pipeline",
        "content_items": len(content),
        "prepared_items": len(content),
        "published_items": 0,
        "real_publication_enabled": False,
        "paid_campaign_launched": False,
        "external_accounts_connected": 0,
        "external_connection_enabled": False,
        "metrics_invented": False,
        "real_metrics_confirmed": 0,
        "blocked_items": len(blocked),
        "next_action": "CEO must confirm official accounts before real publication.",
        "updated_at": timestamp(),
        "content_snapshot": content,
        "blocked_snapshot": blocked,
    }


@publishing_prepared_router.get("/calendar")
def read_publishing_prepared_calendar(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "publishing_prepared")
    return publishing_calendar()


@publishing_prepared_router.get("/content")
def read_publishing_prepared_content(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "publishing_prepared")
    return publishing_content()


@publishing_prepared_router.get("/blocked")
def read_publishing_prepared_blocked(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "publishing_prepared")
    return publishing_blocked()


def marketing_campaigns() -> list[dict[str, object]]:
    return [
        {
            "id": "s4_dcft_paid_validation",
            "name": "DCFT paid validation proposal",
            "product": "DCFT",
            "campaign_type": "paid",
            "status": "approval_needed",
            "requires_ceo_approval": True,
            "roi_status": "missing",
            "budget_approved": False,
            "paid_campaign_launched": False,
            "external_account_connected": False,
            "next_action": "Prepare ROI estimate and wait for CEO approval.",
        },
        {
            "id": "s4_sentinela_paid_validation",
            "name": "SENTINELA paid validation proposal",
            "product": "SENTINELA",
            "campaign_type": "paid",
            "status": "approval_needed",
            "requires_ceo_approval": True,
            "roi_status": "missing",
            "budget_approved": False,
            "paid_campaign_launched": False,
            "external_account_connected": False,
            "next_action": "Do not launch without CEO approval and ROI evidence.",
        },
        {
            "id": "s4_organic_content_support",
            "name": "Organic content support",
            "product": "ecosystem",
            "campaign_type": "organic",
            "status": "prepared",
            "requires_ceo_approval": False,
            "roi_status": "not_required_for_prepared_organic",
            "budget_approved": False,
            "paid_campaign_launched": False,
            "external_account_connected": False,
            "next_action": "Keep prepared until official account connection is confirmed.",
        },
    ]


def marketing_approval_risks() -> list[dict[str, object]]:
    return [
        {
            "id": "s4_paid_without_roi",
            "risk": "paid_campaign_without_roi",
            "severity": "high",
            "status": "blocked",
            "control": "requires_ceo_approval=true",
        },
        {
            "id": "s4_external_accounts_unknown",
            "risk": "external_account_unknown",
            "severity": "medium",
            "status": "blocked",
            "control": "external_account_connected=false",
        },
    ]


@marketing_approval_router.get("/status")
def read_marketing_approval_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    require_read(current_user, "marketing_approval")
    campaigns = marketing_campaigns()
    approval_needed = [campaign for campaign in campaigns if campaign["requires_ceo_approval"]]
    return {
        "block": "S4",
        "status": "approval_gate_prepared",
        "campaigns": len(campaigns),
        "approval_needed": len(approval_needed),
        "paid_campaigns_launched": 0,
        "paid_campaign_launched": False,
        "budget_spent": 0,
        "roi_confirmed": False,
        "external_connection_enabled": False,
        "next_action": "Paid campaigns require CEO approval with ROI before launch.",
        "updated_at": timestamp(),
        "campaigns_snapshot": campaigns,
    }


@marketing_approval_router.get("/campaigns")
def read_marketing_approval_campaigns(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "marketing_approval")
    return marketing_campaigns()


@marketing_approval_router.get("/approval-needed")
def read_marketing_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "marketing_approval")
    return [campaign for campaign in marketing_campaigns() if campaign["requires_ceo_approval"]]


@marketing_approval_router.get("/risks")
def read_marketing_approval_risks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "marketing_approval")
    return marketing_approval_risks()


def commercial_products() -> dict[str, dict[str, object]]:
    return {
        "dcft": {
            "id": "dcft",
            "name": "Doctor Contable Financiero Tributario",
            "commercial_status": "prepared_requires_validation",
            "marketing_owner": "MARKETING",
            "has_own_sales_goal": False,
            "runtime_connected": False,
            "external_connection_enabled": False,
            "sunat_enabled": False,
            "claims_status": "requires_validation",
            "evidence_status": "missing",
            "technical_status": "protected_no_touch",
            "next_action": "Audit evidence, landing, pricing and legal sources before commercial push.",
        },
        "sentinela": {
            "id": "sentinela",
            "name": "SENTINELA",
            "commercial_status": "prepared_requires_validation",
            "marketing_owner": "MARKETING",
            "has_own_sales_goal": False,
            "runtime_connected": False,
            "external_connection_enabled": False,
            "claims_status": "requires_validation",
            "evidence_status": "missing",
            "technical_status": "protected_prepared",
            "next_action": "Validate security claims, proof, onboarding and support before commercial push.",
        },
    }


def commercial_marketing_package() -> dict[str, object]:
    return {
        "id": "s6_marketing_package",
        "status": "prepared_requires_validation",
        "owner": "MARKETING",
        "claims_invented": False,
        "requires_validation": True,
        "items": [
            {
                "product_id": "dcft",
                "value_proposition_status": "draft_requires_validation",
                "audience_status": "unknown",
                "pricing_status": "requires_ceo_validation",
                "landing_required": True,
                "required_pieces": ["landing copy", "FAQ", "onboarding notes", "risk disclaimer"],
            },
            {
                "product_id": "sentinela",
                "value_proposition_status": "draft_requires_validation",
                "audience_status": "unknown",
                "pricing_status": "requires_ceo_validation",
                "landing_required": True,
                "required_pieces": ["security positioning", "FAQ", "onboarding notes", "claim evidence"],
            },
        ],
    }


def commercial_approval_needed() -> list[dict[str, object]]:
    return [
        {
            "id": "s6_dcft_commercial_claims",
            "product": "DCFT",
            "decision": "Approve validated commercial claims after source review.",
            "requires_ceo_approval": True,
            "status": "pending",
        },
        {
            "id": "s6_sentinela_security_claims",
            "product": "SENTINELA",
            "decision": "Approve validated security claims after audit review.",
            "requires_ceo_approval": True,
            "status": "pending",
        },
    ]


@commercial_readiness_router.get("/status")
def read_commercial_readiness_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    require_read(current_user, "commercial_readiness")
    products = commercial_products()
    return {
        "block": "S6",
        "status": "commercial_readiness_prepared",
        "products": len(products),
        "marketing_owner": "MARKETING",
        "products_with_own_sales_goal": 0,
        "dcft_status": products["dcft"]["commercial_status"],
        "sentinela_status": products["sentinela"]["commercial_status"],
        "runtime_connected": False,
        "external_connection_enabled": False,
        "claims_invented": False,
        "requires_validation": 2,
        "unknown_items": 2,
        "updated_at": timestamp(),
        "products_snapshot": list(products.values()),
    }


@commercial_readiness_router.get("/dcft")
def read_commercial_dcft(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    require_read(current_user, "commercial_readiness")
    return commercial_products()["dcft"]


@commercial_readiness_router.get("/sentinela")
def read_commercial_sentinela(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    require_read(current_user, "commercial_readiness")
    return commercial_products()["sentinela"]


@commercial_readiness_router.get("/marketing-package")
def read_commercial_marketing_package(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    require_read(current_user, "commercial_readiness")
    return commercial_marketing_package()


@commercial_readiness_router.get("/approval-needed")
def read_commercial_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "commercial_readiness")
    return commercial_approval_needed()


def analytics_metrics() -> list[dict[str, object]]:
    return [
        {
            "id": "s7_revenue_actual_usd",
            "metric": "actual_revenue_usd",
            "value": 0,
            "status": "manual_ready",
            "evidence_status": "missing",
            "real_metric_confirmed": False,
            "invented": False,
        },
        {
            "id": "s7_conversion_rate",
            "metric": "conversion_rate",
            "value": 0,
            "status": "source_not_connected",
            "evidence_status": "missing",
            "real_metric_confirmed": False,
            "invented": False,
        },
        {
            "id": "s7_publishing_reach",
            "metric": "publishing_reach",
            "value": 0,
            "status": "source_not_connected",
            "evidence_status": "missing",
            "real_metric_confirmed": False,
            "invented": False,
        },
    ]


def analytics_sources() -> list[dict[str, object]]:
    return [
        {
            "id": "manual_revenue_register",
            "name": "Manual revenue register",
            "status": "manual_ready",
            "api_connected": False,
            "requires_credentials": False,
        },
        {
            "id": "web_analytics",
            "name": "Web analytics",
            "status": "api_not_connected",
            "api_connected": False,
            "requires_credentials": True,
        },
        {
            "id": "social_platform_metrics",
            "name": "Social platform metrics",
            "status": "api_not_connected",
            "api_connected": False,
            "requires_credentials": True,
        },
    ]


def analytics_approval_needed() -> list[dict[str, object]]:
    return [
        {
            "id": "s7_external_analytics_credentials",
            "decision": "Approve secure credential path before connecting analytics APIs.",
            "requires_ceo_approval": True,
            "status": "pending",
        }
    ]


def analytics_risks() -> list[dict[str, object]]:
    return [
        {
            "id": "s7_metric_without_source",
            "risk": "metric_without_source",
            "severity": "high",
            "status": "blocked",
            "control": "evidence_status=missing and invented=false",
        },
        {
            "id": "s7_external_credentials",
            "risk": "external_credentials_required",
            "severity": "medium",
            "status": "blocked",
            "control": "requires_ceo_approval=true",
        },
    ]


@analytics_readiness_router.get("/status")
def read_analytics_readiness_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    require_read(current_user, "analytics_readiness")
    metrics = analytics_metrics()
    sources = analytics_sources()
    return {
        "block": "S7",
        "status": "analytics_readiness_prepared",
        "metrics": len(metrics),
        "sources": len(sources),
        "real_metrics_confirmed": 0,
        "metrics_invented": False,
        "external_connection_enabled": False,
        "api_connected_sources": 0,
        "manual_ready_sources": len([source for source in sources if source["status"] == "manual_ready"]),
        "approval_needed": len(analytics_approval_needed()),
        "updated_at": timestamp(),
        "metrics_snapshot": metrics,
        "sources_snapshot": sources,
    }


@analytics_readiness_router.get("/metrics")
def read_analytics_metrics(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "analytics_readiness")
    return analytics_metrics()


@analytics_readiness_router.get("/sources")
def read_analytics_sources(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "analytics_readiness")
    return analytics_sources()


@analytics_readiness_router.get("/approval-needed")
def read_analytics_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "analytics_readiness")
    return analytics_approval_needed()


@analytics_readiness_router.get("/risks")
def read_analytics_risks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict[str, object]]:
    require_read(current_user, "analytics_readiness")
    return analytics_risks()
