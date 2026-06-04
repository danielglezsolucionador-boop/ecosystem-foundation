from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_control_center_frontend_is_served() -> None:
    response = client.get("/control-center")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Control Center" in response.text
    assert "/control-center/assets/app.js" in response.text
    assert "role-select" in response.text
    assert "Governance UI Actions" in response.text
    assert "Decision Center" in response.text
    assert "Approval Center" in response.text
    assert "Integration Gates" in response.text
    assert "Policy Center" in response.text
    assert "Risk Center" in response.text
    assert "Governance Audit" in response.text
    assert "Governance Reports" in response.text


def test_control_center_assets_are_served() -> None:
    css_response = client.get("/control-center/assets/styles.css")
    js_response = client.get("/control-center/assets/app.js")

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert "/api/v1/control-center" in js_response.text
    assert "/api/v1/governance/auth-boundary" in js_response.text
    assert "executePendingAction" in js_response.text
    assert "escalate_approval" in js_response.text
    assert "forbidden" in css_response.text
