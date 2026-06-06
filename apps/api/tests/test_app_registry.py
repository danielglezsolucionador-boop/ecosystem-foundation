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


def test_block_2_apps_are_prepared_without_runtime_connection() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    apps_by_id = {item["id"]: item for item in response.json()}

    for app_id in ("web_factory", "marketing", "marca_personal"):
        assert apps_by_id[app_id]["status"] == "planned"
        assert (
            apps_by_id[app_id]["touch_policy"]
            == "integration_prepared_no_runtime_connection"
        )


def test_block_3_apps_are_prepared_without_runtime_connection() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    apps_by_id = {item["id"]: item for item in response.json()}

    for app_id in ("comercio_autonomo", "buscador_de_tendencias"):
        assert apps_by_id[app_id]["status"] == "planned"
        assert (
            apps_by_id[app_id]["touch_policy"]
            == "integration_prepared_no_runtime_connection"
        )


def test_apps_outside_blocks_2_and_3_remain_registry_only() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    apps_by_id = {item["id"]: item for item in response.json()}

    for app_id in (
        "centinela",
    ):
        assert apps_by_id[app_id]["status"] == "planned"
        assert apps_by_id[app_id]["touch_policy"] == "registry_only"


def test_app_detail_returns_single_registered_app() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps/forja")
    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "id": "forja",
        "name": "FORJA",
        "type": "ecosystem_orchestrator",
        "status": "external",
        "depends_on": [],
        "description": (
            "Construction and execution cabin referenced by the ecosystem. "
            "Not connected by this API yet."
        ),
        "touch_policy": "no_touch_external",
    }


def test_app_detail_normalizes_app_id() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps/CEREBRO%20")
    payload = response.json()

    assert response.status_code == 200
    assert payload["id"] == "cerebro"
    assert payload["name"] == "CEREBRO"


def test_app_detail_returns_controlled_404_for_unknown_app() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps/nonexistent")

    assert response.status_code == 404
    assert response.json() == {
        "detail": {
            "error": "app_not_found",
            "app_id": "nonexistent",
        }
    }


def test_app_registry_status_summary() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps/status/summary")
    payload = response.json()

    assert response.status_code == 200
    assert payload == {
        "total": 13,
        "by_status": {
            "planned": 10,
            "internal": 0,
            "external": 3,
            "blocked": 0,
            "unknown": 0,
        },
        "app_ids": [
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
        ],
        "source": "local_controlled_registry",
        "external_connections_enabled": False,
    }
