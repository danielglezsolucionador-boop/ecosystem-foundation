from fastapi.testclient import TestClient
import pytest

from app.main import app
from auth_helpers import auth_headers


client = TestClient(app)
AUTH_HEADERS = auth_headers(client)


def test_control_center_root_contract() -> None:
    response = client.get("/api/v1/control-center", headers=AUTH_HEADERS)
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] in {"healthy", "degraded", "blocked"}
    assert payload["audit_event_id"]
    assert payload["overview"]["registry_source"] == "local_controlled_registry"
    assert payload["overview"]["external_connections_enabled"] is False
    assert payload["executive_view"]["headline"]
    assert payload["operational_view"]["external_connections_enabled"] is False
    assert len(payload["applications"]) == 13
    assert len(payload["services"]) >= 6
    assert len(payload["dependencies"]) >= 4


@pytest.mark.parametrize(
    "path",
    [
        "/api/v1/control-center/overview",
        "/api/v1/control-center/status",
        "/api/v1/control-center/apps",
        "/api/v1/control-center/services",
        "/api/v1/control-center/dependencies",
        "/api/v1/control-center/metrics",
        "/api/v1/control-center/alerts",
        "/api/v1/control-center/readiness",
    ],
)
def test_control_center_required_endpoints(path: str) -> None:
    response = client.get(path, headers=AUTH_HEADERS)

    assert response.status_code == 200


def test_control_center_apps_use_registry_without_external_connections() -> None:
    response = client.get("/api/v1/control-center/apps", headers=AUTH_HEADERS)
    apps = response.json()
    external_apps = [
        app for app in apps if app["registry_status"] == "external"
    ]

    assert response.status_code == 200
    assert external_apps
    assert all(app["status"] == "degraded" for app in external_apps)
    assert all(app["external_connection_enabled"] is False for app in apps)
    assert all(
        app["touch_policy"] == "no_touch_external" for app in external_apps
    )


def test_control_center_shows_block_2_apps_without_external_connections() -> None:
    response = client.get("/api/v1/control-center/apps", headers=AUTH_HEADERS)
    apps = {item["id"]: item for item in response.json()}

    assert response.status_code == 200
    for app_id in ("web_factory", "marketing", "marca_personal"):
        assert app_id in apps
        assert apps[app_id]["registry_status"] == "planned"
        assert apps[app_id]["external_connection_enabled"] is False
        assert (
            apps[app_id]["touch_policy"]
            == "integration_prepared_no_runtime_connection"
        )


def test_control_center_shows_block_3_apps_without_external_connections() -> None:
    response = client.get("/api/v1/control-center/apps", headers=AUTH_HEADERS)
    apps = {item["id"]: item for item in response.json()}

    assert response.status_code == 200
    for app_id in ("comercio_autonomo", "buscador_de_tendencias"):
        assert app_id in apps
        assert apps[app_id]["registry_status"] == "planned"
        assert apps[app_id]["external_connection_enabled"] is False
        assert (
            apps[app_id]["touch_policy"]
            == "integration_prepared_no_runtime_connection"
        )


def test_control_center_shows_block_4_apps_without_external_connections() -> None:
    response = client.get("/api/v1/control-center/apps", headers=AUTH_HEADERS)
    apps = {item["id"]: item for item in response.json()}

    assert response.status_code == 200
    for app_id in ("forja", "cerebro"):
        assert app_id in apps
        assert apps[app_id]["registry_status"] == "planned"
        assert apps[app_id]["external_connection_enabled"] is False
        assert (
            apps[app_id]["touch_policy"]
            == "integration_prepared_no_runtime_connection"
        )


def test_control_center_readiness_keeps_external_connections_blocked() -> None:
    response = client.get("/api/v1/control-center/readiness", headers=AUTH_HEADERS)
    payload = response.json()
    checks = {item["id"]: item for item in payload["checks"]}

    assert response.status_code == 200
    assert payload["status"] == "blocked"
    assert payload["ready_for_external_connections"] is False
    assert checks["app_registry_loaded"]["status"] == "healthy"
    assert checks["external_apps_isolated"]["status"] == "healthy"
    assert checks["contracts_required_before_external_connections"]["status"] == "blocked"


def test_control_center_metrics_and_alerts_are_structured() -> None:
    metrics_response = client.get("/api/v1/control-center/metrics", headers=AUTH_HEADERS)
    alerts_response = client.get("/api/v1/control-center/alerts", headers=AUTH_HEADERS)
    metrics = {item["id"]: item for item in metrics_response.json()}
    alerts = alerts_response.json()

    assert metrics_response.status_code == 200
    assert alerts_response.status_code == 200
    assert metrics["registered_apps"]["value"] == 13
    assert metrics["external_connections_enabled"]["value"] is False
    assert metrics["storage_backend"]["source"] == "database.initialize_database"
    assert all("severity" in alert for alert in alerts)
    assert any(alert["id"] == "external_apps_not_connected" for alert in alerts)


def test_control_center_status_consolidates_runtime_dependencies_and_services() -> None:
    response = client.get("/api/v1/control-center/status", headers=AUTH_HEADERS)
    payload = response.json()
    dependencies = {item["id"]: item for item in payload["dependencies"]}
    services = {item["id"]: item for item in payload["services"]}

    assert response.status_code == 200
    assert payload["runtime"]["external_connections_enabled"] is False
    assert payload["runtime"]["database_backend"] in {"sqlite", "postgresql"}
    assert dependencies["database"]["status"] == "healthy"
    assert dependencies["integration_contracts"]["status"] == "blocked"
    assert services["app_registry"]["status"] == "healthy"


def test_control_center_unknown_endpoint_returns_404() -> None:
    response = client.get("/api/v1/control-center/does-not-exist", headers=AUTH_HEADERS)

    assert response.status_code == 404
