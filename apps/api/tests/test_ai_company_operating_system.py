from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services import product_readiness as product_readiness_service
from app.services import publishing as publishing_service
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_ai_company_operating_system_core_endpoints_require_auth() -> None:
    paths = [
        "/api/v1/cerebro/chief-of-staff/status",
        "/api/v1/missions/reports/daily",
        "/api/v1/workday/status",
        "/api/v1/revenue/status",
        "/api/v1/revenue/sprint/status",
        "/api/v1/publishing/status",
        "/api/v1/product-readiness/status",
        "/api/v1/ceo/daily-center",
    ]

    for path in paths:
        assert client.get(path).status_code == 401


def test_r2_production_failed_endpoints_return_safe_authenticated_200() -> None:
    paths = [
        "/api/v1/publishing/status",
        "/api/v1/publishing/channels",
        "/api/v1/publishing/content",
        "/api/v1/product-readiness/status",
        "/api/v1/product-readiness/dcft",
        "/api/v1/product-readiness/sentinela",
    ]

    for path in paths:
        response = client.get(path, headers=CEO_HEADERS)
        assert response.status_code == 200, path

    publishing_status = client.get("/api/v1/publishing/status", headers=CEO_HEADERS).json()
    assert publishing_status["not_connected_accounts"] >= 1
    assert publishing_status["paid_campaigns_launched"] == 0
    assert publishing_status["payment_connected"] is False

    dcft = client.get("/api/v1/product-readiness/dcft", headers=CEO_HEADERS).json()
    sentinela = client.get("/api/v1/product-readiness/sentinela", headers=CEO_HEADERS).json()
    for payload in (dcft, sentinela):
        assert payload["sales_owner"] == "MARKETING"
        assert payload["has_own_sales_goal"] is False
        assert payload["app_store_publication_enabled"] is False
        assert payload["play_store_publication_enabled"] is False


def test_r2_payload_readers_accept_postgres_dict_rows() -> None:
    publishing_payload = publishing_service.payload_json_from_row({"payload_json": '{"account_status":"not_connected"}'})
    readiness_payload = product_readiness_service.payload_json_from_row({"payload_json": '{"evidence_status":"missing"}'})

    assert publishing_payload == {"account_status": "not_connected"}
    assert readiness_payload == {"evidence_status": "missing"}


def test_ai_company_os_exposes_cerebro_motto_and_internal_autonomy() -> None:
    response = client.get("/api/v1/cerebro/chief-of-staff/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["motto"] == "El tiempo es dinero"
    assert payload["runtime_connected"] is False
    assert payload["external_connection_enabled"] is False
    matrix = {item["action_type"]: item for item in payload["authority_matrix"]}
    assert matrix["local_agent_activation"]["level"] == "NO_APPROVAL_REQUIRED"
    assert matrix["organic_post_configured_account"]["level"] == "NO_APPROVAL_REQUIRED"
    assert matrix["real_money_payment"]["level"] == "CEO_APPROVAL_REQUIRED"
    assert matrix["paid_campaign"]["level"] == "CEO_APPROVAL_REQUIRED"


def test_ai_company_os_consolidates_missions_workday_revenue_and_ceo_center() -> None:
    mission = client.get("/api/v1/missions/reports/daily", headers=CEO_HEADERS)
    workday = client.get("/api/v1/workday/status", headers=CEO_HEADERS)
    revenue = client.get("/api/v1/revenue/sprint/status", headers=CEO_HEADERS)
    center = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert mission.status_code == 200
    assert workday.status_code == 200
    assert revenue.status_code == 200
    assert center.status_code == 200
    revenue_payload = revenue.json()
    center_payload = center.json()
    assert revenue_payload["global_goal_usd"] == 6000
    assert revenue_payload["ecommerce_goal_usd"] == 10000
    assert revenue_payload["actual_revenue_usd"] == 0
    assert revenue_payload["payment_connected"] is False
    assert center_payload["runtime_connected"] is False
    assert center_payload["external_connection_enabled"] is False
    assert center_payload["sunat_enabled"] is False
    assert center_payload["local_agent_enabled"] is False
    summary = center_payload["executive_summary"]
    assert "Chief of Staff OS" in summary
    assert "Revenue Sprint 30 dias" in summary
    assert "Publishing & Growth" in summary
    assert "Product Readiness DCFT/SENTINELA" in summary


def test_ai_company_os_keeps_dcft_sentinela_sales_owned_by_marketing() -> None:
    dcft = client.get("/api/v1/product-readiness/dcft", headers=CEO_HEADERS)
    sentinela = client.get("/api/v1/product-readiness/sentinela", headers=CEO_HEADERS)
    package = client.post("/api/v1/product-readiness/marketing-package/generate", headers=CEO_HEADERS)

    assert dcft.status_code == 200
    assert sentinela.status_code == 200
    assert package.status_code == 200
    for payload in (dcft.json(), sentinela.json()):
        assert payload["sales_owner"] == "MARKETING"
        assert payload["has_own_sales_goal"] is False
        assert payload["marketing_sells"] is True
        assert payload["runtime_connected"] is False
    assert all(item["sales_owner"] == "MARKETING" for item in package.json()["items"])


def test_ai_company_os_publishing_rules_do_not_invent_accounts_or_paid_campaigns() -> None:
    channel = client.post(
        "/api/v1/publishing/channels",
        headers=CEO_HEADERS,
        json={
            "name": f"R1 Oficial {uuid4()}",
            "platform": "LinkedIn",
            "account_status": "connected",
            "official_account": True,
            "organic_enabled": True,
        },
    ).json()
    organic = client.post(
        "/api/v1/publishing/content",
        headers=CEO_HEADERS,
        json={
            "title": f"Contenido organico R1 {uuid4()}",
            "format": "post",
            "department_owner": "MARCA PERSONAL",
            "channel": channel["name"],
            "publication_mode": "organic",
            "content_brief": "Cuenta oficial conectada: organico no requiere aprobacion CEO.",
        },
    )
    paid = client.post(
        "/api/v1/publishing/content",
        headers=CEO_HEADERS,
        json={
            "title": f"Paid R1 {uuid4()}",
            "format": "campaign",
            "department_owner": "MARKETING",
            "channel": channel["name"],
            "publication_mode": "paid",
            "content_brief": "Paid solo como propuesta; no lanzar campana real.",
        },
    )
    new_account = client.post(
        "/api/v1/publishing/channels",
        headers=CEO_HEADERS,
        json={
            "name": f"Cuenta externa R1 {uuid4()}",
            "platform": "TikTok",
            "new_external_account_requested": True,
        },
    )

    assert organic.status_code == 201
    organic_payload = organic.json()
    assert organic_payload["requires_approval"] is False
    assert organic_payload["approval_reason"] == "organic_configured_account_no_approval"
    assert organic_payload["actual_publication_confirmed"] is False
    assert paid.status_code == 201
    paid_payload = paid.json()
    assert paid_payload["requires_approval"] is True
    assert paid_payload["paid_campaign_launched"] is False
    assert new_account.status_code == 201
    assert new_account.json()["requires_approval"] is True


def test_ai_company_os_marks_unknown_or_prepared_when_ceo_definition_is_missing() -> None:
    content = client.post(
        "/api/v1/publishing/content",
        headers=CEO_HEADERS,
        json={
            "title": f"LENTE nicho pendiente R1 {uuid4()}",
            "format": "short",
            "department_owner": "LENTE",
            "channel": "YouTube Shorts",
            "publication_mode": "prepared",
            "content_brief": "Nicho final pendiente de definicion CEO.",
        },
    )
    dcft = client.get("/api/v1/product-readiness/dcft", headers=CEO_HEADERS)

    assert content.status_code == 201
    payload = content.json()
    assert payload["niche_status"] == "needs_ceo_definition"
    assert payload["publication_status"] == "prepared"
    assert payload["actual_publication_confirmed"] is False
    assert dcft.status_code == 200
    assert dcft.json()["technical_status"] == "unknown"
    assert dcft.json()["evidence_status"] == "missing"


def test_ai_company_control_center_does_not_claim_real_revenue_or_external_runtime() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "El tiempo es dinero" in html.text
    assert "Publishing & Growth" in html.text
    assert "Product Readiness DCFT/SENTINELA" in html.text
    normalized = js.text.lower()
    for false_claim in [
        "venta real confirmada",
        "ingreso real confirmado",
        "sunat real activado",
        "dcft real conectado",
        "sentinela real conectado",
        "campana pagada lanzada",
        "cuenta externa creada",
    ]:
        assert false_claim not in normalized
