from fastapi.testclient import TestClient

from app.core.metadata import APP_NAME, APP_VERSION
from app.main import app


def test_root_returns_service_metadata() -> None:
    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "service": APP_NAME,
        "status": "ok",
        "version": APP_VERSION,
    }


def test_health_contract() -> None:
    client = TestClient(app)

    response = client.get("/health")
    payload = response.json()

    assert response.status_code == 200
    assert payload["service"] == APP_NAME
    assert payload["status"] == "ok"
    assert "timestamp" in payload


def test_runtime_status_contract() -> None:
    client = TestClient(app)

    response = client.get("/runtime/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "operational"
    assert payload["service"] == APP_NAME
    assert payload["environment"] == "local"
    assert payload["version"] == APP_VERSION
    assert payload["database"] == "not_required"
    assert payload["storage"] == "not_required"
    assert payload["provider"] == "not_required"
    assert payload["memory"] == "not_required"
    assert "updated_at" in payload
