from fastapi.testclient import TestClient
import pytest

from app.core.metadata import APP_NAME
from app.main import app
from auth_helpers import auth_headers


client = TestClient(app)
AUTH_HEADERS = auth_headers(client)


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/observability",
        "/api/v1/observability/status",
        "/api/v1/observability/metrics",
        "/api/v1/observability/logs",
        "/api/v1/observability/traces",
        "/api/v1/observability/health",
        "/api/v1/observability/errors",
        "/api/v1/observability/incidents",
        "/api/v1/observability/sla",
        "/api/v1/observability/slo",
    ],
)
def test_observability_required_endpoints(path: str) -> None:
    response = client.get(path, headers=AUTH_HEADERS)

    assert response.status_code == 200


def test_observability_status_contract() -> None:
    response = client.get("/api/v1/observability/status", headers=AUTH_HEADERS)
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "local_observable"
    assert payload["service"] == APP_NAME
    assert payload["environment"] == "local"
    assert len(payload["metrics"]) >= 8
    assert payload["external_monitor_connected"] is False


def test_observability_status_contains_core_metrics() -> None:
    response = client.get("/api/v1/observability/status", headers=AUTH_HEADERS)
    metrics = {item["id"]: item for item in response.json()["metrics"]}

    assert metrics["registered_apps"]["value"] == 14
    assert metrics["external_connections_enabled"]["value"] is False
    assert metrics["storage_backend"]["value"] in {"sqlite", "postgresql"}
    assert isinstance(metrics["memory_entries"]["value"], int)
    assert isinstance(metrics["audit_reports"]["value"], int)
    assert isinstance(metrics["internal_events"]["value"], int)
    assert isinstance(metrics["contracts"]["value"], int)
    assert isinstance(metrics["integration_routes"]["value"], int)


def test_observability_metric_can_be_recorded() -> None:
    response = client.post(
        "/api/v1/observability/metrics",
        json={
            "id": "test_metric",
            "value": 42,
            "status": "ok",
            "source": "test",
            "unit": "count",
            "request_id": "req-test",
            "trace_id": "trace-test",
        },
        headers=AUTH_HEADERS,
    )
    metric = response.json()

    assert response.status_code == 201
    assert metric["id"] == "test_metric"
    assert metric["value"] == 42
    assert metric["trace_id"] == "trace-test"

    list_response = client.get("/api/v1/observability/metrics", headers=AUTH_HEADERS)
    metrics = list_response.json()

    assert list_response.status_code == 200
    assert any(item["id"] == "test_metric" for item in metrics)


def test_observability_log_errors_and_trace_correlation() -> None:
    log_response = client.post(
        "/api/v1/observability/logs",
        json={
            "level": "error",
            "message": "Structured error log test.",
            "source": "test",
            "request_id": "req-observable",
            "trace_id": "trace-observable",
            "metadata": {"safe": True},
        },
        headers=AUTH_HEADERS,
    )
    trace_response = client.post(
        "/api/v1/observability/traces",
        json={
            "trace_id": "trace-observable",
            "span_id": "span-1",
            "operation": "test_operation",
            "duration_ms": 12,
            "metadata": {"safe": True},
        },
        headers=AUTH_HEADERS,
    )

    assert log_response.status_code == 201
    assert trace_response.status_code == 201

    errors_response = client.get("/api/v1/observability/errors", headers=AUTH_HEADERS)
    traces_response = client.get(
        "/api/v1/observability/traces",
        params={"trace_id": "trace-observable"},
        headers=AUTH_HEADERS,
    )

    assert errors_response.status_code == 200
    assert any(log["trace_id"] == "trace-observable" for log in errors_response.json())
    assert traces_response.status_code == 200
    assert any(trace["trace_id"] == "trace-observable" for trace in traces_response.json())


def test_observability_incident_can_be_recorded() -> None:
    response = client.post(
        "/api/v1/observability/incidents",
        json={
            "title": "Incident test",
            "severity": "medium",
            "status": "open",
            "description": "Incident registry test.",
            "source": "test",
            "trace_id": "trace-incident",
        },
        headers=AUTH_HEADERS,
    )
    incident = response.json()

    assert response.status_code == 201
    assert incident["id"]
    assert incident["severity"] == "medium"

    list_response = client.get("/api/v1/observability/incidents", headers=AUTH_HEADERS)
    incidents = list_response.json()

    assert list_response.status_code == 200
    assert any(item["id"] == incident["id"] for item in incidents)


def test_observability_health_sla_slo() -> None:
    health_response = client.get("/api/v1/observability/health", headers=AUTH_HEADERS)
    sla_response = client.get("/api/v1/observability/sla", headers=AUTH_HEADERS)
    slo_response = client.get("/api/v1/observability/slo", headers=AUTH_HEADERS)

    assert health_response.status_code == 200
    assert {item["id"] for item in health_response.json()} >= {
        "storage",
        "memory",
        "audit",
        "events",
        "integration_bus",
        "contracts",
    }
    assert sla_response.status_code == 200
    assert slo_response.status_code == 200
    assert sla_response.json()
    assert slo_response.json()


def test_observability_invalid_payload_returns_422() -> None:
    response = client.post(
        "/api/v1/observability/logs",
        json={
            "level": "",
            "message": "",
            "source": "",
        },
        headers=AUTH_HEADERS,
    )

    assert response.status_code == 422
