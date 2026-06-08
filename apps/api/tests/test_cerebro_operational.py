from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
AUDITOR_HEADERS = auth_headers(client, ControlCenterRole.auditor)
SERVICE_HEADERS = auth_headers(client, ControlCenterRole.service)


def test_cerebro_endpoints_require_auth() -> None:
    for path in [
        "/api/v1/cerebro/status",
        "/api/v1/cerebro/brief/morning",
        "/api/v1/cerebro/brief/evening",
        "/api/v1/cerebro/decisions",
        "/api/v1/cerebro/tasks",
    ]:
        response = client.get(path)
        assert response.status_code == 401

    create_response = client.post(
        "/api/v1/cerebro/tasks",
        json={
            "title": "No auth task",
            "description": "Should be rejected.",
            "destination": "FORJA",
        },
    )
    assert create_response.status_code == 401


def test_cerebro_status_and_briefs_are_operational_internal() -> None:
    status = client.get("/api/v1/cerebro/status", headers=CEO_HEADERS)
    morning = client.get("/api/v1/cerebro/brief/morning", headers=CEO_HEADERS)
    evening = client.get("/api/v1/cerebro/brief/evening", headers=CEO_HEADERS)

    assert status.status_code == 200
    assert status.json()["status"] == "cerebro_operational_internal"
    assert status.json()["external_connection_enabled"] is False
    assert status.json()["runtime_connected"] is False
    assert status.json()["sunat_enabled"] is False
    assert status.json()["local_agent_enabled"] is False
    assert "DCFT" in status.json()["protected_targets"]
    assert "ARSENAL" in status.json()["protected_targets"]
    assert morning.status_code == 200
    assert morning.json()["type"] == "morning"
    assert morning.json()["external_connection_enabled"] is False
    assert evening.status_code == 200
    assert evening.json()["type"] == "evening"
    assert evening.json()["runtime_connected"] is False


def test_ceo_can_create_cerebro_decision_and_audit_event() -> None:
    response = client.post(
        "/api/v1/cerebro/decisions",
        json={
            "title": "Priorizar cierre operativo",
            "description": "Preparar una decision CEO para priorizar el siguiente bloque.",
            "priority": "p1",
            "state": "waiting_ceo",
            "reason": "Requiere criterio CEO.",
        },
        headers=CEO_HEADERS,
    )
    payload = response.json()

    assert response.status_code == 201
    assert payload["state"] == "waiting_ceo"
    assert payload["requires_ceo_approval"] is True
    assert payload["actor_role"] == "ceo"
    assert payload["audit_event_id"]

    audit = client.get(f"/api/v1/audit/events/{payload['audit_event_id']}", headers=CEO_HEADERS)
    assert audit.status_code == 200
    assert audit.json()["source"] == "cerebro.operational_runtime"
    assert audit.json()["metadata"]["action"] == "create_decision"


def test_ceo_can_create_allowed_internal_task_without_external_route() -> None:
    response = client.post(
        "/api/v1/cerebro/tasks",
        json={
            "title": "Preparar alcance interno",
            "description": "FORJA recibe intencion interna sin Local Agent.",
            "destination": "FORJA",
            "priority": "p1",
        },
        headers=CEO_HEADERS,
    )
    payload = response.json()

    assert response.status_code == 201
    assert payload["destination"] == "forja"
    assert payload["destination_label"] == "FORJA"
    assert payload["state"] == "delegated"
    assert payload["blocked"] is False
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["route_dispatched"] is True
    assert payload["bus_route_id"] == "cerebro_to_forja_future"
    assert payload["bus_dispatch_id"]
    assert payload["handler_result"]["result"] == "task_prepared"
    assert payload["handler_result"]["external_connection_enabled"] is False
    assert payload["handler_result"]["runtime_connected"] is False


def test_cerebro_blocks_protected_destinations() -> None:
    for destination, normalized in [
        ("DCFT", "doctor_contable_financiero_tributario"),
        ("SENTINELA", "centinela"),
        ("ARSENAL", "arsenal"),
    ]:
        response = client.post(
            "/api/v1/cerebro/tasks",
            json={
                "title": f"Blocked task {destination}",
                "description": "This must not execute.",
                "destination": destination,
                "priority": "p0",
            },
            headers=CEO_HEADERS,
        )
        payload = response.json()

        assert response.status_code == 201
        assert payload["destination"] == normalized
        assert payload["state"] == "blocked"
        assert payload["blocked"] is True
        assert payload["requires_ceo_approval"] is True
        assert payload["external_connection_enabled"] is False
        assert payload["runtime_connected"] is False
        assert payload["route_dispatched"] is False


def test_cerebro_blocks_sunat_local_agent_and_unknown_destinations() -> None:
    for destination in ["SUNAT", "Local Agent", "proveedor externo"]:
        response = client.post(
            "/api/v1/cerebro/tasks",
            json={
                "title": f"Forbidden {destination}",
                "description": "This must stay blocked.",
                "destination": destination,
            },
            headers=CEO_HEADERS,
        )
        payload = response.json()

        assert response.status_code == 201
        assert payload["state"] == "blocked"
        assert payload["blocked"] is True
        assert payload["external_connection_enabled"] is False
        assert payload["runtime_connected"] is False


def test_cerebro_task_state_update_and_blocked_lock() -> None:
    allowed = client.post(
        "/api/v1/cerebro/tasks",
        json={
            "title": "Cerrar tarea interna",
            "description": "Task can be completed internally.",
            "destination": "PLUMA",
        },
        headers=CEO_HEADERS,
    ).json()
    updated = client.post(
        f"/api/v1/cerebro/tasks/{allowed['id']}/state",
        json={"state": "completed", "reason": "Tarea interna cerrada."},
        headers=CEO_HEADERS,
    )

    blocked = client.post(
        "/api/v1/cerebro/tasks",
        json={
            "title": "Blocked update attempt",
            "description": "Protected tasks stay blocked.",
            "destination": "DCFT",
        },
        headers=CEO_HEADERS,
    ).json()
    unlock_attempt = client.post(
        f"/api/v1/cerebro/tasks/{blocked['id']}/state",
        json={"state": "delegated", "reason": "Should not unlock."},
        headers=CEO_HEADERS,
    )

    assert updated.status_code == 200
    assert updated.json()["state"] == "completed"
    assert unlock_attempt.status_code == 400
    assert unlock_attempt.json()["detail"]["error"] == "blocked_task_state_locked"


def test_cerebro_roles_allow_audit_read_but_block_service_and_auditor_writes() -> None:
    auditor_read = client.get("/api/v1/cerebro/status", headers=AUDITOR_HEADERS)
    auditor_write = client.post(
        "/api/v1/cerebro/decisions",
        json={
            "title": "Auditor write attempt",
            "description": "Auditor cannot create decisions.",
        },
        headers=AUDITOR_HEADERS,
    )
    service_read = client.get("/api/v1/cerebro/status", headers=SERVICE_HEADERS)

    assert auditor_read.status_code == 200
    assert auditor_write.status_code == 403
    assert service_read.status_code == 403


def test_cerebro_does_not_create_real_bus_routes_or_external_claims() -> None:
    before = client.get("/api/v1/integration-bus/routes", headers=CEO_HEADERS).json()
    client.post(
        "/api/v1/cerebro/tasks",
        json={
            "title": "Internal marketing request",
            "description": "Marketing prepares local strategy only.",
            "destination": "MARKETING",
        },
        headers=CEO_HEADERS,
    )
    after = client.get("/api/v1/integration-bus/routes", headers=CEO_HEADERS).json()

    assert len(after) == len(before)
    assert all(route["external_connection_enabled"] is False for route in after)
