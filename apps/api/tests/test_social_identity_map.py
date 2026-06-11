from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_social_identity_endpoints_require_auth() -> None:
    paths = [
        "/api/v1/social-identity/status",
        "/api/v1/social-identity/accounts",
        "/api/v1/social-identity/accounts/marca_personal_tiktok",
        "/api/v1/social-identity/approval-needed",
        "/api/v1/social-identity/risks",
    ]

    for path in paths:
        assert client.get(path).status_code == 401


def test_social_identity_status_is_safe_readiness_inventory() -> None:
    response = client.get("/api/v1/social-identity/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "social_identity_map_prepared"
    assert payload["total_accounts"] >= 30
    assert payload["unknown"] >= 1
    assert payload["prepared"] >= 1
    assert payload["proposed_new"] >= 1
    assert payload["needs_ceo"] >= 1
    assert payload["needs_credentials"] >= 1
    assert payload["needs_account_creation"] >= 1
    assert payload["confirmed_existing"] == 0
    assert payload["account_connected"] is False
    assert payload["real_publication_enabled"] is False
    assert payload["external_connection_enabled"] is False
    assert payload["credentials_stored"] is False


def test_unconfirmed_account_remains_unknown_without_evidence() -> None:
    response = client.get("/api/v1/social-identity/accounts/marca_personal_tiktok", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "unknown"
    assert payload["evidence"] == "missing"
    assert payload["requires_ceo"] is True
    assert payload["account_connected"] is False
    assert payload["real_publication_enabled"] is False


def test_new_account_requires_ceo_and_account_creation() -> None:
    response = client.get("/api/v1/social-identity/accounts/lente_tiktok", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "proposed_new"
    assert payload["requires_ceo"] is True
    assert payload["requires_account_creation"] is True
    assert payload["external_connection_enabled"] is False


def test_prepared_account_does_not_publish_or_store_credentials() -> None:
    response = client.get("/api/v1/social-identity/accounts/pluma_blog", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "prepared"
    assert payload["can_continue_prepared"] is True
    assert payload["requires_ceo"] is False
    assert payload["account_connected"] is False
    assert payload["real_publication_enabled"] is False
    assert payload["credentials_stored"] is False
    serialized = str(payload).lower()
    assert "password" not in serialized
    assert "api_key" not in serialized
    assert "token" not in serialized


def test_social_identity_approval_needed_and_risks_fallback_200() -> None:
    approvals = client.get("/api/v1/social-identity/approval-needed", headers=CEO_HEADERS)
    risks = client.get("/api/v1/social-identity/risks", headers=CEO_HEADERS)

    assert approvals.status_code == 200
    assert risks.status_code == 200
    approval_payload = approvals.json()
    risk_payload = risks.json()
    assert len(approval_payload) >= 1
    assert len(risk_payload) >= 1
    assert all(item["real_publication_enabled"] is False for item in approval_payload[:10])
    assert all(item["credentials_stored"] is False for item in risk_payload[:10])


def test_ceo_daily_center_can_read_social_identity_summary() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["social_identity"]["status"] == "social_identity_map_prepared"
    assert payload["social_identity"]["confirmed_existing"] == 0
    assert "Social Identity Map" in payload["executive_summary"]
    assert "sin publicacion real" in payload["executive_summary"]


def test_control_center_shows_social_identity_panel_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "social-identity-map" in html.text
    assert "/api/v1/social-identity/status" in js.text
    assert "renderSocialIdentityMap" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "cuenta social conectada",
        "publicacion real habilitada",
        "credenciales guardadas",
        "account_connected=true",
        "real_publication_enabled=true",
        "credentials_stored=true",
    ]:
        assert false_claim not in normalized
