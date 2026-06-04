from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def unique_title(prefix: str) -> str:
    return f"{prefix} {uuid4()}"


def create_decision() -> dict:
    response = client.post(
        "/api/v1/governance/decisions",
        json={
            "title": unique_title("Governance decision"),
            "description": "Decision created by the governance rupture suite.",
            "requested_by": "operator",
            "evidence": "local test evidence",
        },
    )

    assert response.status_code == 201
    return response.json()


def create_approval() -> dict:
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
    )

    assert response.status_code == 201
    return response.json()


def create_risk(severity: str = "high") -> dict:
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
        response = client.get(path)
        assert response.status_code == 200


def test_governance_auth_boundary_shapes_actions_by_role() -> None:
    ceo = client.get("/api/v1/governance/auth-boundary?role_id=ceo")
    auditor = client.get("/api/v1/governance/auth-boundary?role_id=auditor")
    service = client.get("/api/v1/governance/auth-boundary?role_id=service")

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
    )

    assert auditor_decision.status_code == 403
    assert auditor_decision.json()["detail"]["error"] == "role_not_authorized"
    assert service_risk.status_code == 403
    assert service_risk.json()["detail"]["reason"] == "service_role_has_no_human_ui_authority"


def test_protected_apps_are_blocked_by_default() -> None:
    response = client.get("/api/v1/governance/integration-gates")
    gates = {item["app_id"]: item for item in response.json()}

    assert response.status_code == 200
    assert gates["forja"]["state"] == "blocked"
    assert gates["cerebro"]["state"] == "blocked"
    assert gates["doctor_contable_financiero_tributario"]["state"] == "blocked"
    assert gates["forja"]["protected"] is True
    assert gates["cerebro"]["protected"] is True
    assert gates["doctor_contable_financiero_tributario"]["protected"] is True
    assert all(
        gate["state"] in {"not_ready", "pending_approval", "approved_for_discovery", "approved_for_connection", "blocked", "suspended"}
        for app_id, gate in gates.items()
        if app_id not in {"forja", "cerebro", "doctor_contable_financiero_tributario"}
    )


def test_decision_approval_requires_authorized_role() -> None:
    decision = create_decision()
    response = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/approve",
        json={"role_id": "operator"},
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "role_not_authorized"


def test_decision_reject_and_block_require_reason() -> None:
    decision = create_decision()

    reject_response = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/reject",
        json={"role_id": "ceo"},
    )
    block_response = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/block",
        json={"role_id": "ceo"},
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
    )
    missing_reason = client.post(
        f"/api/v1/governance/approvals/{approval['id']}/reject",
        json={"role_id": "ceo"},
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
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "evidence_required"


def test_protected_apps_cannot_be_connected() -> None:
    for app_id in ["forja", "cerebro", "dcft"]:
        response = client.post(
            f"/api/v1/governance/integration-gates/{app_id}/approve-connection",
            json={"role_id": "ceo", "evidence": "future connection evidence"},
        )
        assert response.status_code == 400
        assert response.json()["detail"]["error"] == "protected_app_connection_blocked"


def test_non_protected_gate_can_reach_approval_without_real_connection() -> None:
    discovery = client.post(
        "/api/v1/governance/integration-gates/pluma/approve-discovery",
        json={"role_id": "ceo", "evidence": "Discovery evidence"},
    )
    connection = client.post(
        "/api/v1/governance/integration-gates/pluma/approve-connection",
        json={"role_id": "ceo", "evidence": "Connection evidence"},
    )

    assert discovery.status_code == 200
    assert discovery.json()["state"] == "approved_for_discovery"
    assert connection.status_code == 200
    assert connection.json()["state"] == "approved_for_connection"
    assert connection.json()["state"] != "connected"


def test_risk_close_requires_evidence_and_critical_risk_is_reported() -> None:
    risk = create_risk("critical")
    close_response = client.post(
        f"/api/v1/governance/risks/{risk['id']}/close",
        json={"role_id": "ceo"},
    )
    report_response = client.get("/api/v1/governance/reports")
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
    )
    closure = client.post(
        f"/api/v1/governance/risks/{risk['id']}/close",
        json={"role_id": "ceo", "evidence": "Mitigation verified."},
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
    )
    missing_route = client.get("/api/v1/governance/not-real")

    assert invalid_payload.status_code == 422
    assert missing_route.status_code == 404
