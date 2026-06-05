from fastapi.testclient import TestClient
import pytest

from app.main import app
from auth_helpers import auth_headers


client = TestClient(app)
AUTH_HEADERS = auth_headers(client)


def headers_for(path: str) -> dict[str, str] | None:
    protected_prefixes = (
        "/api/v1/control-center",
        "/api/v1/audit",
        "/api/v1/observability",
    )
    return AUTH_HEADERS if path.startswith(protected_prefixes) else None


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/control-center/nope",
        "/api/v1/security/roles/nope",
        "/api/v1/memory/nope",
        "/api/v1/events/nope",
        "/api/v1/contracts/nope",
        "/api/v1/audit/events/nope",
    ],
)
def test_backbone_unknown_resources_return_controlled_404(path: str) -> None:
    response = client.get(path, headers=headers_for(path))

    assert response.status_code == 404
    assert "detail" in response.json()


@pytest.mark.parametrize(
    ("path", "payload"),
    [
        ("/api/v1/security/validate-access", {"role_id": "", "permission": ""}),
        ("/api/v1/memory", {"title": "", "content": "", "type": "bad"}),
        ("/api/v1/events", {"type": "", "source": "", "subject": ""}),
        ("/api/v1/integration-bus/routes", {"source_service": "", "target_service": ""}),
        ("/api/v1/contracts", {"app_id": "", "name": "", "description": ""}),
        ("/api/v1/audit/events", {"category": "bad", "source": "", "detail": ""}),
        ("/api/v1/observability/logs", {"level": "", "message": "", "source": ""}),
    ],
)
def test_backbone_invalid_payloads_return_422(path: str, payload: dict) -> None:
    response = client.post(path, json=payload, headers=headers_for(path))

    assert response.status_code == 422


def test_backbone_malformed_json_returns_422() -> None:
    response = client.post(
        "/api/v1/events",
        content="not-json",
        headers={"content-type": "application/json"},
    )

    assert response.status_code == 422


def test_backbone_external_app_touch_stays_blocked() -> None:
    response = client.post(
        "/api/v1/security/validate-access",
        json={
            "role_id": "ceo",
            "permission": "write:apps",
            "resource": "cerebro",
        },
    )
    payload = response.json()

    assert response.status_code == 201
    assert payload["allowed"] is False
    assert payload["reason"] == "external_app_touch_blocked"


def test_backbone_invalid_integration_dispatch_is_controlled() -> None:
    response = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": "not-real",
            "subject": "bad-dispatch",
            "payload": {},
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"]["error"] == "route_not_found"


def test_backbone_contract_breaking_change_detection_is_not_bypassed() -> None:
    create_response = client.post(
        "/api/v1/contracts",
        json={
            "app_id": "forja",
            "name": "Rupture Contract",
            "schema": {
                "type": "object",
                "required": ["id"],
                "properties": {"id": {"type": "string"}},
            },
            "description": "Rupture contract.",
        },
    )
    contract = create_response.json()
    check_response = client.post(
        f"/api/v1/contracts/{contract['id']}/compatibility-check",
        json={
            "proposed_schema": {
                "type": "object",
                "required": ["id", "new_required"],
                "properties": {
                    "id": {"type": "integer"},
                    "new_required": {"type": "string"},
                },
            }
        },
    )
    payload = check_response.json()

    assert create_response.status_code == 201
    assert check_response.status_code == 200
    assert payload["compatible"] is False
    assert "added_required_field:new_required" in payload["breaking_changes"]
    assert "changed_type:id:string->integer" in payload["breaking_changes"]


def test_backbone_mass_audit_and_logs_remain_queryable() -> None:
    for index in range(10):
        client.post(
            "/api/v1/audit/events",
            json={
                "category": "trace",
                "severity": "info",
                "source": "rupture",
                "action": f"mass_audit_{index}",
                "status": "recorded",
                "detail": "Mass audit rupture test.",
            },
            headers=AUTH_HEADERS,
        )
        client.post(
            "/api/v1/observability/logs",
            json={
                "level": "info",
                "message": f"Mass log {index}",
                "source": "rupture",
                "trace_id": "rupture-trace",
            },
            headers=AUTH_HEADERS,
        )

    audit_response = client.get("/api/v1/audit", headers=AUTH_HEADERS)
    logs_response = client.get("/api/v1/observability/logs", headers=AUTH_HEADERS)

    assert audit_response.status_code == 200
    assert audit_response.json()["events"] >= 10
    assert logs_response.status_code == 200
    assert len(logs_response.json()) >= 10


def test_backbone_runtime_readiness_remains_available() -> None:
    readiness = client.get("/readiness")
    runtime = client.get("/runtime/status")

    assert readiness.status_code == 200
    assert runtime.status_code == 200
    assert "database" in runtime.json()
