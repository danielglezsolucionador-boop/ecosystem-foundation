from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def apps_by_id() -> dict[str, dict]:
    response = client.get("/api/v1/apps")

    assert response.status_code == 200
    return {item["id"]: item for item in response.json()}


def gates_by_id() -> dict[str, dict]:
    response = client.get("/api/v1/governance/integration-gates", headers=CEO_HEADERS)

    assert response.status_code == 200
    return {item["app_id"]: item for item in response.json()}


def routes_by_id() -> dict[str, dict]:
    response = client.get("/api/v1/integration-bus/prepared-routes")

    assert response.status_code == 200
    return {item["id"]: item for item in response.json()}


def assert_prepared_route_blocked(route: dict, expected_status: str) -> None:
    assert route["status"] == expected_status
    assert route["requires_ceo_approval"] is True
    assert route["external_connection_enabled"] is False
    assert route["runtime_connected"] is False

    dispatch = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": route["id"],
            "subject": "block-10-rupture-attempt",
            "payload": {"target": route["target"], "attempt": "real_execution"},
        },
    )

    assert dispatch.status_code == 404
    assert dispatch.json()["detail"] == {
        "error": "route_not_found",
        "route_id": route["id"],
    }


def test_block_10_dcft_real_discovery_connection_and_route_are_blocked() -> None:
    apps = apps_by_id()
    gates = gates_by_id()
    routes = routes_by_id()
    dcft = apps["doctor_contable_financiero_tributario"]

    assert dcft["controlled_state"] == "protected_no_touch"
    assert dcft["external_connection_enabled"] is False
    assert dcft["runtime_connected"] is False
    assert dcft["sunat_enabled"] is False
    assert dcft["requires_ceo_approval"] is True
    assert dcft["governance_execution_blocked"] is True
    assert gates["doctor_contable_financiero_tributario"]["state"] == "blocked"
    assert gates["doctor_contable_financiero_tributario"]["protected"] is True

    discovery = client.post(
        "/api/v1/governance/integration-gates/dcft/request-discovery",
        json={"role_id": "ceo", "reason": "block 10 rupture attempt"},
        headers=CEO_HEADERS,
    )
    connection = client.post(
        "/api/v1/governance/integration-gates/dcft/approve-connection",
        json={"role_id": "ceo", "evidence": "block 10 rupture attempt"},
        headers=CEO_HEADERS,
    )

    assert discovery.status_code == 400
    assert discovery.json()["detail"]["error"] == "protected_app_discovery_blocked"
    assert connection.status_code == 400
    assert connection.json()["detail"]["error"] == "protected_app_connection_blocked"
    assert_prepared_route_blocked(routes["cerebro_to_dcft_future"], "protected_no_touch_blocked")


def test_block_10_sentinela_activation_connection_and_route_are_blocked() -> None:
    apps = apps_by_id()
    gates = gates_by_id()
    routes = routes_by_id()
    sentinela = apps["centinela"]

    assert sentinela["controlled_state"] == "pending_review_protected"
    assert sentinela["external_connection_enabled"] is False
    assert sentinela["runtime_connected"] is False
    assert sentinela["requires_ceo_approval"] is True
    assert sentinela["governance_execution_blocked"] is True
    assert gates["centinela"]["state"] == "blocked"
    assert gates["centinela"]["protected"] is True

    discovery = client.post(
        "/api/v1/governance/integration-gates/sentinela/request-discovery",
        json={"role_id": "ceo", "reason": "block 10 rupture attempt"},
        headers=CEO_HEADERS,
    )
    connection = client.post(
        "/api/v1/governance/integration-gates/sentinela/approve-connection",
        json={"role_id": "ceo", "evidence": "block 10 rupture attempt"},
        headers=CEO_HEADERS,
    )

    assert discovery.status_code == 400
    assert discovery.json()["detail"]["error"] == "protected_app_discovery_blocked"
    assert connection.status_code == 400
    assert connection.json()["detail"]["error"] == "protected_app_connection_blocked"
    assert_prepared_route_blocked(routes["cerebro_to_sentinela_future"], "protected_blocked")


def test_block_10_arsenal_runtime_api_secret_and_route_are_blocked() -> None:
    apps = apps_by_id()
    gates = gates_by_id()
    routes = routes_by_id()
    arsenal = apps["arsenal"]

    assert arsenal["controlled_state"] == "planned_pending_integration"
    assert arsenal["touch_policy"] == "planned_pending_integration_no_runtime"
    assert arsenal["external_connection_enabled"] is False
    assert arsenal["runtime_connected"] is False
    assert arsenal["secrets_required"] is False
    assert arsenal["requires_ceo_approval"] is True
    assert arsenal["governance_execution_blocked"] is True
    assert gates["arsenal"]["state"] == "blocked"
    assert gates["arsenal"]["protected"] is False

    discovery = client.post(
        "/api/v1/governance/integration-gates/arsenal/request-discovery",
        json={"role_id": "ceo", "reason": "block 10 rupture attempt"},
        headers=CEO_HEADERS,
    )
    connection = client.post(
        "/api/v1/governance/integration-gates/arsenal/approve-connection",
        json={"role_id": "ceo", "evidence": "block 10 rupture attempt"},
        headers=CEO_HEADERS,
    )
    policy = client.post(
        "/api/v1/governance/policies/evaluate",
        json={"role_id": "ceo", "action": "connect_runtime", "resource": "arsenal"},
        headers=CEO_HEADERS,
    )

    assert discovery.status_code == 400
    assert discovery.json()["detail"]["error"] == "planned_app_discovery_blocked"
    assert connection.status_code == 400
    assert connection.json()["detail"]["error"] == "planned_app_connection_blocked"
    assert policy.status_code == 200
    assert policy.json()["allowed"] is False
    assert policy.json()["reason"] == "planned_app_connection_blocked"
    assert_prepared_route_blocked(routes["cerebro_to_arsenal_future"], "planned_blocked")


def test_block_10_all_prepared_bus_routes_are_blocked_and_need_ceo_approval() -> None:
    routes = routes_by_id()

    assert len(routes) == 16
    assert all(route["source"] == "cerebro" for route in routes.values())
    assert all(route["requires_ceo_approval"] is True for route in routes.values())
    assert all(route["external_connection_enabled"] is False for route in routes.values())
    assert all(route["runtime_connected"] is False for route in routes.values())
    assert all(route["status"].endswith("_blocked") for route in routes.values())

    for route_id in [
        "cerebro_to_dcft_future",
        "cerebro_to_sentinela_future",
        "cerebro_to_arsenal_future",
        "cerebro_to_forja_future",
        "cerebro_to_nube_future",
    ]:
        response = client.post(
            "/api/v1/integration-bus/dispatch",
            json={
                "route_id": route_id,
                "subject": "block-10-prepared-route-attempt",
                "payload": {"attempt": "real_bus_execution"},
            },
        )
        assert response.status_code == 404
        assert response.json()["detail"]["error"] == "route_not_found"


def test_block_10_cerebro_copy_stays_simulated_blocked_and_escalated_to_ceo() -> None:
    js_response = client.get("/control-center/assets/app.js")

    assert js_response.status_code == 200
    text = js_response.text
    normalized = text.lower()

    assert "departmentalSimulationFlows" in text
    assert "simulated_local" in text
    assert "no_runtime" in text
    assert "CEREBRO evalua" in text or "CEREBRO evalúa" in text
    assert "CEREBRO reporta al CEO" in text
    assert "CEO, esto requiere tu decision" in text or "CEO, esto requiere tu decisión" in text
    assert "DCFT protegido/no-touch: no integrado, no SUNAT real" in text
    assert "SENTINELA no productivo" in text
    assert "ARSENAL no runtime" in text
    assert "sin rutas reales activas" in text
    assert "sin Local Agent" in text

    forbidden_claims = [
        "dcft esta integrado",
        "sentinela esta activo en produccion",
        "forja real esta conectada",
        "nube esta conectada",
        "arsenal ya funciona como runtime",
        "hay rutas reales del bus",
        "hay apps externas conectadas",
        "se activo sunat",
        "local agent esta activo",
        "cerebro ejecuto codigo",
        "ejecutado real",
    ]
    for claim in forbidden_claims:
        assert claim not in normalized


def test_block_10_security_routes_require_valid_local_session() -> None:
    protected_paths = [
        "/api/v1/control-center",
        "/api/v1/governance",
        "/api/v1/governance/integration-gates",
        "/api/v1/audit/run",
    ]

    for path in protected_paths:
        method = client.post if path.endswith("/run") else client.get
        missing_session = method(path)
        invalid_token = method(path, headers={"Authorization": "Bearer invalid-token"})

        assert missing_session.status_code == 401
        assert invalid_token.status_code == 401
