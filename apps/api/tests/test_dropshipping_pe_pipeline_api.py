from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers

PREFIX = "/api/v1/ecommerce-readiness/dropshipping-pe"


def test_pipeline_auth_and_reconciliation():
    client = TestClient(app)
    payload = {
        "provider": "Dropi", "cart": {"lines": [{"product_id": "PE-019", "pack": 1,
        "quantity": 1}], "region": "lima"},
        "events": [{"event_id": f"DEMO-{i}", "code": f"DEMO_DROPI_{stage}"}
                   for i, stage in enumerate(["CONFIRMED", "DISPATCHED", "DELIVERED"], 1)],
        "product_cost_cents": 2000, "logistics_cost_cents": 1500,
        "advertising_cost_cents": 1200, "provider_fee_cents": 500,
        "observed_remittance_cents": 9600,
    }
    assert client.get(PREFIX + "/pipeline-contract").status_code == 401
    assert client.post(PREFIX + "/pipeline-simulation", json=payload).status_code == 401
    headers = auth_headers(client, ControlCenterRole.ceo)
    assert client.get(PREFIX + "/pipeline-contract", headers=headers).json()["live_enabled"] is False
    response = client.post(PREFIX + "/pipeline-simulation", headers=headers, json=payload)
    assert response.status_code == 200
    assert response.json()["reconciliation"] == "matched"
    assert response.json()["real_order_created"] is False
    assert client.post(PREFIX + "/pipeline-simulation", headers=headers,
                       json={**payload, "live": True}).status_code == 422
