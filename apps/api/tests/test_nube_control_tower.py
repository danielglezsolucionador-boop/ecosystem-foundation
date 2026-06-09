from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services.audit import list_audit_events
from app.services.nube import get_nube_evidence_for_auditoria
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
AUDITOR_HEADERS = auth_headers(client, ControlCenterRole.auditor)


def test_nube_endpoints_require_auth() -> None:
    endpoints = [
        ("GET", "/api/v1/nube/status"),
        ("GET", "/api/v1/nube/projects"),
        ("POST", "/api/v1/nube/projects"),
        ("GET", "/api/v1/nube/deployments"),
        ("POST", "/api/v1/nube/deployments"),
        ("GET", "/api/v1/nube/health-checks"),
        ("POST", "/api/v1/nube/health-checks"),
        ("GET", "/api/v1/nube/risks"),
        ("POST", "/api/v1/nube/risks"),
        ("GET", "/api/v1/nube/costs"),
        ("POST", "/api/v1/nube/costs"),
    ]

    for method, path in endpoints:
        response = client.request(method, path, json={})
        assert response.status_code == 401


def test_nube_status_exposes_known_cloud_state_without_runtime() -> None:
    response = client.get("/api/v1/nube/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "nube_internal_control_tower"
    assert payload["project_id"] == "ecosystem-foundation"
    assert payload["production_url"] == "https://ecosystem-foundation.vercel.app"
    assert payload["control_center_url"] == "https://ecosystem-foundation.vercel.app/control-center"
    assert payload["provider"] == "Vercel"
    assert payload["database"] == "PostgreSQL"
    assert payload["persistent"] is True
    assert payload["temporal"] is False
    assert payload["external_connection_enabled"] is False
    assert payload["deploy_automation_enabled"] is False
    assert payload["vercel_api_connected"] is False
    assert payload["local_nube_touched"] is False
    assert payload["local_nube_path"] == "not_touched"
    assert payload["cost_status"] == "unknown"
    assert payload["requires_manual_review"] is True
    assert "v1-ecosystem-company-cabin" in payload["tags"]
    assert "v1-cerebro-internal-bus" in payload["tags"]


def test_nube_registers_project_and_masks_variables_without_saving_secret_values() -> None:
    secret_like_value = "token=blockedvalue"
    rejected = client.post(
        "/api/v1/nube/projects",
        headers=CEO_HEADERS,
        json={
            "name": "Rejected secret project",
            "variables": [{"name": "PAYMENT_SECRET_KEY", "status": "required"}],
            "notes": secret_like_value,
        },
    )
    assert rejected.status_code == 400
    assert rejected.json()["detail"]["error"] == "nube_secret_value_rejected"

    response = client.post(
        "/api/v1/nube/projects",
        headers=CEO_HEADERS,
        json={
            "id": "masked-vars-project",
            "name": "Masked Vars Project",
            "provider": "Vercel",
            "variables": [
                {
                    "name": "PAYMENT_SECRET_KEY",
                    "status": "required",
                    "value": "SHOULD_NOT_BE_SAVED",
                }
            ],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["variables"][0]["name"] == "PAYMENT_SECRET_KEY"
    assert payload["variables"][0]["value"] == "***masked***"
    assert "SHOULD_NOT_BE_SAVED" not in response.text

    projects = client.get("/api/v1/nube/projects", headers=CEO_HEADERS)
    assert "SHOULD_NOT_BE_SAVED" not in projects.text


def test_nube_registers_deployment_health_risk_and_unknown_cost_without_real_deploy() -> None:
    deployment = client.post(
        "/api/v1/nube/deployments",
        headers=CEO_HEADERS,
        json={
            "project_id": "ecosystem-foundation",
            "environment": "production",
            "url": "https://ecosystem-foundation.vercel.app",
            "provider": "Vercel",
            "commit": "d51963a",
            "status": "registered_only",
        },
    )
    health = client.post(
        "/api/v1/nube/health-checks",
        headers=CEO_HEADERS,
        json={
            "project_id": "ecosystem-foundation",
            "url": "https://ecosystem-foundation.vercel.app/health",
            "status": "manual_pass",
            "status_code": 200,
        },
    )
    risk = client.post(
        "/api/v1/nube/risks",
        headers=CEO_HEADERS,
        json={
            "project_id": "ecosystem-foundation",
            "title": "Costos sin medicion real",
            "severity": "medium",
            "description": "No hay costos reales conectados; requiere revision manual.",
        },
    )
    cost = client.post(
        "/api/v1/nube/costs",
        headers=CEO_HEADERS,
        json={
            "project_id": "ecosystem-foundation",
            "provider": "Vercel",
            "cost_status": "unknown",
            "requires_manual_review": True,
        },
    )

    assert deployment.status_code == 201
    assert deployment.json()["deploy_executed_by_nube"] is False
    assert deployment.json()["external_connection_enabled"] is False
    assert health.status_code == 201
    assert health.json()["external_monitor_connected"] is False
    assert risk.status_code == 201
    assert cost.status_code == 201
    assert cost.json()["cost_status"] == "unknown"
    assert cost.json()["estimated_monthly"] is None


def test_cerebro_can_query_nube_without_external_runtime() -> None:
    response = client.post(
        "/api/v1/cerebro/tasks",
        headers=CEO_HEADERS,
        json={
            "title": "Consultar estado NUBE",
            "description": "CEREBRO solicita estado cloud interno para el CEO.",
            "destination": "nube",
            "priority": "p1",
        },
    )

    assert response.status_code == 201
    task = response.json()
    assert task["blocked"] is False
    assert task["route_dispatched"] is True
    assert task["handler_result"]["result"] == "cloud_review_prepared"
    assert task["handler_result"]["nube_status_result"] == "cloud_status_prepared"
    assert task["handler_result"]["external_connection_enabled"] is False
    assert task["handler_result"]["runtime_connected"] is False
    assert task["handler_result"]["nube_brief"]["project_id"] == "ecosystem-foundation"
    assert task["handler_result"]["nube_brief"]["vercel_api_connected"] is False


def test_auditoria_can_request_nube_evidence_and_no_secrets_are_exposed() -> None:
    status_response = client.get("/api/v1/nube/status", headers=AUDITOR_HEADERS)
    evidence = get_nube_evidence_for_auditoria("test_evidence_request")

    assert status_response.status_code == 200
    assert evidence.requested_by == "AUDITORIA"
    assert evidence.variables_masked is True
    assert evidence.secrets_exposed is False
    assert evidence.external_connection_enabled is False
    assert evidence.status.vercel_api_connected is False
    assert all(variable.value == "***masked***" for variable in evidence.status.variables)

    audit_events = list_audit_events()
    assert any(event.source == "nube.internal_control_tower" for event in audit_events)
    audit_dump = "\n".join(event.model_dump_json() for event in audit_events)
    assert "SHOULD_NOT_BE_SAVED" not in audit_dump
    assert "token=blockedvalue" not in audit_dump
