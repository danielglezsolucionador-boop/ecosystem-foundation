from fastapi.testclient import TestClient

from app.core.metadata import APP_NAME
from app.main import app


def test_observability_status_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/observability/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "local_observable"
    assert payload["service"] == APP_NAME
    assert payload["environment"] == "local"
    assert len(payload["metrics"]) == 5


def test_observability_status_contains_core_metrics() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/observability/status")
    metrics = {item["id"]: item for item in response.json()["metrics"]}

    assert metrics["registered_apps"]["value"] == 13
    assert metrics["external_connections_enabled"]["value"] is False
    assert metrics["storage_backend"]["value"] == "sqlite"
    assert isinstance(metrics["memory_entries"]["value"], int)
    assert isinstance(metrics["audit_reports"]["value"], int)

