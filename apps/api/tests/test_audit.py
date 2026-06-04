from fastapi.testclient import TestClient
import pytest

from app.main import app


client = TestClient(app)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/audit",
        "/api/v1/audit/reports",
        "/api/v1/audit/security",
        "/api/v1/audit/configuration",
        "/api/v1/audit/integration",
        "/api/v1/audit/runtime",
        "/api/v1/audit/errors",
    ],
)
def test_audit_required_endpoints(path: str) -> None:
    response = client.get(path)

    assert response.status_code == 200


def test_audit_run_creates_passing_report() -> None:
    response = client.post("/api/v1/audit/run")
    payload = response.json()

    assert response.status_code == 201
    assert payload["id"]
    assert payload["status"] == "pass"
    assert payload["created_at"].endswith("Z")
    assert {
        "app_registry_loaded",
        "external_connections_disabled",
        "storage_connected",
        "memory_local_operational",
        "roles_external_touch_disabled",
        "security_foundation_ready",
        "internal_events_operational",
        "integration_bus_operational",
        "contracts_operational",
    }.issubset({check["id"] for check in payload["checks"]})
    assert all(check["status"] == "pass" for check in payload["checks"])


def test_audit_reports_generate_alias_creates_report() -> None:
    response = client.post("/api/v1/audit/reports/generate", json={"scope": "full"})
    payload = response.json()

    assert response.status_code == 201
    assert payload["status"] == "pass"


def test_audit_reports_list_includes_created_report() -> None:
    created = client.post("/api/v1/audit/run").json()
    response = client.get("/api/v1/audit/reports")
    reports = response.json()

    assert response.status_code == 200
    assert any(report["id"] == created["id"] for report in reports)


def test_audit_event_can_be_created_and_read() -> None:
    response = client.post(
        "/api/v1/audit/events",
        json={
            "category": "security",
            "severity": "high",
            "source": "test",
            "action": "access_denied",
            "status": "recorded",
            "detail": "Security audit event test.",
            "metadata": {"test": True},
        },
    )
    event = response.json()

    assert response.status_code == 201
    assert event["id"]
    assert event["category"] == "security"
    assert event["severity"] == "high"

    detail_response = client.get(f"/api/v1/audit/events/{event['id']}")

    assert detail_response.status_code == 200
    assert detail_response.json()["id"] == event["id"]


def test_audit_category_endpoints_filter_events() -> None:
    created = client.post(
        "/api/v1/audit/events",
        json={
            "category": "integration",
            "severity": "medium",
            "source": "test",
            "action": "dispatch",
            "status": "recorded",
            "detail": "Integration audit event test.",
        },
    ).json()

    response = client.get("/api/v1/audit/integration")
    events = response.json()

    assert response.status_code == 200
    assert any(event["id"] == created["id"] for event in events)


def test_audit_overview_reports_counts() -> None:
    client.post(
        "/api/v1/audit/events",
        json={
            "category": "error",
            "severity": "critical",
            "source": "test",
            "action": "error_seen",
            "status": "recorded",
            "detail": "Error audit event test.",
        },
    )
    response = client.get("/api/v1/audit")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "central_audit_operational"
    assert payload["events"] >= 1
    assert payload["severity_summary"]["critical"] >= 1
    assert payload["external_connections_enabled"] is False


def test_audit_missing_event_returns_404() -> None:
    response = client.get("/api/v1/audit/events/missing-event")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "audit_event_not_found",
            "event_id": "missing-event",
        }
    }


def test_audit_invalid_event_payload_returns_422() -> None:
    response = client.post(
        "/api/v1/audit/events",
        json={
            "category": "not-a-category",
            "severity": "high",
            "source": "",
            "action": "",
            "status": "",
            "detail": "",
        },
    )

    assert response.status_code == 422
