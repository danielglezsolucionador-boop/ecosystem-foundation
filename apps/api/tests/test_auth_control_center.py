from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services.auth import create_user_for_tests, list_auth_audit_events


client = TestClient(app)


def auth_headers(role: ControlCenterRole = ControlCenterRole.ceo) -> dict[str, str]:
    email = f"{role.value.lower()}-auth-test@example.com"
    password = "ControlCenter-Test-Password-123"
    create_user_for_tests(email=email, password=password, name=f"{role.value} Auth Test", role=role)
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    token = response.json()["token"]
    assert token.startswith("ccs_")
    return {"Authorization": f"Bearer {token}"}


def test_login_me_sessions_logout_and_revoke_flow() -> None:
    headers = auth_headers(ControlCenterRole.ceo)

    me = client.get("/api/v1/auth/me", headers=headers)
    sessions = client.get("/api/v1/auth/sessions", headers=headers)
    assert me.status_code == 200
    assert me.json()["role"] == "CEO"
    assert sessions.status_code == 200
    assert sessions.json()

    session_id = sessions.json()[0]["id"]
    revoke = client.post("/api/v1/auth/sessions/revoke", json={"session_id": session_id, "reason": "test"}, headers=headers)
    assert revoke.status_code == 200

    expired = client.get("/api/v1/auth/me", headers=headers)
    assert expired.status_code == 401


def test_invalid_login_and_missing_session_are_denied_and_audited() -> None:
    create_user_for_tests(
        email="invalid-auth-test@example.com",
        password="Correct-Password-123",
        name="Invalid Auth Test",
        role=ControlCenterRole.operator,
    )
    bad_login = client.post(
        "/api/v1/auth/login",
        json={"email": "invalid-auth-test@example.com", "password": "wrong"},
    )
    no_session = client.get("/api/v1/control-center")

    assert bad_login.status_code == 401
    assert no_session.status_code == 401
    audit_results = [event.result for event in list_auth_audit_events()]
    assert "denied_invalid_credentials" in audit_results
    assert "denied_missing_session" in audit_results


def test_role_limits_are_bound_to_real_session_user() -> None:
    operator_headers = auth_headers(ControlCenterRole.operator)
    ceo_headers = auth_headers(ControlCenterRole.ceo)

    denied = client.post(
        "/api/v1/governance/decisions",
        json={
            "title": "Operator cannot spoof CEO",
            "description": "Payload asks for CEO, session remains OPERATOR.",
            "requested_by": "ceo",
        },
        headers=operator_headers,
    )
    assert denied.status_code == 201
    decision = denied.json()
    assert decision["requested_by"] == "operator"

    approval_denied = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/approve",
        json={"role_id": "ceo", "evidence": "spoof attempt"},
        headers=operator_headers,
    )
    assert approval_denied.status_code == 403

    approval_allowed = client.post(
        f"/api/v1/governance/decisions/{decision['id']}/approve",
        json={"role_id": "operator", "evidence": "real CEO session approval"},
        headers=ceo_headers,
    )
    assert approval_allowed.status_code == 200
    assert approval_allowed.json()["approved_by"] == "ceo"

    audit = list_auth_audit_events()
    assert any(event.email == "operator-auth-test@example.com" and event.result == "allowed" for event in audit)
