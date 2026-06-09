from fastapi.testclient import TestClient
import pytest
from uuid import uuid4
import time

from app.main import app
from app.schemas.auth import ControlCenterRole
from app.schemas.governance import GovernanceDecisionCreate, GovernanceRole
from app.services.audit import list_audit_events
from app.services.governance import create_decision
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
OPERATOR_HEADERS = auth_headers(client, ControlCenterRole.operator)


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/v1/ceo/daily-center"),
        ("GET", "/api/v1/ceo/morning"),
        ("GET", "/api/v1/ceo/evening"),
        ("GET", "/api/v1/ceo/decisions"),
        ("POST", "/api/v1/ceo/decisions/not-real/approve"),
        ("POST", "/api/v1/ceo/decisions/not-real/reject"),
    ],
)
def test_ceo_endpoints_require_auth(method: str, path: str) -> None:
    response = client.request(method, path, json={})

    assert response.status_code == 401


def test_ceo_daily_center_consolidates_internal_sources() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ceo_daily_center_operational_internal"
    assert payload["mode"] in {"ok", "degraded"}
    assert isinstance(payload["warnings"], list)
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["sunat_enabled"] is False
    assert payload["local_agent_enabled"] is False
    assert payload["morning"]["type"] == "morning"
    assert payload["evening"]["type"] == "evening"
    assert "cerebro" in payload
    assert "bus" in payload
    assert "auditoria" in payload
    assert "nube" in payload
    assert payload["nube"]["vercel_api_connected"] is False
    assert payload["protected_apps"] == ["DCFT", "SENTINELA", "ARSENAL", "SUNAT", "Local Agent"]
    assert any(action["allowed"] is False for action in payload["actions"])


def test_ceo_daily_center_uses_safe_fallback_when_internal_source_fails(monkeypatch) -> None:
    from app.services import ceo as ceo_service

    def broken_nube_status():
        raise RuntimeError("nube source unavailable")

    def broken_auditoria_status():
        raise RuntimeError("auditoria source unavailable")

    monkeypatch.setattr(ceo_service, "get_nube_status", broken_nube_status)
    monkeypatch.setattr(ceo_service, "get_auditoria_status", broken_auditoria_status)

    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["degraded"] is True
    assert payload["mode"] == "degraded"
    assert "nube_status_fallback" in payload["warnings"]
    assert "auditoria_status_fallback" in payload["warnings"]
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["protected_apps"] == ["DCFT", "SENTINELA", "ARSENAL", "SUNAT", "Local Agent"]


def test_ceo_daily_center_timeout_fallback_does_not_hang(monkeypatch) -> None:
    from app.services import ceo as ceo_service

    def slow_nube_status():
        time.sleep(0.25)
        raise RuntimeError("late nube failure")

    monkeypatch.setattr(ceo_service, "INTERNAL_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(ceo_service, "get_nube_status", slow_nube_status)

    started = time.perf_counter()
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)
    elapsed = time.perf_counter() - started

    assert response.status_code == 200
    assert elapsed < 1.0
    payload = response.json()
    assert payload["degraded"] is True
    assert "nube_status_timeout_fallback" in payload["warnings"]


def test_ceo_morning_and_evening_views_respond() -> None:
    morning = client.get("/api/v1/ceo/morning", headers=CEO_HEADERS)
    evening = client.get("/api/v1/ceo/evening", headers=CEO_HEADERS)

    assert morning.status_code == 200
    assert evening.status_code == 200
    assert morning.json()["headline"] == "Centro Diario del CEO - Mañana"
    assert evening.json()["headline"] == "Centro Diario del CEO - Tarde"
    assert "CEO" in morning.json()["cerebro_recommendation"]
    assert "NUBE" in evening.json()["summary"]


def test_ceo_decision_can_be_approved_and_audited() -> None:
    decision = create_decision(
        GovernanceDecisionCreate(
            title=f"CEO daily approval {uuid4()}",
            description="Internal decision for CEO Daily Center approval.",
            requested_by=GovernanceRole.operator,
            evidence="Internal evidence.",
            metadata={"target_id": "marketing", "action": "prepare_internal_campaign"},
        )
    )

    response = client.post(
        f"/api/v1/ceo/decisions/{decision.id}/approve",
        headers=CEO_HEADERS,
        json={"evidence": "CEO reviewed internal evidence."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "approved"
    assert payload["approved_by"] == "ceo"
    assert any(
        event.source == "ceo.daily_center"
        and event.action == "approve_decision"
        and event.metadata.get("decision_id") == decision.id
        for event in list_audit_events()
    )


def test_ceo_decision_can_be_rejected_and_audited() -> None:
    decision = create_decision(
        GovernanceDecisionCreate(
            title=f"CEO daily rejection {uuid4()}",
            description="Internal decision for CEO Daily Center rejection.",
            requested_by=GovernanceRole.operator,
            evidence="Internal evidence.",
            metadata={"target_id": "pluma", "action": "prepare_internal_content"},
        )
    )

    response = client.post(
        f"/api/v1/ceo/decisions/{decision.id}/reject",
        headers=CEO_HEADERS,
        json={"reason": "CEO rejects this internal decision for now."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "rejected"
    assert payload["rejected_by"] == "ceo"
    assert any(
        event.source == "ceo.daily_center"
        and event.action == "reject_decision"
        and event.metadata.get("decision_id") == decision.id
        for event in list_audit_events()
    )


def test_non_ceo_cannot_approve_decision() -> None:
    decision = create_decision(
        GovernanceDecisionCreate(
            title=f"Operator denied approval {uuid4()}",
            description="Operator must not approve from CEO Daily Center.",
            requested_by=GovernanceRole.operator,
        )
    )

    response = client.post(
        f"/api/v1/ceo/decisions/{decision.id}/approve",
        headers=OPERATOR_HEADERS,
        json={"evidence": "operator attempt"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "role_not_authorized"


def test_prohibited_action_is_blocked_before_approval() -> None:
    decision = create_decision(
        GovernanceDecisionCreate(
            title=f"Prohibited protected activation {uuid4()}",
            description="This must remain blocked.",
            requested_by=GovernanceRole.operator,
            metadata={"target_id": "dcft", "action": "activate_dcft"},
        )
    )

    response = client.post(
        f"/api/v1/ceo/decisions/{decision.id}/approve",
        headers=CEO_HEADERS,
        json={"evidence": "CEO test evidence."},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "ceo_action_prohibited"
    assert response.json()["detail"]["reason"] == "protected_target:dcft"
    assert any(
        event.source == "ceo.daily_center"
        and event.action == "approve_decision"
        and event.status == "blocked"
        and event.metadata.get("decision_id") == decision.id
        for event in list_audit_events()
    )


def test_ceo_dashboard_copy_does_not_claim_false_integrations() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "Centro Diario del CEO" in html.text
    assert "ceo-daily-center-summary" in html.text
    assert "/api/v1/ceo/daily-center" in js.text
    assert "renderCeoDailyCenter" in js.text
    normalized = js.text.lower()
    false_claims = [
        "dcft real conectado",
        "sentinela real conectado",
        "arsenal real conectado",
        "sunat activo",
        "local agent activo",
        "deploy directo activo",
        "apis externas conectadas",
    ]
    for claim in false_claims:
        assert claim not in normalized
