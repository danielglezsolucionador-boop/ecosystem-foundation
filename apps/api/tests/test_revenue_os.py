from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_revenue_endpoints_require_auth() -> None:
    paths = [
        "/api/v1/revenue/status",
        "/api/v1/revenue/goals",
        "/api/v1/revenue/opportunities",
        "/api/v1/revenue/approval-requests",
        "/api/v1/revenue/daily-report",
        "/api/v1/revenue/department-contribution",
    ]

    for path in paths:
        assert client.get(path).status_code == 401


def test_revenue_goals_exist_and_ecommerce_is_separate() -> None:
    response = client.get("/api/v1/revenue/goals", headers=CEO_HEADERS)

    assert response.status_code == 200
    goals = response.json()
    assert any(goal["scope"] == "global" and goal["monthly_target_usd"] == 6000 for goal in goals)
    assert any(
        goal["scope"] == "ecommerce"
        and goal["monthly_target_usd"] == 10000
        and goal["separated_from_global"] is True
        for goal in goals
    )


def test_revenue_status_reports_no_real_revenue_and_separate_pipelines() -> None:
    response = client.get("/api/v1/revenue/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "revenue_os_prepared_internal"
    assert payload["actual_revenue_usd"] == 0
    assert payload["actual_revenue_status"] == "no_real_revenue_reported"
    assert payload["global_goal"]["monthly_target_usd"] == 6000
    assert payload["ecommerce_goal"]["monthly_target_usd"] == 10000
    assert payload["ecommerce_goal"]["separated_from_global"] is True
    assert payload["external_connection_enabled"] is False
    assert payload["payment_connected"] is False
    assert payload["sunat_enabled"] is False


def test_opportunity_with_investment_calculates_net_profit_and_goal_contribution() -> None:
    response = client.post(
        "/api/v1/revenue/opportunities",
        headers=CEO_HEADERS,
        json={
            "title": f"Paid matrix {uuid4()}",
            "origin": "CEREBRO",
            "department": "MARKETING",
            "related_product": "DCFT",
            "action_type": "paid_campaign",
            "investment_usd": 100,
            "expected_revenue_usd": 600,
            "probability_percent": 70,
            "payback_time": "7 days",
            "risk": "controlled",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    matrix = payload["economic_matrix"]
    assert payload["requires_ceo_approval"] is True
    assert payload["status"] == "waiting_ceo_approval"
    assert matrix["expected_net_profit_usd"] == 500
    assert matrix["roi_percent"] == 500
    assert matrix["monthly_goal_contribution_percent"] == 8.33
    assert matrix["status"] == "calculated"


def test_opportunity_without_data_does_not_invent_roi() -> None:
    response = client.post(
        "/api/v1/revenue/opportunities",
        headers=CEO_HEADERS,
        json={
            "title": f"Needs data {uuid4()}",
            "origin": "Buscador de Tendencias",
            "department": "PLUMA",
            "action_type": "analysis",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "needs_more_data"
    assert payload["requires_ceo_approval"] is False
    assert payload["economic_matrix"]["status"] == "needs_more_data"
    assert payload["economic_matrix"]["roi_percent"] is None
    assert "no inventar ROI" in payload["economic_matrix"]["recommendation"]


def test_organic_and_local_agent_actions_do_not_require_approval() -> None:
    organic = client.post(
        "/api/v1/revenue/opportunities",
        headers=CEO_HEADERS,
        json={
            "title": f"Organic content {uuid4()}",
            "origin": "CEREBRO",
            "department": "PLUMA",
            "action_type": "organic",
            "expected_revenue_usd": 500,
            "probability_percent": 40,
            "payback_time": "30 days",
        },
    )
    local_agent = client.post(
        "/api/v1/revenue/opportunities",
        headers=CEO_HEADERS,
        json={
            "title": f"Local Agent prepared classification {uuid4()}",
            "origin": "CEREBRO",
            "department": "HERMES",
            "action_type": "local_agent_activation",
            "expected_revenue_usd": 0,
            "probability_percent": 0,
            "payback_time": "not_estimated",
        },
    )

    assert organic.status_code == 201
    assert local_agent.status_code == 201
    assert organic.json()["requires_ceo_approval"] is False
    assert local_agent.json()["requires_ceo_approval"] is False
    assert local_agent.json()["runtime_connected"] is False


def test_paid_campaign_requires_approval_and_can_request_ceo_approval() -> None:
    created = client.post(
        "/api/v1/revenue/opportunities",
        headers=CEO_HEADERS,
        json={
            "title": f"Paid campaign approval {uuid4()}",
            "origin": "MARKETING",
            "department": "MARKETING",
            "action_type": "paid_campaign",
            "investment_usd": 100,
            "expected_revenue_usd": 600,
            "probability_percent": 80,
            "payback_time": "7 days",
            "recommendation": "Aprobar solo si CEO acepta el gasto.",
        },
    )
    opportunity_id = created.json()["id"]
    approval = client.post(
        f"/api/v1/revenue/opportunities/{opportunity_id}/request-approval",
        headers=CEO_HEADERS,
    )

    assert created.status_code == 201
    assert created.json()["requires_ceo_approval"] is True
    assert approval.status_code == 200
    payload = approval.json()
    assert payload["opportunity_id"] == opportunity_id
    assert payload["status"] == "pending_ceo"
    assert payload["payment_connected"] is False
    assert payload["cerebro_approval_request_id"]


def test_ecommerce_opportunity_contributes_only_to_ecommerce_goal() -> None:
    response = client.post(
        "/api/v1/revenue/opportunities",
        headers=CEO_HEADERS,
        json={
            "title": f"Amazon signal {uuid4()}",
            "origin": "SNIFF AMAZON",
            "department": "SNIFF AMAZON",
            "related_product": "ecommerce",
            "action_type": "organic",
            "expected_revenue_usd": 1000,
            "probability_percent": 50,
            "payback_time": "21 days",
            "ecommerce_separate": True,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    matrix = payload["economic_matrix"]
    assert payload["contributes_to_global_goal"] is False
    assert payload["contributes_to_ecommerce_goal"] is True
    assert matrix["monthly_goal_contribution_percent"] is None
    assert matrix["ecommerce_goal_contribution_percent"] == 10


def test_department_contribution_includes_monetization_roles() -> None:
    response = client.get("/api/v1/revenue/department-contribution", headers=CEO_HEADERS)

    assert response.status_code == 200
    rows = response.json()
    by_id = {row["department_id"]: row for row in rows}
    assert by_id["pluma"]["target_scope"] == "global"
    assert by_id["marketing"]["target_scope"] == "global"
    assert by_id["ecommerce"]["target_scope"] == "ecommerce"
    assert by_id["sniff_amazon"]["target_scope"] == "ecommerce"
    assert by_id["auditoria"]["target_scope"] == "indirect"
    assert all(row["external_connection_enabled"] is False for row in rows)


def test_cerebro_and_ceo_daily_center_include_revenue_os() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert "revenue" in payload
    assert payload["revenue"]["status"] == "revenue_os_prepared_internal"
    assert payload["cerebro"]["revenue_os"]["status"] == "revenue_os_prepared_internal"
    assert "Revenue OS" in payload["executive_summary"]
    assert payload["revenue"]["payment_connected"] is False


def test_control_center_shows_revenue_os_without_false_money_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "Revenue OS" in html.text
    assert "/api/v1/revenue/status" in js.text
    assert "renderRevenueOs" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "ingreso real confirmado",
        "pago real conectado",
        "stripe conectado",
        "sunat activo",
        "venta automatica real",
    ]:
        assert false_claim not in normalized
