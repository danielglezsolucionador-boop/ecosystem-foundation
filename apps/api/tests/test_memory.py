from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def create_test_memory(title: str = "Autopilot validation memory") -> dict:
    response = client.post(
        "/api/v1/memory",
        json={
            "title": title,
            "content": "Memory entry created by local API test.",
            "type": "application",
            "status": "active",
            "source": "test",
            "app_id": "forja",
            "tags": ["autopilot", "validation"],
            "metadata": {"test": True},
        },
    )

    assert response.status_code == 201
    return response.json()


def test_memory_status_contract() -> None:
    response = client.get("/api/v1/memory/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "local_operational"
    assert payload["backend"] in {"sqlite", "postgresql"}
    assert isinstance(payload["entries"], int)
    assert isinstance(payload["versions"], int)
    assert isinstance(payload["audit_events"], int)
    assert "application" in payload["supported_types"]
    assert payload["external_sources_connected"] is False


def test_memory_entry_can_be_created_and_listed() -> None:
    created = create_test_memory()

    assert created["id"]
    assert created["title"] == "Autopilot validation memory"
    assert created["content"] == "Memory entry created by local API test."
    assert created["source"] == "test"
    assert created["type"] == "application"
    assert created["status"] == "active"
    assert created["app_id"] == "forja"
    assert created["tags"] == ["autopilot", "validation"]
    assert created["version"] == 1
    assert created["external_source_connected"] is False
    assert created["created_at"].endswith("Z")

    list_response = client.get("/api/v1/memory")
    entries = list_response.json()

    assert list_response.status_code == 200
    assert any(entry["id"] == created["id"] for entry in entries)


def test_memory_entries_alias_remains_compatible() -> None:
    created = create_test_memory("Alias validation memory")
    list_response = client.get("/api/v1/memory/entries")
    entries = list_response.json()

    assert list_response.status_code == 200
    assert any(entry["id"] == created["id"] for entry in entries)


def test_memory_detail_update_versions_and_audit() -> None:
    created = create_test_memory("Versioned memory")

    detail_response = client.get(f"/api/v1/memory/{created['id']}")
    assert detail_response.status_code == 200
    assert detail_response.json()["version"] == 1

    update_response = client.put(
        f"/api/v1/memory/{created['id']}",
        json={
            "content": "Updated memory content.",
            "status": "superseded",
            "change_reason": "test_update",
        },
    )
    updated = update_response.json()

    assert update_response.status_code == 200
    assert updated["version"] == 2
    assert updated["content"] == "Updated memory content."
    assert updated["status"] == "superseded"

    versions_response = client.get(f"/api/v1/memory/{created['id']}/versions")
    versions = versions_response.json()

    assert versions_response.status_code == 200
    assert [version["version"] for version in versions] == [2, 1]
    assert versions[0]["action"] == "test_update"
    assert versions[1]["action"] == "create"

    audit_response = client.get("/api/v1/memory/audit")
    audit_events = audit_response.json()

    assert audit_response.status_code == 200
    assert any(
        event["memory_id"] == created["id"] and event["action"] == "update"
        for event in audit_events
    )


def test_memory_search_by_app_type_and_status() -> None:
    created = create_test_memory("Searchable memory")

    app_response = client.get("/api/v1/memory/apps/forja")
    app_entries = app_response.json()

    assert app_response.status_code == 200
    assert any(entry["id"] == created["id"] for entry in app_entries)

    filtered_response = client.get(
        "/api/v1/memory",
        params={
            "app_id": "forja",
            "type": "application",
            "status": "active",
        },
    )
    filtered_entries = filtered_response.json()

    assert filtered_response.status_code == 200
    assert any(entry["id"] == created["id"] for entry in filtered_entries)


def test_memory_missing_entry_returns_404() -> None:
    response = client.get("/api/v1/memory/missing-memory")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "memory_not_found",
            "memory_id": "missing-memory",
        }
    }


def test_memory_invalid_payload_returns_422() -> None:
    response = client.post(
        "/api/v1/memory",
        json={
            "title": "",
            "content": "",
            "type": "not-a-type",
        },
    )

    assert response.status_code == 422
