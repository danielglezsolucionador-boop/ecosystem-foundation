from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers

PREFIX = "/api/v1/ecommerce-readiness/dropshipping-pe/growth"
SCENARIO = dict(spend_cents=12000, budget_cap_cents=30000, orders=15,
                delivered_paid=12, failed_or_refunded=3, pending=0,
                net_sales_ex_vat_cents=90000, non_ad_costs_cents=50000)


def test_growth_routes():
    client = TestClient(app)
    path = PREFIX + "/creative-plan?candidate=PE-019&platform=tiktok"
    assert client.get(path).status_code == 401
    assert client.post(PREFIX + "/creative-review", json={}).status_code == 401
    assert client.post(PREFIX + "/campaign-simulation", json=SCENARIO).status_code == 401
    headers = auth_headers(client, ControlCenterRole.ceo)
    assert len(client.get(path, headers=headers).json()["scripts"]) == 3
    assert client.post(PREFIX + "/creative-review", headers=headers, json={}).json()["approved_for_publication"] is False
    result = client.post(PREFIX + "/campaign-simulation", headers=headers, json=SCENARIO)
    assert result.status_code == 200
    assert result.json()["decision"] == "review_scaling_with_ceo"
    assert not result.json()["spend_executed"]
    assert client.post(PREFIX + "/campaign-simulation", headers=headers,
                       json={**SCENARIO, "live": True}).status_code == 422
