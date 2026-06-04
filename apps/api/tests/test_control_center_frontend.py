from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_control_center_frontend_is_served() -> None:
    response = client.get("/control-center")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Control Center" in response.text
    assert "/control-center/assets/app.js" in response.text


def test_control_center_assets_are_served() -> None:
    css_response = client.get("/control-center/assets/styles.css")
    js_response = client.get("/control-center/assets/app.js")

    assert css_response.status_code == 200
    assert "text/css" in css_response.headers["content-type"]
    assert js_response.status_code == 200
    assert "javascript" in js_response.headers["content-type"]
    assert "/api/v1/control-center" in js_response.text
