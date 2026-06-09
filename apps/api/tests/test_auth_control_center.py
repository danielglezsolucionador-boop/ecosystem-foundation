from datetime import datetime
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services.auth import bootstrap_initial_admin, create_user_for_tests, list_auth_audit_events


client = TestClient(app)


def parse_zulu(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


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


def test_login_remember_me_extends_session_and_allows_auth_me() -> None:
    email = "remember-auth-test@example.com"
    password = "ControlCenter-Remember-Test-123"
    create_user_for_tests(email=email, password=password, name="Remember Auth Test", role=ControlCenterRole.ceo)

    normal_login = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    remember_login = client.post("/api/v1/auth/login", json={"email": email, "password": password, "remember_me": True})

    assert normal_login.status_code == 200
    assert remember_login.status_code == 200

    normal_payload = normal_login.json()
    remember_payload = remember_login.json()
    normal_expiry = parse_zulu(normal_payload["expires_at"])
    remember_expiry = parse_zulu(remember_payload["expires_at"])

    assert remember_expiry > normal_expiry
    assert (remember_expiry - normal_expiry).days >= 20

    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {remember_payload['token']}"})
    assert me.status_code == 200
    assert me.json()["email"] == email

    audit = [
        event
        for event in list_auth_audit_events()
        if event.session_id == remember_payload["session"]["id"] and event.action == "auth.login"
    ]
    assert audit
    assert audit[0].metadata["remember_me"] is True
    assert audit[0].metadata["session_ttl_hours"] == 720


def test_logout_revokes_remembered_session() -> None:
    email = "remember-logout-test@example.com"
    password = "remember-logout-test-password"
    create_user_for_tests(email=email, password=password, name="Remember Logout Test", role=ControlCenterRole.ceo)
    login_response = client.post("/api/v1/auth/login", json={"email": email, "password": password, "remember_me": True})
    token = login_response.json()["token"]
    headers = {"Authorization": f"Bearer {token}"}

    logout_response = client.post("/api/v1/auth/logout", headers=headers)
    me_after_logout = client.get("/api/v1/auth/me", headers=headers)

    assert logout_response.status_code == 200
    assert me_after_logout.status_code == 401


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


def test_initial_admin_bootstrap_rotates_from_environment(monkeypatch) -> None:
    email = f"bootstrap-{uuid4()}@example.com"
    monkeypatch.setenv("CONTROL_CENTER_ADMIN_EMAIL", email)
    monkeypatch.setenv("CONTROL_CENTER_ADMIN_PASSWORD", "Initial-Control-Center-Password-123")
    monkeypatch.setenv("CONTROL_CENTER_ADMIN_NAME", "Initial CEO")

    created = bootstrap_initial_admin()
    first_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Initial-Control-Center-Password-123"},
    )

    monkeypatch.setenv("CONTROL_CENTER_ADMIN_PASSWORD", "Rotated-Control-Center-Password-456")
    monkeypatch.setenv("CONTROL_CENTER_ADMIN_NAME", "Rotated CEO")
    rotated = bootstrap_initial_admin()
    old_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Initial-Control-Center-Password-123"},
    )
    new_login = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "Rotated-Control-Center-Password-456"},
    )

    assert created is not None
    assert created.role == ControlCenterRole.ceo
    assert first_login.status_code == 200
    assert rotated is not None
    assert rotated.name == "Rotated CEO"
    assert old_login.status_code == 401
    assert new_login.status_code == 200
