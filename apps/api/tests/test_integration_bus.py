from fastapi.testclient import TestClient
import pytest

from app.main import app


client = TestClient(app)


def create_test_route() -> dict:
    response = client.post(
        "/api/v1/integration-bus/routes",
        json={
            "source_service": "memory",
            "target_service": "events",
            "event_type": "platform.memory.created",
            "channel": "internal",
        },
    )

    assert response.status_code == 201
    return response.json()


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/integration-bus",
        "/api/v1/integration-bus/routes",
        "/api/v1/integration-bus/services",
        "/api/v1/integration-bus/dependencies",
        "/api/v1/integration-bus/audit",
        "/api/v1/integration-bus/status",
    ],
)
def test_integration_bus_required_endpoints(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200


def test_integration_bus_overview_contract() -> None:
    response = client.get("/api/v1/integration-bus")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "integration_bus_operational"
    assert payload["external_connections_enabled"] is False
    assert len(payload["services"]) >= 9
    assert any(service["id"] == "hermes" for service in payload["services"])
    assert all(
        service["external_connection_enabled"] is False
        for service in payload["services"]
    )
    assert payload["dependencies"]


def test_route_can_be_registered_and_audited() -> None:
    route = create_test_route()

    assert route["id"]
    assert route["source_service"] == "memory"
    assert route["target_service"] == "events"
    assert route["event_type"] == "platform.memory.created"
    assert route["status"] == "active"
    assert route["dead_letter_enabled"] is True
    assert route["external_connection_enabled"] is False

    audit_response = client.get("/api/v1/integration-bus/audit")
    audit_events = audit_response.json()

    assert audit_response.status_code == 200
    assert any(
        event["route_id"] == route["id"]
        and event["action"] == "route_registered"
        for event in audit_events
    )


def test_route_registration_validates_services() -> None:
    response = client.post(
        "/api/v1/integration-bus/routes",
        json={
            "source_service": "ghost",
            "target_service": "events",
            "event_type": "platform.memory.created",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "error": "source_service_not_found",
        "source_service": "ghost",
    }


def test_route_registration_validates_event_type() -> None:
    response = client.post(
        "/api/v1/integration-bus/routes",
        json={
            "source_service": "memory",
            "target_service": "events",
            "event_type": "unknown.event",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == {
        "error": "event_type_not_registered",
        "event_type": "unknown.event",
    }


def test_hermes_route_can_be_prepared_without_external_connection() -> None:
    response = client.post(
        "/api/v1/integration-bus/routes",
        json={
            "source_service": "integration-bus",
            "target_service": "hermes",
            "event_type": "platform.hermes.discovery.completed",
            "channel": "internal",
        },
    )
    route = response.json()

    assert response.status_code == 201
    assert route["target_service"] == "hermes"
    assert route["external_connection_enabled"] is False


def test_dispatch_publishes_internal_event() -> None:
    route = create_test_route()
    response = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": route["id"],
            "subject": "memory-created",
            "payload": {"memory_id": "memory-test-id"},
            "metadata": {"test": True},
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "dispatched"
    assert payload["event_id"]
    assert payload["dead_letter_routed"] is False
    assert payload["audit_event_id"]

    event_response = client.get(f"/api/v1/events/{payload['event_id']}")
    event = event_response.json()

    assert event_response.status_code == 200
    assert event["type"] == "platform.memory.created"
    assert event["metadata"]["integration_route_id"] == route["id"]


def test_dispatch_can_route_to_dead_letter() -> None:
    route = create_test_route()
    response = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": route["id"],
            "subject": "dead-letter",
            "payload": {"memory_id": "memory-test-id"},
            "route_to_dead_letter": True,
        },
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "dead_letter_routed"
    assert payload["dead_letter_routed"] is True


def test_dispatch_missing_route_returns_404() -> None:
    response = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": "missing-route",
            "subject": "missing",
            "payload": {"memory_id": "memory-test-id"},
        },
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "route_not_found",
            "route_id": "missing-route",
        }
    }


def test_dispatch_validates_payload_against_event_catalog() -> None:
    route = create_test_route()
    response = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": route["id"],
            "subject": "invalid-payload",
            "payload": {},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "event_payload_missing_required_fields"


def test_integration_bus_invalid_payload_returns_422() -> None:
    response = client.post(
        "/api/v1/integration-bus/routes",
        json={
            "source_service": "",
            "target_service": "",
            "event_type": "",
        },
    )

    assert response.status_code == 422
