from fastapi.testclient import TestClient
import pytest

from app.main import app


client = TestClient(app)


BASE_SCHEMA = {
    "type": "object",
    "required": ["id", "status"],
    "properties": {
        "id": {"type": "string"},
        "status": {"type": "string"},
        "count": {"type": "integer"},
    },
}


def create_test_contract(name: str = "FORJA Status Contract") -> dict:
    response = client.post(
        "/api/v1/contracts",
        json={
            "app_id": "forja",
            "name": name,
            "version": "v1",
            "schema": BASE_SCHEMA,
            "status": "draft",
            "description": "Local contract test without external app connection.",
        },
    )

    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/contracts",
        "/api/v1/contracts/status",
        "/api/v1/contracts/audit",
    ],
)
def test_contracts_required_endpoints(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200


def test_contract_can_be_registered_for_app() -> None:
    contract = create_test_contract()

    assert contract["id"]
    assert contract["app_id"] == "forja"
    assert contract["schema"] == BASE_SCHEMA
    assert contract["breaking_change_detected"] is False
    assert contract["external_connection_enabled"] is False

    detail_response = client.get(f"/api/v1/contracts/{contract['id']}")

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == contract["id"]


def test_contract_registration_validates_app_id() -> None:
    response = client.post(
        "/api/v1/contracts",
        json={
            "app_id": "ghost-app",
            "name": "Ghost Contract",
            "schema": BASE_SCHEMA,
            "description": "Invalid app contract.",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "error": "app_not_registered",
        "app_id": "ghost-app",
    }


def test_contract_payload_validation_pass_and_fail() -> None:
    contract = create_test_contract("Payload Validation Contract")

    valid_response = client.post(
        f"/api/v1/contracts/{contract['id']}/validate",
        json={"payload": {"id": "abc", "status": "ok", "count": 1}},
    )
    invalid_response = client.post(
        f"/api/v1/contracts/{contract['id']}/validate",
        json={"payload": {"id": "abc", "count": "bad"}},
    )

    assert valid_response.status_code == 200
    assert valid_response.json()["valid"] is True
    assert valid_response.json()["errors"] == []
    assert invalid_response.status_code == 200
    assert invalid_response.json()["valid"] is False
    assert "missing_required_field:status" in invalid_response.json()["errors"]
    assert "invalid_type:count:integer" in invalid_response.json()["errors"]


def test_contract_compatibility_detects_breaking_change() -> None:
    contract = create_test_contract("Compatibility Contract")
    proposed_schema = {
        "type": "object",
        "required": ["id", "status", "new_required"],
        "properties": {
            "id": {"type": "string"},
            "status": {"type": "integer"},
            "new_required": {"type": "string"},
        },
    }

    response = client.post(
        f"/api/v1/contracts/{contract['id']}/compatibility-check",
        json={"proposed_schema": proposed_schema},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["compatible"] is False
    assert "added_required_field:new_required" in payload["breaking_changes"]
    assert "removed_property:count" in payload["breaking_changes"]
    assert "changed_type:status:string->integer" in payload["breaking_changes"]


def test_contract_update_versions_and_flags_breaking_change() -> None:
    contract = create_test_contract("Versioned Contract")
    proposed_schema = {
        "type": "object",
        "required": ["id", "status", "new_required"],
        "properties": {
            "id": {"type": "string"},
            "status": {"type": "string"},
            "count": {"type": "integer"},
            "new_required": {"type": "string"},
        },
    }

    update_response = client.put(
        f"/api/v1/contracts/{contract['id']}",
        json={
            "schema": proposed_schema,
            "version": "v2",
            "change_reason": "breaking_test",
        },
    )
    updated = update_response.json()

    assert update_response.status_code == 200
    assert updated["version"] == "v2"
    assert updated["breaking_change_detected"] is True

    versions_response = client.get(f"/api/v1/contracts/{contract['id']}/versions")
    versions = versions_response.json()

    assert versions_response.status_code == 200
    assert [version["sequence"] for version in versions] == [2, 1]
    assert versions[0]["action"] == "breaking_test"
    assert versions[1]["action"] == "create"


def test_contracts_can_be_filtered_by_app() -> None:
    contract = create_test_contract("Filtered Contract")
    response = client.get("/api/v1/contracts", params={"app_id": "forja"})
    contracts = response.json()

    assert response.status_code == 200
    assert any(item["id"] == contract["id"] for item in contracts)


def test_hermes_contract_is_seeded_without_external_connection() -> None:
    response = client.get("/api/v1/contracts", params={"app_id": "hermes"})
    contracts = response.json()

    assert response.status_code == 200
    assert any(item["id"] == "hermes.discovery.v1" for item in contracts)
    hermes_contract = next(
        item for item in contracts if item["id"] == "hermes.discovery.v1"
    )
    assert hermes_contract["status"] == "prepared_for_discovery"
    assert hermes_contract["external_connection_enabled"] is False


def test_auditor_contract_is_seeded_without_external_connection() -> None:
    response = client.get("/api/v1/contracts", params={"app_id": "auditor"})
    contracts = response.json()

    assert response.status_code == 200
    assert any(item["id"] == "auditor.discovery.v1" for item in contracts)
    auditor_contract = next(
        item for item in contracts if item["id"] == "auditor.discovery.v1"
    )
    assert auditor_contract["status"] == "prepared_for_discovery"
    assert auditor_contract["external_connection_enabled"] is False


def test_contract_audit_records_actions() -> None:
    contract = create_test_contract("Audit Contract")
    client.post(
        f"/api/v1/contracts/{contract['id']}/validate",
        json={"payload": {"id": "abc", "status": "ok"}},
    )
    response = client.get("/api/v1/contracts/audit")
    audit_events = response.json()

    assert response.status_code == 200
    assert any(
        event["contract_id"] == contract["id"]
        and event["action"] == "validate_payload"
        for event in audit_events
    )


def test_contract_missing_returns_404() -> None:
    response = client.get("/api/v1/contracts/missing-contract")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "contract_not_found",
            "contract_id": "missing-contract",
        }
    }


def test_contract_invalid_payload_returns_422() -> None:
    response = client.post(
        "/api/v1/contracts",
        json={
            "app_id": "",
            "name": "",
            "schema": {},
            "description": "",
        },
    )

    assert response.status_code == 422
