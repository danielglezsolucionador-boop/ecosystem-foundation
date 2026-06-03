from fastapi.testclient import TestClient

from app.main import app

ALLOWED_STATUSES = {"planned", "internal", "external", "blocked", "unknown"}
EXPECTED_APP_IDS = {
    "forja",
    "cerebro",
    "centinela",
    "pluma",
    "lente",
    "buscador_de_tendencias",
    "comercio_autonomo",
    "marca_personal",
    "marketing",
    "web_factory",
    "doctor_contable_financiero_tributario",
    "auditor",
    "hermes",
}


def test_app_registry_lists_controlled_ecosystem_apps() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    payload = response.json()

    assert response.status_code == 200
    assert isinstance(payload, list)
    assert len(payload) == 13
    assert {item["id"] for item in payload} == EXPECTED_APP_IDS


def test_app_registry_payload_contract() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    payload = response.json()

    required_fields = {
        "id",
        "name",
        "type",
        "status",
        "depends_on",
        "description",
        "touch_policy",
    }

    for item in payload:
        assert set(item) == required_fields
        assert item["id"]
        assert item["name"]
        assert item["type"]
        assert item["status"] in ALLOWED_STATUSES
        assert isinstance(item["depends_on"], list)
        assert item["description"]
        assert item["touch_policy"]


def test_external_apps_are_registry_only_not_connected() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    apps_by_id = {item["id"]: item for item in response.json()}

    for app_id in ("forja", "cerebro", "doctor_contable_financiero_tributario"):
        assert apps_by_id[app_id]["status"] == "external"
        assert apps_by_id[app_id]["touch_policy"] == "no_touch_external"

