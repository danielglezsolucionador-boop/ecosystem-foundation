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
    "arsenal",
    "auditor",
    "hermes",
}


def test_app_registry_lists_controlled_ecosystem_apps() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    payload = response.json()

    assert response.status_code == 200
    assert isinstance(payload, list)
    assert len(payload) == 14
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
        "role",
        "commercial_role",
        "controlled_state",
        "external_connection_enabled",
        "runtime_connected",
        "sunat_enabled",
        "requires_ceo_approval",
        "governance_execution_blocked",
        "secrets_required",
        "human_cabin_complete",
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
        assert item["external_connection_enabled"] is False
        assert item["runtime_connected"] is False
        if item["id"] == "cerebro":
            assert item["governance_execution_blocked"] is False
        else:
            assert item["governance_execution_blocked"] is True


def test_external_apps_are_registry_only_not_connected() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    apps_by_id = {item["id"]: item for item in response.json()}

    for app_id in ("doctor_contable_financiero_tributario",):
        assert apps_by_id[app_id]["status"] == "external"
        assert apps_by_id[app_id]["touch_policy"] == "no_touch_external"
        assert apps_by_id[app_id]["controlled_state"] == "protected_no_touch"
        assert apps_by_id[app_id]["sunat_enabled"] is False
        assert apps_by_id[app_id]["requires_ceo_approval"] is True


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


def test_block_4_apps_are_prepared_without_runtime_connection() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    apps_by_id = {item["id"]: item for item in response.json()}

    assert apps_by_id["forja"]["status"] == "planned"
    assert (
        apps_by_id["forja"]["touch_policy"]
        == "integration_prepared_no_runtime_connection"
    )
    assert apps_by_id["cerebro"]["status"] == "internal"
    assert apps_by_id["cerebro"]["controlled_state"] == "operational_internal"
    assert apps_by_id["cerebro"]["touch_policy"] == "internal_operational_no_external_runtime"
    assert apps_by_id["cerebro"]["external_connection_enabled"] is False
    assert apps_by_id["cerebro"]["runtime_connected"] is False


def test_block_7_future_apps_are_registered_but_not_connected() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps")
    apps_by_id = {item["id"]: item for item in response.json()}

    controlled_apps = {
        "doctor_contable_financiero_tributario": "protected_no_touch",
        "centinela": "pending_review_protected",
        "arsenal": "planned_pending_integration",
    }
    for app_id, controlled_state in controlled_apps.items():
        app_item = apps_by_id[app_id]
        assert app_item["controlled_state"] == controlled_state
        assert app_item["external_connection_enabled"] is False
        assert app_item["runtime_connected"] is False
        assert app_item["requires_ceo_approval"] is True
        assert app_item["governance_execution_blocked"] is True

    assert apps_by_id["doctor_contable_financiero_tributario"]["sunat_enabled"] is False
    assert apps_by_id["doctor_contable_financiero_tributario"]["secrets_required"] is False
    assert apps_by_id["centinela"]["touch_policy"] == "pending_review_protected_no_runtime"
    assert apps_by_id["arsenal"]["touch_policy"] == "planned_pending_integration_no_runtime"
    assert apps_by_id["arsenal"]["secrets_required"] is False
    assert apps_by_id["arsenal"]["human_cabin_complete"] is False


def test_app_detail_returns_single_registered_app() -> None:
    client = TestClient(app)

    response = client.get("/api/v1/apps/forja")
    payload = response.json()

    assert response.status_code == 200
    expected = {
        "id": "forja",
        "name": "FORJA",
        "type": "ecosystem_orchestrator",
        "status": "planned",
        "depends_on": [],
        "description": (
            "Construction and execution cabin with local discovery evidence "
            "prepared for controlled integration."
        ),
        "touch_policy": "integration_prepared_no_runtime_connection",
    }
    for key, value in expected.items():
        assert payload[key] == value


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
        "total": 14,
        "by_status": {
            "planned": 12,
            "internal": 1,
            "external": 1,
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
            "arsenal",
            "auditor",
            "hermes",
        ],
        "source": "local_controlled_registry",
        "external_connections_enabled": False,
    }
