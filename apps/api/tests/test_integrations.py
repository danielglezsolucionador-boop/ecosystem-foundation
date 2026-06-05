from fastapi.testclient import TestClient

from app.main import app
from app.services import integration_apps


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
        "auditor.discovery.v1",
        "pluma.discovery.v1",
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
    assert discovery["evidence_source"] in {
        "runtime_repository",
        "versioned_local_discovery_snapshot",
    }
    assert discovery["evidence_files_expected"]
    assert discovery["evidence_files_found"]
    assert "No verified live HTTP API is connected for Hermes." in discovery["blockers"]


def test_hermes_discovery_uses_snapshot_when_runtime_repo_is_missing(monkeypatch) -> None:
    client = TestClient(app)
    monkeypatch.delenv("HERMES_KNOWLEDGE_CORE_PATH", raising=False)
    monkeypatch.setitem(integration_apps.LOCAL_DISCOVERY_PATHS, "hermes", ())

    response = client.get("/api/v1/integrations/apps/hermes/discovery")
    discovery = response.json()

    assert response.status_code == 200
    assert discovery["repository_detected"] is False
    assert discovery["repository_path"] is None
    assert discovery["evidence_source"] == "versioned_local_discovery_snapshot"
    assert discovery["health_status"] == "local_evidence_snapshot_found"
    assert discovery["evidence_files_found"] == discovery["evidence_files_expected"]
    assert discovery["missing_evidence_files"] == []
    assert discovery["external_connection_enabled"] is False


def test_auditor_integration_profile_and_discovery_are_controlled() -> None:
    client = TestClient(app)

    profile_response = client.get("/api/v1/integrations/apps/auditor")
    discovery_response = client.get("/api/v1/integrations/apps/auditor/discovery")
    profile = profile_response.json()
    discovery = discovery_response.json()

    assert profile_response.status_code == 200
    assert profile["app_id"] == "auditor"
    assert profile["integration_status"] == "prepared_for_discovery"
    assert profile["external_connection_enabled"] is False
    assert profile["contract_id"] == "auditor.discovery.v1"

    assert discovery_response.status_code == 200
    assert discovery["app_id"] == "auditor"
    assert discovery["contract_id"] == "auditor.discovery.v1"
    assert discovery["evidence_source"] == "versioned_local_discovery_snapshot"
    assert discovery["health_status"] == "local_evidence_snapshot_found"
    assert discovery["missing_evidence_files"] == []
    assert discovery["external_connection_enabled"] is False
    assert "No standalone Auditor runtime repository was detected." in discovery["blockers"]


def test_pluma_integration_profile_and_discovery_are_controlled() -> None:
    client = TestClient(app)

    profile_response = client.get("/api/v1/integrations/apps/pluma")
    discovery_response = client.get("/api/v1/integrations/apps/pluma/discovery")
    profile = profile_response.json()
    discovery = discovery_response.json()

    assert profile_response.status_code == 200
    assert profile["app_id"] == "pluma"
    assert profile["integration_status"] == "prepared_for_discovery"
    assert profile["external_connection_enabled"] is False
    assert profile["contract_id"] == "pluma.discovery.v1"

    assert discovery_response.status_code == 200
    assert discovery["app_id"] == "pluma"
    assert discovery["contract_id"] == "pluma.discovery.v1"
    assert discovery["evidence_source"] in {
        "runtime_repository",
        "versioned_local_discovery_snapshot",
    }
    assert discovery["evidence_files_found"]
    assert discovery["external_connection_enabled"] is False
    assert "No Pluma runtime connection is enabled from ecosystem-foundation." in discovery["blockers"]


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
