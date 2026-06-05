from fastapi.testclient import TestClient
import pytest

from app.main import app


client = TestClient(app)


def publish_test_event(subject: str = "test-memory") -> dict:
    response = client.post(
        "/api/v1/events",
        json={
            "type": "platform.memory.created",
            "source": "test",
            "subject": subject,
            "payload": {"memory_id": "memory-test-id"},
            "metadata": {"test": True},
        },
    )

    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/events",
        "/api/v1/events/status",
        "/api/v1/events/catalog",
        "/api/v1/events/consumers",
        "/api/v1/events/audit",
        "/api/v1/events/dead-letter",
    ],
)
def test_events_required_endpoints(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200


def test_event_can_be_published_and_read() -> None:
    event = publish_test_event()

    assert event["id"]
    assert event["type"] == "platform.memory.created"
    assert event["status"] == "published"
    assert event["external_queue_connected"] is False

    detail_response = client.get(f"/api/v1/events/{event['id']}")
    detail = detail_response.json()

    assert detail_response.status_code == 200
    assert detail["id"] == event["id"]


def test_event_payload_validation_rejects_missing_required_field() -> None:
    response = client.post(
        "/api/v1/events",
        json={
            "type": "platform.memory.updated",
            "source": "test",
            "subject": "invalid-memory-update",
            "payload": {"memory_id": "memory-test-id"},
        },
    )
    payload = response.json()

    assert response.status_code == 400
    assert payload["detail"]["error"] == "event_payload_missing_required_fields"
    assert payload["detail"]["missing_fields"] == ["version"]


def test_hermes_discovery_event_can_be_published() -> None:
    response = client.post(
        "/api/v1/events",
        json={
            "type": "platform.hermes.discovery.completed",
            "source": "integration-bus",
            "subject": "hermes-discovery",
            "payload": {
                "app_id": "hermes",
                "status": "prepared_for_discovery",
                "evidence_count": 8,
            },
        },
    )
    event = response.json()

    assert response.status_code == 201
    assert event["type"] == "platform.hermes.discovery.completed"
    assert event["external_queue_connected"] is False


def test_auditor_discovery_event_can_be_published() -> None:
    response = client.post(
        "/api/v1/events",
        json={
            "type": "platform.auditor.discovery.completed",
            "source": "integration-bus",
            "subject": "auditor-discovery",
            "payload": {
                "app_id": "auditor",
                "status": "prepared_for_discovery",
                "evidence_count": 8,
            },
        },
    )
    event = response.json()

    assert response.status_code == 201
    assert event["type"] == "platform.auditor.discovery.completed"
    assert event["external_queue_connected"] is False


def test_event_unknown_type_returns_controlled_error() -> None:
    response = client.post(
        "/api/v1/events",
        json={
            "type": "unknown.event",
            "source": "test",
            "subject": "unknown",
            "payload": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "error": "event_type_not_registered",
        "event_type": "unknown.event",
    }


def test_event_replay_creates_replayed_event_and_audit() -> None:
    event = publish_test_event("replay-memory")
    response = client.post(
        f"/api/v1/events/{event['id']}/replay",
        json={"reason": "test_replay"},
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["original_event_id"] == event["id"]
    assert payload["replayed_event"]["status"] == "replayed"
    assert payload["replayed_event"]["metadata"]["original_event_id"] == event["id"]
    assert payload["audit_event_id"]


def test_event_dead_letter_prepared() -> None:
    response = client.post(
        "/api/v1/events",
        json={
            "type": "platform.audit.completed",
            "source": "test",
            "subject": "dead-letter-test",
            "payload": {"audit_id": "audit-test", "status": "fail"},
            "route_to_dead_letter": True,
        },
    )
    event = response.json()

    assert response.status_code == 201
    assert event["status"] == "dead_letter"

    dead_letter_response = client.get("/api/v1/events/dead-letter")
    dead_letter_events = dead_letter_response.json()

    assert dead_letter_response.status_code == 200
    assert any(item["id"] == event["id"] for item in dead_letter_events)


def test_events_can_be_filtered() -> None:
    event = publish_test_event("filtered-memory")
    response = client.get(
        "/api/v1/events",
        params={
            "status": "published",
            "type": "platform.memory.created",
            "source": "test",
        },
    )
    events = response.json()

    assert response.status_code == 200
    assert any(item["id"] == event["id"] for item in events)


def test_event_missing_returns_404() -> None:
    response = client.get("/api/v1/events/missing-event")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "event_not_found",
            "event_id": "missing-event",
        }
    }


def test_event_replay_missing_returns_404() -> None:
    response = client.post("/api/v1/events/missing-event/replay")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "event_not_found",
            "event_id": "missing-event",
        }
    }


def test_event_invalid_payload_returns_422() -> None:
    response = client.post(
        "/api/v1/events",
        json={
            "type": "",
            "source": "",
            "subject": "",
        },
    )

    assert response.status_code == 422
