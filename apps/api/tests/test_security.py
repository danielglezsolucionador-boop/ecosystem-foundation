from fastapi.testclient import TestClient
import pytest

from app.main import app


client = TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/security",
        "/api/v1/security/users",
        "/api/v1/security/roles",
        "/api/v1/security/permissions",
        "/api/v1/security/policies",
        "/api/v1/security/service-identities",
        "/api/v1/security/api-key-placeholders",
        "/api/v1/security/session-model",
        "/api/v1/security/audit",
    ],
)
def test_security_required_endpoints(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200


def test_security_overview_contract() -> None:
    response = client.get("/api/v1/security")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "security_foundation_ready"
    assert payload["external_connections_enabled"] is False
    assert payload["secrets_exposed"] is False
    assert {role["id"] for role in payload["roles"]} == {
        "ceo",
        "admin",
        "operator",
        "auditor",
        "service",
    }
    assert all(role["can_view_secrets"] is False for role in payload["roles"])
    assert all(
        item["secret_material_present"] is False
        for item in payload["service_identities"]
    )
    assert payload["session_model"]["status"] == "prepared_not_issuing"


def test_security_permissions_include_required_minimum() -> None:
    response = client.get("/api/v1/security/permissions")
    permissions = {item["id"] for item in response.json()}

    assert response.status_code == 200
    assert {
        "read:control_center",
        "write:control_center",
        "read:apps",
        "write:apps",
        "read:memory",
        "write:memory",
        "read:events",
        "write:events",
        "read:audit",
        "write:audit",
        "read:observability",
        "write:observability",
        "manage:system",
    }.issubset(permissions)


def test_validate_access_allows_and_audits_known_permission() -> None:
    response = client.post(
        "/api/v1/security/validate-access",
        json={
            "role_id": "ceo",
            "permission": "manage:system",
            "resource": "platform",
        },
    )
    payload = response.json()

    assert response.status_code == 201
    assert payload["allowed"] is True
    assert payload["reason"] == "permission_granted"
    assert payload["required_human_approval"] is True
    assert payload["audit_event_id"]

    audit_response = client.get("/api/v1/security/audit")
    audit_events = audit_response.json()

    assert audit_response.status_code == 200
    assert any(event["id"] == payload["audit_event_id"] for event in audit_events)


def test_validate_access_denies_external_app_touch() -> None:
    response = client.post(
        "/api/v1/security/validate-access",
        json={
            "role_id": "ceo",
            "permission": "write:apps",
            "resource": "forja",
        },
    )
    payload = response.json()

    assert response.status_code == 201
    assert payload["allowed"] is False
    assert payload["reason"] == "external_app_touch_blocked"
    assert payload["can_touch_external_apps"] is False
    assert payload["audit_event_id"]


def test_validate_access_denies_unknown_role_without_crashing() -> None:
    response = client.post(
        "/api/v1/security/validate-access",
        json={
            "role_id": "ghost",
            "permission": "read:apps",
            "resource": "platform",
        },
    )
    payload = response.json()

    assert response.status_code == 201
    assert payload["allowed"] is False
    assert payload["reason"] == "role_not_found"
    assert payload["audit_event_id"]


def test_security_role_detail_missing_returns_404() -> None:
    response = client.get("/api/v1/security/roles/ghost")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "role_not_found",
            "role_id": "ghost",
        }
    }


def test_validate_access_rejects_invalid_payload() -> None:
    response = client.post(
        "/api/v1/security/validate-access",
        json={"role_id": "", "permission": ""},
    )

    assert response.status_code == 422
