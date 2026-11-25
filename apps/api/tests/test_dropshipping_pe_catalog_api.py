from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers

PREFIX = "/api/v1/ecommerce-readiness/dropshipping-pe"
SCENARIO = dict(price="89", supplier_cost="20", delivered_shipping="15",
                failed_shipping="10", advertising_per_order="12", delivery_rate="0.8",
                payment_rate="0.05", reserve_per_delivery="4")


def test_catalog_and_mock_comparison_require_auth():
    client = TestClient(app)
    payload = {"candidate_id": "PE-019", "quotes": [{"provider": "Aliclik", "economics": SCENARIO}]}
    assert client.get(PREFIX + "/catalog").status_code == 401
    assert client.post(PREFIX + "/provider-comparison", json=payload).status_code == 401
    headers = auth_headers(client, ControlCenterRole.ceo)
    response = client.get(PREFIX + "/catalog", headers=headers)
    assert response.status_code == 200
    assert len(response.json()["items"]) == 30
    response = client.post(PREFIX + "/provider-comparison", headers=headers, json=payload)
    assert response.status_code == 200
    assert response.json()["recommended_supplier"] is None
    assert response.json()["ranked_hypothetical_quotes"][0]["contribution_per_delivery_pen"] == "14.47"
    assert client.post(PREFIX + "/provider-comparison", headers=headers,
                       json={**payload, "candidate_id": "PE-999"}).status_code == 422
    assert client.post(PREFIX + "/provider-comparison", headers=headers,
                       json={**payload, "live": True}).status_code == 422
