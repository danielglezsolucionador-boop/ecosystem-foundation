from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers

PREFIX = "/api/v1/ecommerce-readiness/dropshipping-pe"


def test_integration_contract_is_authenticated_and_fail_closed():
    c = TestClient(app)
    assert c.get(PREFIX+"/integration-contract").status_code == 401
    h = auth_headers(c,ControlCenterRole.ceo)
    assert c.get(PREFIX+"/integration-contract",headers=h).json()["live_enabled"] is False
    result = c.post(PREFIX+"/supplier-checklist",headers=h,json={"provider":"Dropi"})
    assert result.status_code == 200 and not result.json()["approved_for_sale"]
    assert c.post(PREFIX+"/supplier-checklist",headers=h,json={"provider":"Dropi","token":"no"}).status_code == 422
    r = c.post(PREFIX+"/offer-scenario",headers=h,json={"price":"89","supplier_cost":"20",
        "delivered_shipping":"15","failed_shipping":"10","advertising_per_order":"12",
        "delivery_rate":".8","payment_rate":".05","reserve_per_delivery":"4"})
    assert r.status_code == 200
    assert r.json()["budget_approved"] is False and r.json()["contribution_per_delivery"] == "14.47"
