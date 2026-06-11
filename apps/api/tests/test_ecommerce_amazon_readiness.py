from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_ecommerce_amazon_endpoints_require_auth() -> None:
    paths = [
        "/api/v1/ecommerce-readiness/status",
        "/api/v1/ecommerce-readiness/opportunities",
        "/api/v1/ecommerce-readiness/approval-needed",
        "/api/v1/amazon-readiness/status",
        "/api/v1/amazon-readiness/opportunities",
        "/api/v1/amazon-readiness/risks",
    ]

    for path in paths:
        assert client.get(path).status_code == 401


def test_ecommerce_status_keeps_goal_separate_from_global() -> None:
    response = client.get("/api/v1/ecommerce-readiness/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ecommerce_readiness_prepared"
    assert payload["monthly_goal_usd"] == 10000
    assert payload["global_goal_usd"] == 6000
    assert payload["separated_from_global_goal"] is True
    assert payload["actual_revenue_usd"] == 0
    assert payload["actual_sales_confirmed"] is False
    assert payload["margin_invented"] is False
    assert payload["payment_connected"] is False
    assert payload["store_created"] is False
    assert payload["inventory_purchased"] is False
    assert payload["external_connection_enabled"] is False


def test_investment_supplier_and_payment_require_ceo() -> None:
    opportunities = client.get("/api/v1/ecommerce-readiness/opportunities", headers=CEO_HEADERS).json()
    approval_needed = client.get("/api/v1/ecommerce-readiness/approval-needed", headers=CEO_HEADERS).json()

    supplier = next(item for item in opportunities if item["id"] == "ecommerce_supplier_map")
    payment = next(item for item in opportunities if item["id"] == "ecommerce_payment_provider")
    assert supplier["state"] == "needs_supplier"
    assert supplier["requires_ceo"] is True
    assert supplier["requires_inventory"] is True
    assert supplier["inventory_purchased"] is False
    assert payment["state"] == "needs_payment_provider"
    assert payment["requires_ceo"] is True
    assert payment["requires_payment_provider"] is True
    assert payment["payment_connected"] is False
    assert {item["id"] for item in approval_needed} >= {"ecommerce_supplier_map", "ecommerce_payment_provider"}


def test_amazon_account_and_paid_tools_are_blocked_for_ceo() -> None:
    opportunities = client.get("/api/v1/amazon-readiness/opportunities", headers=CEO_HEADERS).json()
    status = client.get("/api/v1/amazon-readiness/status", headers=CEO_HEADERS).json()

    seller = next(item for item in opportunities if item["id"] == "amazon_seller_account")
    paid_tool = next(item for item in opportunities if item["id"] == "amazon_paid_research_tool")
    assert seller["state"] == "needs_account_creation"
    assert seller["requires_ceo"] is True
    assert seller["requires_external_account"] is True
    assert seller["amazon_seller_connected"] is False
    assert paid_tool["state"] == "needs_paid_tool"
    assert paid_tool["requires_paid_tool"] is True
    assert status["amazon_seller_connected"] is False
    assert status["paid_tool_connected"] is False


def test_no_margin_sales_or_winning_products_are_invented() -> None:
    ecommerce = client.get("/api/v1/ecommerce-readiness/opportunities", headers=CEO_HEADERS).json()
    amazon = client.get("/api/v1/amazon-readiness/opportunities", headers=CEO_HEADERS).json()
    amazon_status = client.get("/api/v1/amazon-readiness/status", headers=CEO_HEADERS).json()

    for item in ecommerce + amazon:
        assert item["real_sales_confirmed"] is False
        assert item["real_margin_confirmed"] is False
        assert item["margin_estimated"] in {"unknown_not_estimated", "unknown_requires_ceo"}
        assert item["prohibited_scraping_enabled"] is False
    assert amazon_status["real_products_declared_winners"] is False
    assert amazon_status["real_sales_confirmed"] is False
    assert amazon_status["real_margin_confirmed"] is False
    assert amazon_status["prohibited_scraping_enabled"] is False


def test_amazon_risks_fallback_safe_200() -> None:
    risks = client.get("/api/v1/amazon-readiness/risks", headers=CEO_HEADERS)

    assert risks.status_code == 200
    payload = risks.json()
    assert len(payload) >= 1
    assert all(item["external_connection_enabled"] is False for item in payload)
    assert all(item["credentials_stored"] is False for item in payload)


def test_ceo_daily_center_reads_ecommerce_amazon_readiness() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["ecommerce_readiness"]["status"] == "ecommerce_readiness_prepared"
    assert payload["amazon_readiness"]["status"] == "amazon_readiness_prepared"
    assert payload["ecommerce_readiness"]["monthly_goal_usd"] == 10000
    assert "E-Commerce/Amazon Readiness" in payload["executive_summary"]
    assert "sin tienda, pagos, inventario, Amazon Seller" in payload["executive_summary"]


def test_control_center_shows_ecommerce_amazon_panel_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "ecommerce-amazon-readiness" in html.text
    assert "/api/v1/ecommerce-readiness/status" in js.text
    assert "renderEcommerceAmazonReadiness" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "producto ganador confirmado",
        "ventas reales confirmadas",
        "amazon seller conectado",
        "inventario comprado",
        "payment_connected=true",
        "prohibited_scraping_enabled=true",
    ]:
        assert false_claim not in normalized
