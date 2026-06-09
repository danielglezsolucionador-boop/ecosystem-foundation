from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_publishing_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/publishing/status"),
        ("GET", "/api/v1/publishing/channels"),
        ("POST", "/api/v1/publishing/channels"),
        ("GET", "/api/v1/publishing/calendar"),
        ("POST", "/api/v1/publishing/calendar"),
        ("GET", "/api/v1/publishing/content"),
        ("POST", "/api/v1/publishing/content"),
        ("GET", "/api/v1/publishing/content/not-real"),
        ("POST", "/api/v1/publishing/content/not-real/schedule"),
        ("POST", "/api/v1/publishing/content/not-real/mark-published"),
        ("GET", "/api/v1/publishing/growth"),
        ("POST", "/api/v1/publishing/growth/metrics"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_publishing_status_seeds_channels_without_real_accounts() -> None:
    response = client.get("/api/v1/publishing/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "publishing_growth_engine_prepared_internal"
    assert payload["channels"] >= 9
    assert payload["content_items"] >= 5
    assert payload["not_connected_accounts"] >= 1
    assert payload["paid_campaigns_launched"] == 0
    assert payload["payment_connected"] is False


def test_create_content_defaults_to_prepared_when_account_not_connected() -> None:
    response = client.post(
        "/api/v1/publishing/content",
        headers=CEO_HEADERS,
        json={
            "title": f"PLUMA prepared post {uuid4()}",
            "format": "post",
            "department_owner": "PLUMA",
            "channel": "TikTok",
            "language": "es",
            "content_brief": "Preparar post sin publicar real.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["account_status"] == "not_connected"
    assert payload["publication_mode"] == "prepared"
    assert payload["publication_status"] == "prepared"
    assert payload["requires_approval"] is False
    assert payload["actual_publication_confirmed"] is False


def test_schedule_not_connected_content_remains_prepared() -> None:
    item = client.post(
        "/api/v1/publishing/content",
        headers=CEO_HEADERS,
        json={
            "title": f"Newsletter prepared {uuid4()}",
            "format": "newsletter",
            "department_owner": "PLUMA",
            "channel": "Newsletter",
        },
    ).json()

    response = client.post(
        f"/api/v1/publishing/content/{item['id']}/schedule",
        headers=CEO_HEADERS,
        json={"scheduled_at": "2026-06-15T09:00:00Z", "publication_mode": "organic"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scheduled_at"] == "2026-06-15T09:00:00Z"
    assert payload["publication_status"] == "prepared"
    assert payload["status"] == "prepared"


def test_connected_organic_account_does_not_require_ceo_approval() -> None:
    channel = client.post(
        "/api/v1/publishing/channels",
        headers=CEO_HEADERS,
        json={
            "name": f"LinkedIn Oficial {uuid4()}",
            "platform": "LinkedIn",
            "account_status": "connected",
            "official_account": True,
            "organic_enabled": True,
        },
    ).json()
    response = client.post(
        "/api/v1/publishing/content",
        headers=CEO_HEADERS,
        json={
            "title": f"Marca personal organic {uuid4()}",
            "format": "post",
            "department_owner": "MARCA PERSONAL",
            "channel": channel["name"],
            "publication_mode": "organic",
            "content_brief": "Publicacion organica permitida para cuenta ya conectada.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["account_status"] == "connected"
    assert payload["publication_mode"] == "organic"
    assert payload["requires_approval"] is False
    assert payload["approval_reason"] == "organic_configured_account_no_approval"


def test_paid_campaign_requires_ceo_approval_and_does_not_launch() -> None:
    response = client.post(
        "/api/v1/publishing/content",
        headers=CEO_HEADERS,
        json={
            "title": f"Paid campaign draft {uuid4()}",
            "format": "campaign",
            "department_owner": "MARKETING",
            "channel": "Instagram",
            "publication_mode": "paid",
            "content_brief": "Paid campaign solo como propuesta con ROI.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["requires_approval"] is True
    assert payload["approval_reason"] == "paid_campaign_requires_ceo_approval"
    assert payload["paid_campaign_launched"] is False
    assert payload["status"] == "waiting_ceo_approval"


def test_new_external_account_requires_approval() -> None:
    response = client.post(
        "/api/v1/publishing/channels",
        headers=CEO_HEADERS,
        json={
            "name": f"Nueva cuenta externa {uuid4()}",
            "platform": "TikTok",
            "new_external_account_requested": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["requires_approval"] is True
    assert payload["approval_reason"] == "new_external_account_requires_ceo_approval"
    assert payload["external_connection_enabled"] is False


def test_growth_metrics_do_not_invent_evidence() -> None:
    response = client.post(
        "/api/v1/publishing/growth/metrics",
        headers=CEO_HEADERS,
        json={
            "channel": "Blog/Web",
            "metric_name": "views",
            "value": 0,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["value"] == 0
    assert payload["evidence_status"] == "missing"
    assert payload["real_metric_confirmed"] is False


def test_cerebro_coordinates_pluma_lente_marketing() -> None:
    response = client.get("/api/v1/publishing/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    coordination = response.json()["cerebro_coordination"]
    assert "PLUMA" in coordination
    assert "LENTE" in coordination
    assert "MARKETING" in coordination
    assert "approval_rule" in coordination


def test_ceo_daily_center_shows_publishing() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["publishing"]["status"] == "publishing_growth_engine_prepared_internal"
    assert "Publishing & Growth" in payload["executive_summary"]


def test_control_center_shows_publishing_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "publishing-growth-engine" in html.text
    assert "/api/v1/publishing/status" in js.text
    assert "renderPublishingGrowth" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "campana pagada lanzada",
        "publicacion real confirmada",
        "metrica real confirmada",
        "venta real confirmada",
    ]:
        assert false_claim not in normalized
