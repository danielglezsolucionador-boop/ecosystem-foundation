from fastapi.testclient import TestClient

from app.main import app


def test_unknown_route_returns_404() -> None:
    client = TestClient(app)

    response = client.get("/does-not-exist")

    assert response.status_code == 404


def test_blank_app_id_returns_controlled_404() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps/%20%20")

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "app_not_found"


def test_memory_rejects_empty_payload() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/memory/entries", json={})

    assert response.status_code == 422


def test_memory_rejects_malformed_json() -> None:
    client = TestClient(app)

    response = client.post(
        "/api/v1/memory/entries",
        content="not-json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


def test_permission_check_unknown_role_returns_controlled_404() -> None:
    client = TestClient(app)

    response = client.get(
        "/api/v1/permissions/check",
        params={"role_id": "ghost", "permission": "memory:write"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == {
        "error": "role_not_found",
        "role_id": "ghost",
    }
