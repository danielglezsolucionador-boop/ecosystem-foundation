from fastapi.testclient import TestClient

from app.main import app
from auth_helpers import auth_headers


def test_platform_status_certifies_local_v1() -> None:
    client = TestClient(app)
    headers = auth_headers(client)

    client.post("/api/v1/audit/run", headers=headers)
    response = client.get("/api/v1/platform/status")
    payload = response.json()

    assert response.status_code == 200
    assert payload["status"] == "PLATFORM_V1_LOCAL_OPERATIONAL"
    assert payload["local_ready"] is True
    assert payload["external_apps_connected"] is False
    assert {phase["id"] for phase in payload["phases"]} == set("ABCDEFGHI")
    assert all(phase["status"] == "pass" for phase in payload["phases"])
