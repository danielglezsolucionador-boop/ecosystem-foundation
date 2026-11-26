from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers

PREFIX = "/api/v1/ecommerce-readiness/dropshipping-pe"
SCENARIO = dict(price="89", supplier_cost="20", delivered_shipping="15",
                failed_shipping="10", advertising_per_order="12", delivery_rate="0.8",
                payment_rate="0.05", reserve_per_delivery="4")


def test_dropshipping_auth_and_scenarios():
    client = TestClient(app)
    assert client.get(PREFIX + "/status").status_code == 401
    assert client.post(PREFIX + "/financial-scenario", json=SCENARIO).status_code == 401
    assert client.post(PREFIX + "/order-simulation", json={"events": []}).status_code == 401
    headers = auth_headers(client, ControlCenterRole.ceo)
    status = client.get(PREFIX + "/status", headers=headers)
    assert status.status_code == 200
    assert status.json()["live_enabled"] is False
    financial = client.post(PREFIX + "/financial-scenario", headers=headers, json=SCENARIO)
    assert financial.status_code == 200
    assert financial.json()["contribution_per_delivery"] == "14.47"
    assert not financial.json()["meets_provisional_target"]
    assert client.post(PREFIX + "/financial-scenario", headers=headers,
                       json={**SCENARIO, "delivery_rate": "0"}).status_code == 422
    assert client.post(PREFIX + "/order-simulation", headers=headers,
                       json={"events": ["dispatch"]}).status_code == 422
    order = client.post(PREFIX + "/order-simulation", headers=headers,
                        json={"events": ["confirm", "dispatch", "deliver"]})
    assert order.status_code == 200
    assert order.json()["state"] == "delivered"
    assert order.json()["real_order_created"] is False
    assert client.post(PREFIX + "/order-simulation", headers=headers,
                       json={"events": [], "live": True}).status_code == 422
