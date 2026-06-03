from fastapi.testclient import TestClient

from app.main import APP_NAME, APP_VERSION, app


def test_root_returns_service_metadata() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": APP_NAME,
        "status": "ok",
        "version": APP_VERSION,
    }

