from fastapi.testclient import TestClient
from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers

PREFIX = "/api/v1/ecommerce-readiness/dropshipping-pe"


def test_dropshipping_routes_do_not_use_disabled_auth_bypass(monkeypatch):
    client = TestClient(app)
    monkeypatch.setenv("CONTROL_CENTER_AUTH_ENABLED", "true")
    headers = auth_headers(client, ControlCenterRole.ceo)
    monkeypatch.setenv("CONTROL_CENTER_AUTH_ENABLED", "false")
    for suffix in ("/status", "/catalog", "/pipeline-contract", "/evidence", "/playbooks"):
        assert client.get(PREFIX + suffix).status_code == 401
    assert client.get(PREFIX + "/status", headers=headers).status_code == 200
    assert client.get(PREFIX + "/evidence", headers=headers).status_code == 403
