from fastapi.testclient import TestClient

from app.main import app


def test_audit_run_creates_passing_report() -> None:
    client = TestClient(app)

    response = client.post("/api/v1/audit/run")
    payload = response.json()

    assert response.status_code == 201
    assert payload["id"]
    assert payload["status"] == "pass"
    assert payload["created_at"].endswith("Z")
    assert {check["id"] for check in payload["checks"]} == {
        "app_registry_loaded",
        "external_connections_disabled",
        "storage_connected",
        "memory_local_operational",
        "roles_external_touch_disabled",
    }
    assert all(check["status"] == "pass" for check in payload["checks"])


def test_audit_reports_list_includes_created_report() -> None:
    client = TestClient(app)

    created = client.post("/api/v1/audit/run").json()
    response = client.get("/api/v1/audit/reports")
    reports = response.json()

    assert response.status_code == 200
    assert any(report["id"] == created["id"] for report in reports)

