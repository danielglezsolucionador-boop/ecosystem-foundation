from fastapi.testclient import TestClient

from app.main import app


def test_permission_roles_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/permissions/roles")
    payload = response.json()

    assert response.status_code == 200
    assert {role["id"] for role in payload} == {"viewer", "operator", "admin"}
    assert all(role["can_touch_external_apps"] is False for role in payload)


def test_permission_role_detail() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/permissions/roles/admin")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == "admin"
    assert "memory:write" in payload["permissions"]
    assert payload["can_touch_external_apps"] is False


def test_permission_role_missing_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/permissions/roles/ghost")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "role_not_found",
            "role_id": "ghost",
        }
    }


def test_permission_check_allows_known_permission() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/permissions/check",
        params={"role_id": "admin", "permission": "memory:write"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "role_id": "admin",
        "permission": "memory:write",
        "allowed": True,
        "reason": "permission_granted",
    }


def test_permission_check_denies_unknown_permission() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/permissions/check",
        params={"role_id": "viewer", "permission": "memory:write"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["role_id"] == "viewer"
    assert payload["permission"] == "memory:write"
    assert payload["allowed"] is False
    assert payload["reason"] == "permission_not_in_role"

