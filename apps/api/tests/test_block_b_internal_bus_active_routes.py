from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
AUDITOR_HEADERS = auth_headers(client, ControlCenterRole.auditor)


ALLOWED_ROUTES = [
    ("cerebro_to_forja_future", "forja", "task_prepared"),
    ("cerebro_to_hermes_future", "hermes", "automation_prepared"),
    ("cerebro_to_creador_de_apis_y_skills_future", "creador_de_apis_y_skills", "api_skill_spec_prepared"),
    ("cerebro_to_web_factory_future", "web_factory", "landing_brief_prepared"),
    ("cerebro_to_buscador_de_tendencias_future", "buscador_de_tendencias", "research_request_prepared"),
    ("cerebro_to_pluma_future", "pluma", "draft_request_prepared"),
    ("cerebro_to_lente_future", "lente", "visual_brief_prepared"),
    ("cerebro_to_marketing_future", "marketing", "campaign_brief_prepared"),
    ("cerebro_to_marca_personal_future", "marca_personal", "personal_brand_brief_prepared"),
    ("cerebro_to_auditoria_future", "auditor", "audit_review_created"),
    ("cerebro_to_nube_future", "nube", "cloud_review_prepared"),
    ("cerebro_to_sniff_amazon_future", "sniff_amazon", "amazon_opportunity_review_prepared"),
    ("cerebro_to_comercio_autonomo_future", "comercio_autonomo", "commerce_plan_prepared"),
]


@pytest.mark.parametrize(("route_id", "target", "expected_result"), ALLOWED_ROUTES)
def test_block_b_cerebro_dispatches_to_allowed_internal_departments(
    route_id: str,
    target: str,
    expected_result: str,
) -> None:
    response = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": route_id,
            "subject": f"block-b-{target}",
            "payload": {"topic": target, "request": "prepare_internal_work"},
        },
        headers=CEO_HEADERS,
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["route_id"] == route_id
    assert payload["status"] == "completed"
    assert payload["target_service"] == target
    assert payload["allowed"] is True
    assert payload["blocked"] is False
    assert payload["handler_result"]["result"] == expected_result
    assert payload["handler_result"]["external_connection_enabled"] is False
    assert payload["handler_result"]["runtime_connected"] is False
    assert payload["handler_result"]["local_agent_enabled"] is False
    assert payload["handler_result"]["sunat_enabled"] is False
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["event_id"]
    assert payload["audit_event_id"]


@pytest.mark.parametrize(
    ("route_id", "reason"),
    [
        ("cerebro_to_dcft_future", "dcft_protected_no_touch"),
        ("cerebro_to_sentinela_future", "sentinela_pending_review_protected"),
        ("cerebro_to_arsenal_future", "arsenal_planned_pending_integration"),
    ],
)
def test_block_b_protected_targets_remain_blocked(route_id: str, reason: str) -> None:
    response = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": route_id,
            "subject": "block-b-protected-attempt",
            "payload": {"attempt": "execute_protected_target"},
        },
        headers=CEO_HEADERS,
    )
    payload = response.json()["detail"]

    assert response.status_code == 403
    assert payload["error"] == "internal_route_blocked"
    assert payload["reason"] == reason
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False


def test_block_b_routes_endpoint_requires_auth_and_lists_internal_routes() -> None:
    missing_session = client.get("/api/v1/integration-bus/routes")
    authorized = client.get("/api/v1/integration-bus/routes", headers=CEO_HEADERS)
    routes = {route["route_id"]: route for route in authorized.json()}

    assert missing_session.status_code == 401
    assert authorized.status_code == 200
    assert routes["cerebro_to_pluma_future"]["allowed"] is True
    assert routes["cerebro_to_pluma_future"]["external_connection_enabled"] is False
    assert routes["cerebro_to_pluma_future"]["runtime_connected"] is False
    assert routes["cerebro_to_dcft_future"]["allowed"] is False
    assert routes["cerebro_to_dcft_future"]["status"] == "blocked"


def test_block_b_auditor_can_read_but_cannot_dispatch() -> None:
    read_response = client.get("/api/v1/integration-bus/routes", headers=AUDITOR_HEADERS)
    dispatch_response = client.post(
        "/api/v1/integration-bus/dispatch",
        json={
            "route_id": "cerebro_to_pluma_future",
            "subject": "auditor-must-not-dispatch",
            "payload": {"topic": "role-boundary"},
        },
        headers=AUDITOR_HEADERS,
    )

    assert read_response.status_code == 200
    assert dispatch_response.status_code == 403
    assert dispatch_response.json()["detail"]["error"] == "integration_bus_role_not_authorized"


def test_block_b_route_state_update_is_internal_and_audited() -> None:
    response = client.post(
        "/api/v1/integration-bus/routes/cerebro_to_pluma_future/state",
        json={
            "status": "prepared",
            "reason": "Block B state check without external execution.",
        },
        headers=CEO_HEADERS,
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["route_id"] == "cerebro_to_pluma_future"
    assert payload["status"] == "prepared"
    assert payload["audit_event_id"]
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False


def test_block_b_protected_route_state_cannot_be_unlocked() -> None:
    response = client.post(
        "/api/v1/integration-bus/routes/cerebro_to_dcft_future/state",
        json={
            "status": "completed",
            "reason": "must stay blocked",
        },
        headers=CEO_HEADERS,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "protected_internal_route_state_locked"
