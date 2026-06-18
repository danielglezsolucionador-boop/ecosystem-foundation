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
        ("GET", "/api/v1/arsenal/broker/status"),
        ("POST", "/api/v1/arsenal/broker/complete"),
        ("GET", "/api/v1/arsenal/linkedin/status"),
        ("GET", "/api/v1/arsenal/linkedin/oauth/start"),
        ("POST", "/api/v1/arsenal/linkedin/posts"),
        ("GET", "/api/v1/arsenal/resources"),
        ("GET", "/api/v1/arsenal/resources/arsenal-toolbelt-sombra"),
        ("POST", "/api/v1/arsenal/resources"),
        (
            "POST",
            "/api/v1/arsenal/resources/arsenal-toolbelt-sombra/replace",
        ),
        (
            "POST",
            "/api/v1/arsenal/resources/arsenal-toolbelt-sombra/disable",
        ),
        ("GET", "/api/v1/arsenal/catalog"),
        ("POST", "/api/v1/arsenal/catalog"),
        ("GET", "/api/v1/arsenal/categories"),
        ("GET", "/api/v1/arsenal/risks"),
        ("POST", "/api/v1/arsenal/risks"),
        ("GET", "/api/v1/arsenal/readiness"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_api_broker_status_is_prepared_without_runtime_claims() -> None:
    response = client.get("/api/v1/arsenal/broker/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "integrated_prepared_pending_credentials"
    assert payload["execution_enabled"] is False
    assert payload["external_call_executed"] is False
    assert payload["runtime_connected"] is False
    assert payload["secrets_stored"] is False
    assert "PLUMA" in payload["permissions"]
    assert "posts" in payload["permissions"]["PLUMA"]


def test_api_broker_stays_disabled_even_if_enablement_is_requested(
    monkeypatch,
) -> None:
    from app.core.config import get_settings

    monkeypatch.setenv("ARSENAL_API_BROKER_ENABLED", "true")
    get_settings.cache_clear()
    response = client.get("/api/v1/arsenal/broker/status", headers=CEO_HEADERS)
    get_settings.cache_clear()

    assert response.status_code == 200
    assert response.json()["execution_enabled"] is False


def test_api_broker_validates_permissions_without_calling_provider() -> None:
    response = client.post(
        "/api/v1/arsenal/broker/complete",
        headers=CEO_HEADERS,
        json={
            "office": "PLUMA",
            "capability": "posts",
            "prompt": "Redacta un post interno seguro.",
            "metadata": {"source": "test"},
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["office"] == "PLUMA"
    assert payload["capability"] == "posts"
    assert payload["cost_usd"] == 0
    assert payload["external_call_executed"] is False
    assert payload["runtime_connected"] is False
    assert payload["secrets_stored"] is False


def test_api_broker_rejects_cross_office_capability() -> None:
    response = client.post(
        "/api/v1/arsenal/broker/complete",
        headers=CEO_HEADERS,
        json={
            "office": "PLUMA",
            "capability": "riesgo",
            "prompt": "Analiza riesgo.",
        },
    )

    assert response.status_code == 403
    assert response.json()["detail"]["error"] == "arsenal_broker_permission_denied"


def test_api_broker_rejects_secrets_in_metadata() -> None:
    response = client.post(
        "/api/v1/arsenal/broker/complete",
        headers=CEO_HEADERS,
        json={
            "office": "CENTINELA",
            "capability": "riesgo",
            "prompt": "Analiza riesgo.",
            "metadata": {"api_key": "sk-testsecretvalue"},
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "arsenal_secret_payload_rejected"


def test_linkedin_is_pending_credentials_and_cannot_publish(
    monkeypatch,
) -> None:
    from app.core.config import get_settings

    for name in [
        "LINKEDIN_CLIENT_ID",
        "LINKEDIN_CLIENT_SECRET",
        "LINKEDIN_REDIRECT_URI",
        "LINKEDIN_ACCESS_TOKEN",
        "LINKEDIN_PERSON_URN",
    ]:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("LINKEDIN_POSTING_ENABLED", "true")
    get_settings.cache_clear()

    status = client.get("/api/v1/arsenal/linkedin/status", headers=CEO_HEADERS)
    oauth = client.get(
        "/api/v1/arsenal/linkedin/oauth/start",
        headers=CEO_HEADERS,
    )
    post = client.post(
        "/api/v1/arsenal/linkedin/posts",
        headers=CEO_HEADERS,
        json={
            "content": "Borrador seguro para revisión CEO.",
            "publish_now": True,
        },
    )

    get_settings.cache_clear()

    assert status.status_code == 200
    status_payload = status.json()
    assert status_payload["status"] == "prepared_pending_credentials"
    assert status_payload["posting_requested"] is True
    assert status_payload["posting_enabled"] is False
    assert status_payload["publication_allowed"] is False
    assert "LINKEDIN_CLIENT_ID" in status_payload["pending_credentials"]
    assert oauth.status_code == 200
    assert oauth.json()["authorization_url"] is None
    assert oauth.json()["activation_required"] is True
    assert post.status_code == 200
    post_payload = post.json()
    assert post_payload["ok"] is False
    assert post_payload["status"] == "blocked_publication_disabled"
    assert post_payload["external_call_executed"] is False


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
