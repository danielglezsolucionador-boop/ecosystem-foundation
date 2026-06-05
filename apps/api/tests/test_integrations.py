from fastapi.testclient import TestClient

from app.main import app


def test_integration_contracts_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/integrations/contracts")
    payload = response.json()

    assert response.status_code == 200
    assert {contract["id"] for contract in payload} == {
        "app-registry.v1",
        "control-center-overview.v1",
        "permissions.v1",
        "memory.v1",
        "audit.v1",
        "external-app-runtime.v1",
        "hermes.discovery.v1",
    }


def test_external_runtime_contract_is_prepared_not_connected() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/integrations/contracts/external-app-runtime.v1")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "prepared_not_connected"
    assert payload["external_dependency"] is True
    assert payload["endpoint"] == "not_connected"


def test_integration_contract_missing_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/integrations/contracts/ghost.v1")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "contract_not_found",
            "contract_id": "ghost.v1",
        }
    }


def test_hermes_integration_profile_and_discovery_are_controlled() -> None:
    client = TestClient(app)

    profile_response = client.get("/api/v1/integrations/apps/hermes")
    discovery_response = client.get("/api/v1/integrations/apps/hermes/discovery")
    profile = profile_response.json()
    discovery = discovery_response.json()

    assert profile_response.status_code == 200
    assert profile["app_id"] == "hermes"
    assert profile["integration_status"] == "prepared_for_discovery"
    assert profile["external_connection_enabled"] is False
    assert profile["contract_id"] == "hermes.discovery.v1"

    assert discovery_response.status_code == 200
    assert discovery["app_id"] == "hermes"
    assert discovery["contract_id"] == "hermes.discovery.v1"
    assert discovery["external_connection_enabled"] is False
    assert isinstance(discovery["repository_detected"], bool)
    assert discovery["evidence_files_expected"]
    assert "No verified live HTTP API is connected for Hermes." in discovery["blockers"]


def test_integration_app_missing_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/integrations/apps/ghost/discovery")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "integration_app_not_found",
            "app_id": "ghost",
        }
    }
