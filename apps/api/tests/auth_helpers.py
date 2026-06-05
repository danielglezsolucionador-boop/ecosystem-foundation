from fastapi.testclient import TestClient
from uuid import uuid4

from app.schemas.auth import ControlCenterRole
from app.services.auth import create_user_for_tests


def auth_headers(client: TestClient, role: ControlCenterRole = ControlCenterRole.ceo) -> dict[str, str]:
    email = f"{role.value.lower()}-{uuid4()}@example.com"
    password = "ControlCenter-Suite-Password-123"
    create_user_for_tests(email=email, password=password, name=f"{role.value} Suite", role=role)
    response = client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}
