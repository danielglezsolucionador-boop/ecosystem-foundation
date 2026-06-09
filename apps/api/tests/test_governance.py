from uuid import uuid4

from fastapi.testclient import TestClient
import pytest

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
ADMIN_HEADERS = auth_headers(client, ControlCenterRole.admin)
OPERATOR_HEADERS = auth_headers(client, ControlCenterRole.operator)
AUDITOR_HEADERS = auth_headers(client, ControlCenterRole.auditor)
SERVICE_HEADERS = auth_headers(client, ControlCenterRole.service)


def unique_title(prefix: str) -> str:
    return f"{prefix} {uuid4()}"


def create_decision(headers: dict[str, str] = OPERATOR_HEADERS) -> dict:
    response = client.post(
        "/api/v1/governance/decisions",
        json={
            "title": unique_title("Governance decision"),
            "description": "Decision created by the governance rupture suite.",
            "requested_by": "operator",
            "evidence": "local test evidence",
        },
        headers=headers,
    )

    assert response.status_code == 201
    return response.json()


def create_approval(headers: dict[str, str] = OPERATOR_HEADERS) -> dict:
    response = client.post(
        "/api/v1/governance/approvals",
        json={
            "title": unique_title("Governance approval"),
            "description": "Approval created by the governance rupture suite.",
            "approval_type": "integration_discovery",
            "requested_by": "operator",
            "target_id": "pluma",
            "evidence": "local test evidence",
        },
        headers=headers,
    )

    assert response.status_code == 201
    return response.json()


def create_risk(severity: str = "high", headers: dict[str, str] = OPERATOR_HEADERS) -> dict:
    response = client.post(
        "/api/v1/governance/risks",
        json={
            "title": unique_title("Governance risk"),
            "description": "Risk created by the governance rupture suite.",
            "risk_type": "integration",
            "severity": severity,
            "owner": "operator",
            "evidence": "local test evidence",
        },
        headers=headers,
    )

    assert response.status_code == 201
    return response.json()


def test_governance_required_endpoints_exist() -> None:
    for path in [
        "/api/v1/governance",
        "/api/v1/governance/auth-boundary",
        "/api/v1/governance/decisions",
        "/api/v1/governance/approvals",
        "/api/v1/governance/approvals/pending",
        "/api/v1/governance/integration-gates",
        "/api/v1/governance/policies",
        "/api/v1/governance/risks",
        "/api/v1/governance/audit",
        "/api/v1/governance/reports",
        "/api/v1/security/roles",
        "/api/v1/security/permissions",
    ]:
        headers = CEO_HEADERS if path.startswith("/api/v1/governance") else None
        response = client.get(path, headers=headers)
        assert response.status_code == 200


def test_governance_auth_boundary_shapes_actions_by_role() -> None:
    ceo = client.get("/api/v1/governance/auth-boundary?role_id=auditor", headers=CEO_HEADERS)
    auditor = client.get("/api/v1/governance/auth-boundary?role_id=ceo", headers=AUDITOR_HEADERS)
    service = client.get("/api/v1/governance/auth-boundary?role_id=ceo", headers=SERVICE_HEADERS)

    assert ceo.status_code == 200
    assert auditor.status_code == 200
    assert service.status_code == 200

    ceo_actions = {item["id"]: item for item in ceo.json()["actions"]}
    auditor_actions = {item["id"]: item for item in auditor.json()["actions"]}
    service_actions = {item["id"]: item for item in service.json()["actions"]}

    assert "ceo" in ceo.json()["views_allowed"]
    assert ceo_actions["approve_decision"]["allowed"] is True
    assert ceo_actions["close_risk"]["allowed"] is True
    assert auditor_actions["approve_decision"]["allowed"] is False
    assert auditor_actions["create_risk"]["allowed"] is False
    assert ceo_actions["escalate_approval"]["allowed"] is True
    assert service_actions["create_decision"]["allowed"] is False
    assert service_actions["evaluate_policy"]["allowed"] is True
    assert service.json()["external_connections_enabled"] is False


def test_governance_create_actions_respect_auth_boundary() -> None:
    auditor_decision = client.post(
        "/api/v1/governance/decisions",
        json={
            "title": unique_title("Auditor decision attempt"),
            "description": "Auditor must not create governance decisions.",
            "requested_by": "auditor",
        },
        headers=AUDITOR_HEADERS,
    )
    service_risk = client.post(
        "/api/v1/governance/risks",
        json={
            "title": unique_title("Service risk attempt"),
            "description": "Service identity must not create human risks.",
            "risk_type": "operational",
            "severity": "medium",
            "owner": "service",
        },
        headers=SERVICE_HEADERS,
    )

    assert auditor_decision.status_code == 403
    assert auditor_decision.json()["detail"]["error"] == "role_not_authorized"
    assert service_risk.status_code == 403
    assert service_risk.json()["detail"]["reason"] == "service_role_has_no_human_ui_authority"


def test_dcft_remains_protected_while_block_4_apps_are_controlled() -> None:
    response = client.get("/api/v1/governance/integration-gates", headers=CEO_HEADERS)
    gates = {item["app_id"]: item for item in response.json()}

    assert response.status_code == 200
    assert gates["doctor_contable_financiero_tributario"]["state"] == "blocked"
    assert gates["doctor_contable_financiero_tributario"]["protected"] is True
    assert gates["centinela"]["state"] == "blocked"
    assert gates["centinela"]["protected"] is True
    assert gates["arsenal"]["state"] == "blocked"
    assert gates["arsenal"]["protected"] is False
    assert gates["forja"]["protected"] is False
    assert gates["cerebro"]["protected"] is False
    assert gates["forja"]["state"] != "blocked"
    assert gates["cerebro"]["state"] != "blocked"
    assert all(
        gate["state"] in {"not_ready", "pending_approval", "approved_for_discovery", "approved_for_connection", "blocked", "suspended"}
        for app_id, gate in gates.items()
        if app_id not in {"doctor_contable_financiero_tributario", "centinela"}
    )


def test_decision_approval_requires_authorized_role() -> None:
    decision = create_decision()
    response = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/approve",
        json={"role_id": "operator"},
        headers=OPERATOR_HEADERS,
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "role_not_authorized"


def test_decision_reject_and_block_require_reason() -> None:
    decision = create_decision()

    reject_response = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/reject",
        json={"role_id": "ceo"},
        headers=CEO_HEADERS,
    )
    block_response = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/block",
        json={"role_id": "ceo"},
        headers=CEO_HEADERS,
    )

    assert reject_response.status_code == 400
    assert reject_response.json()["detail"]["error"] == "reason_required"
    assert block_response.status_code == 400
    assert block_response.json()["detail"]["error"] == "reason_required"


def test_decision_can_be_approved_by_human_authority() -> None:
    decision = create_decision()
    response = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/approve",
        json={"role_id": "ceo", "evidence": "CEO approval evidence"},
        headers=CEO_HEADERS,
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "approved"
    assert payload["approved_by"] == "ceo"
    assert payload["audit_event_ids"]


def test_approval_transitions_require_role_and_reason() -> None:
    approval = create_approval()
    unauthorized = client.post(
        f"/api/v1/governance/approvals/{approval['id']}/approve",
        json={"role_id": "operator"},
        headers=OPERATOR_HEADERS,
    )
    missing_reason = client.post(
        f"/api/v1/governance/approvals/{approval['id']}/reject",
        json={"role_id": "ceo"},
        headers=CEO_HEADERS,
    )

    assert unauthorized.status_code == 403
    assert unauthorized.json()["detail"]["error"] == "role_not_authorized"
    assert missing_reason.status_code == 400
    assert missing_reason.json()["detail"]["error"] == "reason_required"


def test_approval_can_be_approved_by_ceo() -> None:
    approval = create_approval()
    response = client.post(
        f"/api/v1/governance/approvals/{approval['id']}/approve",
        json={"role_id": "ceo", "evidence": "Approval evidence"},
        headers=CEO_HEADERS,
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "approved"
    assert payload["approved_by"] == "ceo"


def test_approval_can_be_escalated_by_operator_with_reason() -> None:
    approval = create_approval()
    response = client.post(
        f"/api/v1/governance/approvals/{approval['id']}/escalate",
        json={"role_id": "operator", "reason": "Needs CEO context."},
        headers=OPERATOR_HEADERS,
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "escalated"
    assert payload["reason"] == "Needs CEO context."
    assert payload["metadata"]["escalated_by"] == "operator"


def test_integration_gate_approval_requires_evidence() -> None:
    response = client.post(
        "/api/v1/governance/integration-gates/pluma/approve-discovery",
        json={"role_id": "ceo"},
        headers=CEO_HEADERS,
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "evidence_required"


def test_protected_apps_cannot_be_discovered_or_connected() -> None:
    for app_id in ["dcft", "sentinela"]:
        discovery_response = client.post(
            f"/api/v1/governance/integration-gates/{app_id}/request-discovery",
            json={"role_id": "ceo", "evidence": "future discovery evidence"},
            headers=CEO_HEADERS,
        )
        response = client.post(
            f"/api/v1/governance/integration-gates/{app_id}/approve-connection",
            json={"role_id": "ceo", "evidence": "future connection evidence"},
            headers=CEO_HEADERS,
        )
        assert discovery_response.status_code == 400
        assert discovery_response.json()["detail"]["error"] == "protected_app_discovery_blocked"
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "protected_app_connection_blocked"


def test_arsenal_planned_gate_cannot_be_discovered_or_connected() -> None:
    discovery_response = client.post(
        "/api/v1/governance/integration-gates/arsenal/request-discovery",
        json={"role_id": "ceo", "evidence": "future discovery evidence"},
        headers=CEO_HEADERS,
    )
    response = client.post(
        "/api/v1/governance/integration-gates/arsenal/approve-connection",
        json={"role_id": "ceo", "evidence": "future connection evidence"},
        headers=CEO_HEADERS,
    )

    assert discovery_response.status_code == 400
    assert discovery_response.json()["detail"]["error"] == "planned_app_discovery_blocked"
    assert discovery_response.json()["detail"]["reason"] == "planned_pending_integration_no_runtime"
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "planned_app_connection_blocked"
    assert response.json()["detail"]["reason"] == "planned_pending_integration_no_runtime"


def test_non_protected_gate_can_reach_approval_without_real_connection() -> None:
    gates_response = client.get("/api/v1/governance/integration-gates", headers=CEO_HEADERS)
    gates = gates_response.json()
    approved_reviews = client.get("/api/v1/auditoria/reviews", headers=CEO_HEADERS).json()
    approved_refs = {
        item["reference"]
        for item in approved_reviews
        if item["status"] == "approved"
    }
    candidates = [
        gate["app_id"]
        for gate in gates
        if gate["protected"] is False
        and gate["app_id"] not in approved_refs
        and gate["state"] not in {"approved_for_connection", "blocked", "connected"}
    ]
    if not candidates:
        pytest.skip("No clean non-protected gate available in the persistent local database.")
    app_id = candidates[0]
    discovery = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/approve-discovery",
        json={"role_id": "ceo", "evidence": "Discovery evidence"},
        headers=CEO_HEADERS,
    )
    blocked_connection = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/approve-connection",
        json={"role_id": "ceo", "evidence": "Connection evidence"},
        headers=CEO_HEADERS,
    )
    review = client.post(
        "/api/v1/auditoria/reviews",
        json={
            "object_type": "department",
            "reference": app_id,
            "source": "governance-test",
            "priority": "p1",
            "criteria": ["security", "technical_readiness", "ceo_standard"],
        },
        headers=CEO_HEADERS,
    ).json()
    decision = client.post(
        f"/api/v1/auditoria/reviews/{review['id']}/decision",
        json={
            "decision": "approved",
            "auditor": "auditoria-test",
            "observations": ["Connection approval may stay future-only."],
        },
        headers=AUDITOR_HEADERS,
    )
    connection = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/approve-connection",
        json={"role_id": "ceo", "evidence": "Connection evidence"},
        headers=CEO_HEADERS,
    )

    assert discovery.status_code == 200
    assert discovery.json()["state"] == "approved_for_discovery"
    assert blocked_connection.status_code == 400
    assert blocked_connection.json()["detail"]["error"] == "auditoria_approval_required"
    assert decision.status_code == 200
    assert connection.status_code == 200
    assert connection.json()["state"] == "approved_for_connection"
    assert connection.json()["state"] != "connected"


def test_auditor_gate_can_request_and_approve_discovery_without_real_connection() -> None:
    gates_response = client.get("/api/v1/governance/integration-gates", headers=CEO_HEADERS)
    gates = {item["app_id"]: item for item in gates_response.json()}
    request = client.post(
        "/api/v1/governance/integration-gates/auditor/request-discovery",
        json={
            "role_id": "operator",
            "reason": "Auditor discovery follows Hermes production PASS.",
            "evidence": "Auditor discovery profile and contract are registered locally.",
        },
        headers=OPERATOR_HEADERS,
    )
    approval = client.post(
        "/api/v1/governance/integration-gates/auditor/approve-discovery",
        json={
            "role_id": "ceo",
            "evidence": "Auditor discovery evidence reviewed; runtime connection remains disabled.",
        },
        headers=CEO_HEADERS,
    )

    assert gates_response.status_code == 200
    assert gates["auditor"]["protected"] is False
    assert request.status_code == 200
    assert request.json()["state"] == "pending_approval"
    assert request.json()["approval_id"]
    assert approval.status_code == 200
    assert approval.json()["state"] == "approved_for_discovery"
    assert approval.json()["approved_by"] == "ceo"
    assert approval.json()["audit_event_ids"]


def test_pluma_gate_can_request_and_approve_discovery_without_real_connection() -> None:
    request = client.post(
        "/api/v1/governance/integration-gates/pluma/request-discovery",
        json={
            "role_id": "operator",
            "reason": "PLUMA follows Auditor local PASS.",
            "evidence": "PLUMA discovery profile and contract are registered locally.",
        },
        headers=OPERATOR_HEADERS,
    )
    approval = client.post(
        "/api/v1/governance/integration-gates/pluma/approve-discovery",
        json={
            "role_id": "ceo",
            "evidence": "PLUMA discovery evidence reviewed; runtime connection remains disabled.",
        },
        headers=CEO_HEADERS,
    )

    assert request.status_code == 200
    assert request.json()["state"] == "pending_approval"
    assert approval.status_code == 200
    assert approval.json()["state"] == "approved_for_discovery"
    assert approval.json()["approved_by"] == "ceo"


def test_lente_gate_can_request_and_approve_discovery_without_real_connection() -> None:
    request = client.post(
        "/api/v1/governance/integration-gates/lente/request-discovery",
        json={
            "role_id": "operator",
            "reason": "LENTE follows PLUMA local PASS.",
            "evidence": "LENTE discovery profile and contract are registered locally.",
        },
        headers=OPERATOR_HEADERS,
    )
    approval = client.post(
        "/api/v1/governance/integration-gates/lente/approve-discovery",
        json={
            "role_id": "ceo",
            "evidence": "LENTE discovery evidence reviewed; runtime connection remains disabled.",
        },
        headers=CEO_HEADERS,
    )

    assert request.status_code == 200
    assert request.json()["state"] == "pending_approval"
    assert approval.status_code == 200
    assert approval.json()["state"] == "approved_for_discovery"
    assert approval.json()["approved_by"] == "ceo"


@pytest.mark.parametrize(
    ("app_id", "label"),
    [
        ("web_factory", "WEB_FACTORY"),
        ("marketing", "MARKETING"),
        ("marca_personal", "MARCA_PERSONAL"),
    ],
)
def test_block_2_gates_can_request_and_approve_discovery_without_real_connection(
    app_id: str,
    label: str,
) -> None:
    gates_response = client.get("/api/v1/governance/integration-gates", headers=CEO_HEADERS)
    gates = {item["app_id"]: item for item in gates_response.json()}
    request = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/request-discovery",
        json={
            "role_id": "operator",
            "reason": f"{label} is part of block 2 prepared discovery.",
            "evidence": f"{label} discovery profile and contract are registered locally.",
        },
        headers=OPERATOR_HEADERS,
    )
    approval = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/approve-discovery",
        json={
            "role_id": "ceo",
            "evidence": f"{label} discovery evidence reviewed; runtime connection remains disabled.",
        },
        headers=CEO_HEADERS,
    )

    assert gates_response.status_code == 200
    assert gates[app_id]["protected"] is False
    assert request.status_code == 200
    assert request.json()["state"] == "pending_approval"
    assert request.json()["approval_id"]
    assert approval.status_code == 200
    assert approval.json()["state"] == "approved_for_discovery"
    assert approval.json()["approved_by"] == "ceo"
    assert approval.json()["state"] != "connected"


@pytest.mark.parametrize(
    ("app_id", "label"),
    [
        ("comercio_autonomo", "COMERCIO_AUTONOMO"),
        ("buscador_de_tendencias", "BUSCADOR_DE_TENDENCIAS"),
    ],
)
def test_block_3_gates_can_request_and_approve_discovery_without_real_connection(
    app_id: str,
    label: str,
) -> None:
    gates_response = client.get("/api/v1/governance/integration-gates", headers=CEO_HEADERS)
    gates = {item["app_id"]: item for item in gates_response.json()}
    request = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/request-discovery",
        json={
            "role_id": "operator",
            "reason": f"{label} is part of block 3 prepared discovery.",
            "evidence": f"{label} discovery profile and contract are registered locally.",
        },
        headers=OPERATOR_HEADERS,
    )
    approval = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/approve-discovery",
        json={
            "role_id": "ceo",
            "evidence": f"{label} discovery evidence reviewed; runtime connection remains disabled.",
        },
        headers=CEO_HEADERS,
    )

    assert gates_response.status_code == 200
    assert gates[app_id]["protected"] is False
    assert request.status_code == 200
    assert request.json()["state"] == "pending_approval"
    assert request.json()["approval_id"]
    assert approval.status_code == 200
    assert approval.json()["state"] == "approved_for_discovery"
    assert approval.json()["approved_by"] == "ceo"
    assert approval.json()["state"] != "connected"


@pytest.mark.parametrize(
    ("app_id", "label"),
    [
        ("forja", "FORJA"),
        ("cerebro", "CEREBRO"),
    ],
)
def test_block_4_gates_can_request_and_approve_discovery_without_real_connection(
    app_id: str,
    label: str,
) -> None:
    gates_response = client.get("/api/v1/governance/integration-gates", headers=CEO_HEADERS)
    gates = {item["app_id"]: item for item in gates_response.json()}
    request = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/request-discovery",
        json={
            "role_id": "operator",
            "reason": f"{label} is part of block 4 prepared discovery.",
            "evidence": f"{label} discovery profile and contract are registered locally.",
        },
        headers=OPERATOR_HEADERS,
    )
    approval = client.post(
        f"/api/v1/governance/integration-gates/{app_id}/approve-discovery",
        json={
            "role_id": "ceo",
            "evidence": f"{label} discovery evidence reviewed; runtime connection remains disabled.",
        },
        headers=CEO_HEADERS,
    )

    assert gates_response.status_code == 200
    assert gates[app_id]["protected"] is False
    assert request.status_code == 200
    assert request.json()["state"] == "pending_approval"
    assert request.json()["approval_id"]
    assert approval.status_code == 200
    assert approval.json()["state"] == "approved_for_discovery"
    assert approval.json()["approved_by"] == "ceo"
    assert approval.json()["state"] != "connected"


def test_risk_close_requires_evidence_and_critical_risk_is_reported() -> None:
    risk = create_risk("critical")
    close_response = client.post(
        f"/api/v1/governance/risks/{risk['id']}/close",
        json={"role_id": "ceo"},
        headers=CEO_HEADERS,
    )
    report_response = client.get("/api/v1/governance/reports", headers=CEO_HEADERS)
    critical_ids = {item["id"] for item in report_response.json()["critical_risks"]}

    assert close_response.status_code == 400
    assert close_response.json()["detail"]["error"] == "evidence_required"
    assert report_response.status_code == 200
    assert risk["id"] in critical_ids


def test_risk_mitigation_and_closure_are_audited() -> None:
    risk = create_risk("medium")
    mitigation = client.post(
        f"/api/v1/governance/risks/{risk['id']}/mitigate",
        json={"role_id": "operator", "mitigation": "Add explicit governance checks."},
        headers=OPERATOR_HEADERS,
    )
    closure = client.post(
        f"/api/v1/governance/risks/{risk['id']}/close",
        json={"role_id": "ceo", "evidence": "Mitigation verified."},
        headers=CEO_HEADERS,
    )

    assert mitigation.status_code == 200
    assert mitigation.json()["status"] == "mitigated"
    assert closure.status_code == 200
    assert closure.json()["status"] == "closed"
    assert closure.json()["closure_evidence"] == "Mitigation verified."


def test_policy_evaluation_blocks_service_human_decision() -> None:
    response = client.post(
        "/api/v1/governance/policies/evaluate",
        json={"role_id": "service", "action": "approve", "resource": "platform"},
        headers=SERVICE_HEADERS,
    )
    payload = response.json()

    assert response.status_code == 200
    assert payload["allowed"] is False
    assert payload["reason"] == "service_role_cannot_make_human_decisions"
    assert payload["audit_event_id"]


def test_governance_invalid_payload_and_unknown_endpoint_are_controlled() -> None:
    invalid_payload = client.post(
        "/api/v1/governance/decisions",
        json={"title": "", "description": ""},
        headers=CEO_HEADERS,
    )
    missing_route = client.get("/api/v1/governance/not-real", headers=CEO_HEADERS)

    assert invalid_payload.status_code == 422
    assert missing_route.status_code == 404
