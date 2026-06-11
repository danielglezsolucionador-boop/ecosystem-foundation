from pathlib import Path

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)


PHASE_S_ENDPOINTS = [
    "/api/v1/publishing-prepared/status",
    "/api/v1/publishing-prepared/calendar",
    "/api/v1/publishing-prepared/content",
    "/api/v1/publishing-prepared/blocked",
    "/api/v1/marketing-approval/status",
    "/api/v1/marketing-approval/campaigns",
    "/api/v1/marketing-approval/approval-needed",
    "/api/v1/marketing-approval/risks",
    "/api/v1/commercial-readiness/status",
    "/api/v1/commercial-readiness/dcft",
    "/api/v1/commercial-readiness/sentinela",
    "/api/v1/commercial-readiness/marketing-package",
    "/api/v1/commercial-readiness/approval-needed",
    "/api/v1/analytics-readiness/status",
    "/api/v1/analytics-readiness/metrics",
    "/api/v1/analytics-readiness/sources",
    "/api/v1/analytics-readiness/approval-needed",
    "/api/v1/analytics-readiness/risks",
]


def test_phase_s_partial_endpoints_require_auth() -> None:
    for path in PHASE_S_ENDPOINTS:
        response = client.get(path)
        assert response.status_code == 401, path


def test_publishing_prepared_is_safe_and_not_published() -> None:
    headers = auth_headers(client, ControlCenterRole.ceo)

    status_response = client.get("/api/v1/publishing-prepared/status", headers=headers)
    assert status_response.status_code == 200
    status = status_response.json()
    assert status["block"] == "S3"
    assert status["status"] == "prepared_local"
    assert status["published_items"] == 0
    assert status["real_publication_enabled"] is False
    assert status["paid_campaign_launched"] is False
    assert status["external_connection_enabled"] is False
    assert status["metrics_invented"] is False

    content = client.get("/api/v1/publishing-prepared/content", headers=headers).json()
    assert content
    assert all(item["publication_status"] == "prepared" for item in content)
    assert all(item["published"] is False for item in content)
    assert any(item["account_status"] in {"unknown", "not_connected"} for item in content)

    blocked = client.get("/api/v1/publishing-prepared/blocked", headers=headers).json()
    assert any(item["blocked_action"] == "real_publication" for item in blocked)


def test_marketing_paid_gate_requires_ceo_and_roi() -> None:
    headers = auth_headers(client, ControlCenterRole.admin)

    status = client.get("/api/v1/marketing-approval/status", headers=headers).json()
    assert status["block"] == "S4"
    assert status["paid_campaigns_launched"] == 0
    assert status["paid_campaign_launched"] is False
    assert status["budget_spent"] == 0
    assert status["roi_confirmed"] is False

    campaigns = client.get("/api/v1/marketing-approval/campaigns", headers=headers).json()
    paid_campaigns = [campaign for campaign in campaigns if campaign["campaign_type"] == "paid"]
    assert paid_campaigns
    assert all(campaign["requires_ceo_approval"] is True for campaign in paid_campaigns)
    assert all(campaign["roi_status"] == "missing" for campaign in paid_campaigns)
    assert all(campaign["paid_campaign_launched"] is False for campaign in paid_campaigns)


def test_commercial_readiness_keeps_dcft_sentinela_marketing_owned() -> None:
    headers = auth_headers(client, ControlCenterRole.auditor)

    status = client.get("/api/v1/commercial-readiness/status", headers=headers).json()
    assert status["block"] == "S6"
    assert status["marketing_owner"] == "MARKETING"
    assert status["products_with_own_sales_goal"] == 0
    assert status["runtime_connected"] is False
    assert status["external_connection_enabled"] is False
    assert status["claims_invented"] is False

    dcft = client.get("/api/v1/commercial-readiness/dcft", headers=headers).json()
    sentinela = client.get("/api/v1/commercial-readiness/sentinela", headers=headers).json()
    assert dcft["has_own_sales_goal"] is False
    assert sentinela["has_own_sales_goal"] is False
    assert dcft["marketing_owner"] == "MARKETING"
    assert sentinela["marketing_owner"] == "MARKETING"
    assert dcft["sunat_enabled"] is False
    assert dcft["technical_status"] == "protected_no_touch"

    package = client.get("/api/v1/commercial-readiness/marketing-package", headers=headers).json()
    assert package["claims_invented"] is False
    assert package["requires_validation"] is True


def test_analytics_readiness_does_not_invent_metrics() -> None:
    headers = auth_headers(client, ControlCenterRole.operator)

    status = client.get("/api/v1/analytics-readiness/status", headers=headers).json()
    assert status["block"] == "S7"
    assert status["real_metrics_confirmed"] == 0
    assert status["metrics_invented"] is False
    assert status["external_connection_enabled"] is False
    assert status["api_connected_sources"] == 0

    metrics = client.get("/api/v1/analytics-readiness/metrics", headers=headers).json()
    assert metrics
    assert all(metric["value"] == 0 for metric in metrics)
    assert all(metric["evidence_status"] == "missing" for metric in metrics)
    assert all(metric["invented"] is False for metric in metrics)

    sources = client.get("/api/v1/analytics-readiness/sources", headers=headers).json()
    assert any(source["status"] == "manual_ready" for source in sources)
    assert any(source["status"] == "api_not_connected" for source in sources)
    assert all(source["api_connected"] is False for source in sources)


def test_control_center_contains_phase_s_partial_panels_and_endpoints() -> None:
    root = Path(__file__).resolve().parents[3]
    app_js = (root / "apps" / "web" / "control-center" / "assets" / "app.js").read_text(encoding="utf-8")
    index_html = (root / "apps" / "web" / "control-center" / "index.html").read_text(encoding="utf-8")

    for endpoint in PHASE_S_ENDPOINTS:
        assert endpoint in app_js

    for panel_id in [
        "publishing-prepared",
        "marketing-approval-gate",
        "commercial-readiness",
        "analytics-readiness",
    ]:
        assert panel_id in index_html

    forbidden_claims = ["paid_campaign_launched=true", "published_items=1", "metrics_invented=true"]
    for claim in forbidden_claims:
        assert claim not in app_js
        assert claim not in index_html
