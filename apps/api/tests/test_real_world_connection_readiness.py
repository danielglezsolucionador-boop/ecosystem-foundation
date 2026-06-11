from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_real_world_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/real-world/status"),
        ("GET", "/api/v1/real-world/connections"),
        ("GET", "/api/v1/real-world/connections/marketing_meta_ads"),
        ("POST", "/api/v1/real-world/connections/marketing_meta_ads/mark-prepared"),
        ("POST", "/api/v1/real-world/connections/marketing_meta_ads/request-ceo-definition"),
        ("POST", "/api/v1/real-world/connections/marketing_meta_ads/request-approval"),
        ("GET", "/api/v1/real-world/approval-needed"),
        ("GET", "/api/v1/real-world/risks"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_real_world_status_is_safe_prepared_inventory() -> None:
    response = client.get("/api/v1/real-world/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "real_world_connection_readiness_prepared"
    assert payload["total_connections"] >= 50
    assert payload["connected"] == 0
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["real_publication_enabled"] is False
    assert payload["paid_campaign_launched"] is False
    assert payload["payment_connected"] is False
    assert payload["sunat_enabled"] is False
    assert payload["secrets_stored"] is False
    assert payload["unknown"] >= 1
    assert payload["prepared"] >= 1
    assert payload["needs_ceo"] >= 1
    assert payload["needs_credentials"] >= 1
    assert payload["needs_paid_approval"] >= 1


def test_unknown_when_evidence_is_missing() -> None:
    response = client.get("/api/v1/real-world/connections/marca_personal_tiktok", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "unknown"
    assert payload["evidence"] == "missing"
    assert payload["requires_ceo"] is True
    assert payload["external_connection_enabled"] is False


def test_money_and_external_accounts_require_ceo() -> None:
    paid = client.get("/api/v1/real-world/connections/marketing_meta_ads", headers=CEO_HEADERS)
    external_account = client.get("/api/v1/real-world/connections/amazon_seller", headers=CEO_HEADERS)

    assert paid.status_code == 200
    assert external_account.status_code == 200
    paid_payload = paid.json()
    account_payload = external_account.json()
    assert paid_payload["state"] == "needs_paid_approval"
    assert paid_payload["requires_ceo"] is True
    assert paid_payload["requires_money"] is True
    assert paid_payload["paid_campaign_launched"] is False
    assert account_payload["state"] == "needs_account_creation"
    assert account_payload["requires_ceo"] is True
    assert account_payload["requires_credentials"] is True


def test_real_publication_in_unconfirmed_account_requires_ceo() -> None:
    response = client.get("/api/v1/real-world/connections/publishing_tiktok", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "unknown"
    assert payload["requires_ceo"] is True
    assert payload["real_publication_enabled"] is False


def test_prepared_connection_does_not_require_ceo_or_runtime() -> None:
    response = client.post(
        "/api/v1/real-world/connections/apis_documentation/mark-prepared",
        headers=CEO_HEADERS,
        json={"note": "Preparar documentacion interna sin secretos."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "prepared"
    assert payload["requires_ceo"] is False
    assert payload["can_continue_prepared"] is True
    assert payload["runtime_connected"] is False
    assert payload["secrets_stored"] is False


def test_secret_like_values_are_rejected_and_not_stored() -> None:
    response = client.post(
        "/api/v1/real-world/connections/apis_documentation/mark-prepared",
        headers=CEO_HEADERS,
        json={"note": "password=DoNotStore123"},
    )

    assert response.status_code == 400
    payload = response.json()
    assert payload["detail"]["error"] == "real_world_secret_like_value_rejected"
    after = client.get("/api/v1/real-world/connections/apis_documentation", headers=CEO_HEADERS).json()
    assert after["secrets_stored"] is False
    assert "DoNotStore123" not in after["notes"]


def test_request_approval_keeps_external_execution_disabled() -> None:
    response = client.post(
        "/api/v1/real-world/connections/web_factory_domains/request-approval",
        headers=CEO_HEADERS,
        json={"reason": "Solicitud preparada con ROI pendiente."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["requires_ceo"] is True
    assert payload["requires_money"] is True
    assert payload["state"] == "needs_paid_approval"
    assert payload["external_connection_enabled"] is False
    assert payload["payment_connected"] is False


def test_approval_needed_and_risks_are_safe_fallback_200() -> None:
    approvals = client.get("/api/v1/real-world/approval-needed", headers=CEO_HEADERS)
    risks = client.get("/api/v1/real-world/risks", headers=CEO_HEADERS)

    assert approvals.status_code == 200
    assert risks.status_code == 200
    assert len(approvals.json()) >= 1
    assert len(risks.json()) >= 1
    assert all(item["external_connection_enabled"] is False for item in approvals.json()[:10])


def test_ceo_daily_center_can_read_real_world_summary() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["real_world"]["status"] == "real_world_connection_readiness_prepared"
    assert payload["real_world"]["connected"] == 0
    assert "Real World Connections" in payload["executive_summary"]
    assert "no hay ejecucion externa" in payload["executive_summary"]


def test_control_center_shows_real_world_panel_without_false_connection_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "real-world-connections" in html.text
    assert "/api/v1/real-world/status" in js.text
    assert "renderRealWorldConnections" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "cuenta externa creada",
        "campana pagada lanzada",
        "sunat real activado",
        "payment_connected=true",
        "secrets_stored=true",
    ]:
        assert false_claim not in normalized
