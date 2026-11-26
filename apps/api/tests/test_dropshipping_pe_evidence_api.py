from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers

PREFIX = "/api/v1/ecommerce-readiness/dropshipping-pe"


def test_evidence_routes_require_auth_and_review_role(monkeypatch, tmp_path):
    from app.api import ecommerce_readiness as routes
    from types import SimpleNamespace
    monkeypatch.setattr(routes, "get_settings", lambda: SimpleNamespace(
        environment="local", database_url="sqlite:///" + str(tmp_path / "evidence.db")))
    client = TestClient(app)
    data = {"candidate": "PE-019", "provider": "Dropi", "kind": "stock", "reference": "DEMO-1"}
    assert client.get(PREFIX + "/playbooks").status_code == 401
    assert client.get(PREFIX + "/evidence").status_code == 401
    assert client.post(PREFIX + "/evidence", json=data).status_code == 401
    operator = auth_headers(client, ControlCenterRole.operator)
    ceo = auth_headers(client, ControlCenterRole.ceo)
    result = client.post(PREFIX + "/evidence", json=data, headers=operator)
    assert result.status_code == 201
    assert result.json()["approved_for_sale"] is False
    eid = result.json()["id"]
    url = PREFIX + "/evidence/" + eid + "/review"
    assert client.post(url, json={"decision": "accepted_demo"}, headers=operator).status_code == 403
    assert client.post(url, json={"decision": "accepted_demo"}, headers=ceo).status_code == 200
    assert client.post(url, json={"decision": "rejected_demo"}, headers=ceo).status_code == 422
    result = client.get(PREFIX + "/evidence", headers=ceo).json()
    assert result["items"][0]["decision"] == "accepted_demo"
    assert result["approved_for_sale"] is False
    assert len(client.get(PREFIX + "/playbooks", headers=ceo).json()["items"]) == 6
    monkeypatch.setattr(routes, "control_center_auth_enabled", lambda: False)
    assert client.get(PREFIX + "/evidence", headers=ceo).status_code == 403
