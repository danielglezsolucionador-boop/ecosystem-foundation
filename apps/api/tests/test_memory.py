from fastapi.testclient import TestClient

from app.main import app


def test_memory_status_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/memory/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "local_operational"
    assert payload["backend"] == "sqlite"
    assert isinstance(payload["entries"], int)
    assert payload["external_sources_connected"] is False


def test_memory_entry_can_be_created_and_listed() -> None:
    client = TestClient(app)

    create_response = client.post(
        "/api/v1/memory/entries",
        json={
            "title": "Autopilot validation memory",
            "content": "Memory entry created by local API test.",
            "source": "test",
            "tags": ["autopilot", "validation"],
        },
    )
    created = create_response.json()

    assert create_response.status_code == 201
    assert created["id"]
    assert created["title"] == "Autopilot validation memory"
    assert created["content"] == "Memory entry created by local API test."
    assert created["source"] == "test"
    assert created["tags"] == ["autopilot", "validation"]
    assert created["created_at"].endswith("Z")

    list_response = client.get("/api/v1/memory/entries")
    entries = list_response.json()

    assert list_response.status_code == 200
    assert any(entry["id"] == created["id"] for entry in entries)

