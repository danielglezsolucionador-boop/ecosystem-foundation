from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def blueprint_payload(**overrides):
    payload = {
        "name": f"Internal API blueprint {uuid4()}",
        "item_type": "api",
        "category": "apis_internas",
        "internal_use": "Capacidad interna preparada para CEREBRO.",
        "is_sellable": False,
        "cost_usd": 0,
        "requires_secret": False,
        "requires_external_api": False,
        "risk": "controlled",
        "monetization": "not_estimated",
        "owner": "CEREBRO",
    }
    payload.update(overrides)
    return payload


def test_arsenal_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/arsenal/status"),
        ("GET", "/api/v1/arsenal/catalog"),
        ("POST", "/api/v1/arsenal/catalog"),
        ("GET", "/api/v1/arsenal/categories"),
        ("GET", "/api/v1/arsenal/risks"),
        ("POST", "/api/v1/arsenal/risks"),
        ("GET", "/api/v1/arsenal/readiness"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_catalog_lists_and_categories_are_prepared() -> None:
    catalog = client.get("/api/v1/arsenal/catalog", headers=CEO_HEADERS)
    categories = client.get("/api/v1/arsenal/categories", headers=CEO_HEADERS)

    assert catalog.status_code == 200
    assert categories.status_code == 200
    category_ids = {item["id"] for item in categories.json()}
    assert "apis_internas" in category_ids
    assert "skills_vendibles" in category_ids
    assert "herramientas_contables_tributarias" in category_ids
    assert all(item["runtime_connected"] is False for item in categories.json())


def test_create_item_without_secret_stores_metadata_only() -> None:
    response = client.post(
        "/api/v1/arsenal/catalog",
        headers=CEO_HEADERS,
        json=blueprint_payload(metadata={"source": "test", "provider": "none"}),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "prepared"
    assert payload["requires_ceo_approval"] is False
    assert payload["secrets_stored"] is False
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["metadata"]["provider"] == "none"


def test_rejects_secret_payload_and_does_not_store_api_keys() -> None:
    response = client.post(
        "/api/v1/arsenal/catalog",
        headers=CEO_HEADERS,
        json=blueprint_payload(metadata={"api_key": "<redacted>"}),
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "arsenal_secret_payload_rejected"


def test_item_with_cost_requires_ceo_approval() -> None:
    response = client.post(
        "/api/v1/arsenal/catalog",
        headers=CEO_HEADERS,
        json=blueprint_payload(
            name=f"Paid connector blueprint {uuid4()}",
            category="conectores",
            cost_usd=25,
            requires_external_api=True,
        ),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["requires_ceo_approval"] is True
    assert payload["status"] == "needs_ceo_approval"
    assert payload["payment_connected"] is False


def test_item_without_cost_does_not_require_approval() -> None:
    response = client.post(
        "/api/v1/arsenal/catalog",
        headers=CEO_HEADERS,
        json=blueprint_payload(
            name=f"Free skill blueprint {uuid4()}",
            item_type="skill",
            category="skills_internas",
        ),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["requires_ceo_approval"] is False
    assert payload["status"] == "prepared"


def test_sellable_item_requires_auditoria() -> None:
    response = client.post(
        "/api/v1/arsenal/catalog",
        headers=CEO_HEADERS,
        json=blueprint_payload(
            name=f"Sellable skill blueprint {uuid4()}",
            item_type="skill",
            category="skills_vendibles",
            is_sellable=True,
            sellable_use="Skill empaquetable para venta futura.",
            monetization="Puede venderse despues de auditoria.",
        ),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["requires_auditoria"] is True
    assert payload["audit_status"] == "requires_auditoria"
    assert payload["status"] == "needs_audit"


def test_cerebro_can_create_prepared_item() -> None:
    response = client.post(
        "/api/v1/arsenal/catalog",
        headers=CEO_HEADERS,
        json=blueprint_payload(
            name=f"CEREBRO prepared capability {uuid4()}",
            owner="CEREBRO",
            internal_use="CEREBRO consulta esta capacidad como metadata preparada.",
        ),
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["owner"] == "CEREBRO"
    assert payload["technical_status"] == "blueprint_prepared"


def test_forja_can_receive_prepared_task_without_runtime() -> None:
    created = client.post(
        "/api/v1/arsenal/catalog",
        headers=CEO_HEADERS,
        json=blueprint_payload(name=f"FORJA ready blueprint {uuid4()}"),
    )
    item_id = created.json()["id"]

    response = client.post(
        f"/api/v1/arsenal/catalog/{item_id}/send-to-forja",
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "forja_task_prepared"
    assert payload["destination"] == "forja"
    assert payload["runtime_connected"] is False
    assert payload["external_connection_enabled"] is False


def test_revenue_os_can_evaluate_sellable_monetization() -> None:
    created = client.post(
        "/api/v1/arsenal/catalog",
        headers=CEO_HEADERS,
        json=blueprint_payload(
            name=f"Revenue API blueprint {uuid4()}",
            category="apis_vendibles",
            is_sellable=True,
            sellable_use="API vendible despues de auditoria.",
            monetization="Evaluar como oportunidad tecnica vendible.",
        ),
    )
    item_id = created.json()["id"]

    evaluated = client.post(
        f"/api/v1/arsenal/catalog/{item_id}/evaluate",
        headers=CEO_HEADERS,
        json={
            "risk": "controlled",
            "monetization": "Pipeline estimado para Revenue OS, sin venta real.",
            "expected_revenue_usd": 800,
            "probability_percent": 50,
            "evaluate_revenue_os": True,
        },
    )

    assert evaluated.status_code == 200
    payload = evaluated.json()
    assert payload["revenue_opportunity_id"]
    assert payload["runtime_connected"] is False
    assert payload["external_connection_enabled"] is False


def test_status_and_readiness_do_not_claim_external_api_connection() -> None:
    status = client.get("/api/v1/arsenal/status", headers=CEO_HEADERS)
    readiness = client.get("/api/v1/arsenal/readiness", headers=CEO_HEADERS)

    assert status.status_code == 200
    assert readiness.status_code == 200
    payload = status.json()
    assert payload["status"] == "arsenal_blueprint_governed_prepared"
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["payment_connected"] is False
    assert payload["secrets_stored"] is False
    assert readiness.json()["runtime_connected"] is False


def test_control_center_shows_arsenal_blueprint_without_false_runtime_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "ARSENAL / Capacidades" in html.text
    assert "/api/v1/arsenal/status" in js.text
    assert "renderArsenalBlueprint" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "arsenal runtime conectado",
        "arsenal real conectado",
        "apis externas conectadas",
        "secretos guardados",
        "proveedor con costo activo",
    ]:
        assert false_claim not in normalized
