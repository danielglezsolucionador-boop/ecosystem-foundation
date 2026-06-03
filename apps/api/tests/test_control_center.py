from fastapi.testclient import TestClient

from app.main import app


def test_control_center_overview_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/control-center/overview")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "local_operational"
    assert payload["registry_source"] == "local_controlled_registry"
    assert payload["external_connections_enabled"] is False
    assert len(payload["metrics"]) == 4
    assert len(payload["next_actions"]) == 3
    assert payload["risks"]


def test_control_center_overview_uses_app_registry_counts() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/control-center/overview")
    metrics = {item["id"]: item for item in response.json()["metrics"]}

    assert metrics["registered_apps"]["value"] == 13
    assert metrics["planned_apps"]["value"] == 8
    assert metrics["external_references"]["value"] == 3
    assert metrics["storage_backend"]["value"] == "sqlite"


def test_control_center_does_not_enable_external_connections() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/control-center/overview")
    payload = response.json()

    assert payload["external_connections_enabled"] is False
    assert any("External app runtime is not connected" in risk for risk in payload["risks"])
    assert any("DATABASE_URL" in risk for risk in payload["risks"])
