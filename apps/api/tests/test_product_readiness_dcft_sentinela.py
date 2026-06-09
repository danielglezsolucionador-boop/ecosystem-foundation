from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_product_readiness_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/product-readiness/status"),
        ("GET", "/api/v1/product-readiness/dcft"),
        ("POST", "/api/v1/product-readiness/dcft/audit"),
        ("GET", "/api/v1/product-readiness/sentinela"),
        ("POST", "/api/v1/product-readiness/sentinela/audit"),
        ("GET", "/api/v1/product-readiness/gaps"),
        ("POST", "/api/v1/product-readiness/gaps/not-real/send-to-forja"),
        ("GET", "/api/v1/product-readiness/marketing-package"),
        ("POST", "/api/v1/product-readiness/marketing-package/generate"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_product_readiness_status_keeps_marketing_as_sales_owner() -> None:
    response = client.get("/api/v1/product-readiness/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "product_readiness_prepared_requires_validation"
    assert payload["marketing_owner"] == "MARKETING"
    assert payload["products"] == 2
    assert payload["products_with_own_sales_goal"] == 0
    assert payload["sunat_enabled"] is False
    assert payload["paid_campaign_enabled"] is False
    assert payload["open_gaps"] >= 1


def test_dcft_has_no_own_sales_goal_and_unknowns_when_evidence_missing() -> None:
    response = client.get("/api/v1/product-readiness/dcft", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["sales_owner"] == "MARKETING"
    assert payload["has_own_sales_goal"] is False
    assert payload["marketing_sells"] is True
    assert payload["technical_status"] == "unknown"
    assert payload["commercial_status"] == "requires_validation"
    assert payload["evidence_status"] == "missing"
    assert payload["sunat_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["gaps"]


def test_sentinela_is_security_product_without_own_sales_goal_or_future_b2b_label() -> None:
    response = client.get("/api/v1/product-readiness/sentinela", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["sales_owner"] == "MARKETING"
    assert payload["has_own_sales_goal"] is False
    assert payload["marketing_sells"] is True
    assert payload["commercial_status"] == "requires_validation"
    assert payload["runtime_connected"] is False
    assert "future product b2b" not in payload["description"].lower()
    assert "futuro producto b2b" not in payload["description"].lower()


def test_product_audit_does_not_invent_ready_claims() -> None:
    response = client.post(
        "/api/v1/product-readiness/dcft/audit",
        headers=CEO_HEADERS,
        json={"notes": "Revision local sin evidencia oficial."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["audit_status"] == "requires_validation"
    assert payload["commercial_status"] == "requires_validation"
    assert payload["evidence_status"] == "missing"
    assert payload["app_store_publication_enabled"] is False
    assert payload["play_store_publication_enabled"] is False


def test_send_gap_to_forja_is_prepared_not_implemented() -> None:
    gaps = client.get("/api/v1/product-readiness/gaps", headers=CEO_HEADERS).json()
    target = next(gap for gap in gaps if gap["product_id"] == "sentinela")

    response = client.post(
        f"/api/v1/product-readiness/gaps/{target['id']}/send-to-forja",
        headers=CEO_HEADERS,
        json={"instruction": "Preparar mejora sin tocar SENTINELA real."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "sent_to_forja"
    assert payload["forge_status"] == "prepared"
    assert payload["technical_status"] == "pending_execution"
    assert payload["requires_validation"] is True


def test_marketing_package_does_not_invent_legal_or_security_claims() -> None:
    response = client.post("/api/v1/product-readiness/marketing-package/generate", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["owner"] == "MARKETING"
    assert payload["no_legal_claims_without_source"] is True
    assert payload["no_security_claims_without_evidence"] is True
    assert payload["paid_campaign_requires_ceo_approval"] is True
    assert len(payload["items"]) == 2
    for item in payload["items"]:
        assert item["sales_owner"] == "MARKETING"
        assert item["has_own_sales_goal"] is False
        assert item["claim_status"] == "requires_validation"
        assert item["readiness_status"] == "requires_validation"


def test_ceo_daily_center_shows_product_readiness() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["product_readiness"]["status"] == "product_readiness_prepared_requires_validation"
    assert "Product Readiness DCFT/SENTINELA" in payload["executive_summary"]
    assert "MARKETING vende" in payload["executive_summary"]


def test_control_center_shows_product_readiness_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "product-readiness-dcft-sentinela" in html.text
    assert "/api/v1/product-readiness/status" in js.text
    assert "renderProductReadiness" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "dcft listo para vender",
        "sentinela listo para vender",
        "sunat real activado",
        "app store publicado",
        "campana pagada activa",
    ]:
        assert false_claim not in normalized
