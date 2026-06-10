from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services import revenue as revenue_service
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_revenue_sprint_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/revenue/sprint/status"),
        ("POST", "/api/v1/revenue/sprint/start"),
        ("GET", "/api/v1/revenue/sprint/routes"),
        ("POST", "/api/v1/revenue/sprint/routes"),
        ("GET", "/api/v1/revenue/sprint/missions"),
        ("POST", "/api/v1/revenue/sprint/missions"),
        ("GET", "/api/v1/revenue/sprint/daily"),
        ("GET", "/api/v1/revenue/sprint/risks"),
        ("GET", "/api/v1/revenue/sprint/approval-needed"),
        ("POST", "/api/v1/revenue/sprint/report"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_sprint_starts_without_real_revenue_or_paid_campaigns() -> None:
    response = client.post("/api/v1/revenue/sprint/start", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "revenue_execution_sprint_prepared_internal"
    assert payload["sprint_status"] == "running"
    assert payload["global_goal_usd"] == 6000
    assert payload["ecommerce_goal_usd"] == 10000
    assert payload["routes"] >= 10
    assert payload["missions"] >= 1
    assert payload["actual_revenue_usd"] == 0
    assert payload["actual_revenue_status"] == "no_real_revenue_reported"
    assert payload["paid_campaigns_launched"] == 0
    assert payload["payment_connected"] is False


def test_initial_routes_are_opportunities_and_missing_evidence_when_needed() -> None:
    response = client.get("/api/v1/revenue/sprint/routes", headers=CEO_HEADERS)

    assert response.status_code == 200
    routes = response.json()
    names = {route["name"] for route in routes}
    assert "DCFT vendido por Marketing" in names
    assert "E-COMMERCE separado" in names
    assert all(route["real_revenue_confirmed"] is False for route in routes)
    assert all(route["payment_connected"] is False for route in routes)
    assert any(route["evidence_status"] == "missing" for route in routes)


def test_create_route_does_not_invent_sales_and_defaults_missing_evidence() -> None:
    response = client.post(
        "/api/v1/revenue/sprint/routes",
        headers=CEO_HEADERS,
        json={
            "name": f"Producto digital tendencia {uuid4()}",
            "owner": "BUSCADOR DE TENDENCIAS",
            "hypothesis": "Puede convertirse en producto digital si aparece demanda real.",
            "next_actions": ["Validar senal", "Preparar brief"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["evidence_status"] == "missing"
    assert payload["potential_estimated_usd"] is None
    assert payload["real_revenue_confirmed"] is False
    assert payload["status"] == "needs_more_data"


def test_paid_campaign_route_requires_ceo_approval() -> None:
    response = client.post(
        "/api/v1/revenue/sprint/routes",
        headers=CEO_HEADERS,
        json={
            "name": f"Paid sprint route {uuid4()}",
            "owner": "MARKETING",
            "hypothesis": "Solo seria evaluable con ROI y aprobacion CEO.",
            "investment_required_usd": 100,
            "action_type": "paid_campaign",
            "potential_estimated_usd": 600,
            "evidence_available": ["hipotesis comercial"],
            "evidence_missing": ["ROI final", "aprobacion CEO"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["approval_required"] is True
    assert payload["status"] == "waiting_ceo_approval"
    assert payload["paid_campaign_launched"] is False


def test_organic_route_does_not_require_approval() -> None:
    response = client.post(
        "/api/v1/revenue/sprint/routes",
        headers=CEO_HEADERS,
        json={
            "name": f"Organic route {uuid4()}",
            "owner": "PLUMA",
            "hypothesis": "Validacion organica sin gasto.",
            "action_type": "organic_validation",
            "evidence_available": ["brief interno"],
            "evidence_missing": ["metricas organicas"],
        },
    )

    assert response.status_code == 201
    assert response.json()["approval_required"] is False


def test_ecommerce_route_is_separate() -> None:
    response = client.post(
        "/api/v1/revenue/sprint/routes",
        headers=CEO_HEADERS,
        json={
            "name": f"Ecommerce sprint {uuid4()}",
            "owner": "E-COMMERCE",
            "hypothesis": "Validar oportunidad sin comprar inventario.",
            "ecommerce_separate": True,
            "evidence_missing": ["margen", "producto", "proveedor"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["ecommerce_separate"] is True


def test_cerebro_creates_sprint_mission_without_payment_execution() -> None:
    route = client.post(
        "/api/v1/revenue/sprint/routes",
        headers=CEO_HEADERS,
        json={
            "name": f"Mission route {uuid4()}",
            "owner": "WEB FACTORY",
            "hypothesis": "Landing puede validar demanda sin checkout.",
            "evidence_available": ["oferta preliminar"],
            "evidence_missing": ["conversion organica"],
        },
    ).json()
    response = client.post(
        "/api/v1/revenue/sprint/missions",
        headers=CEO_HEADERS,
        json={
            "route_id": route["id"],
            "departments": ["WEB FACTORY", "MARKETING", "AUDITORIA"],
            "expected_output": "Landing preparada sin cobro real.",
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["route_id"] == route["id"]
    assert payload["mission_id"]
    assert payload["payment_connected"] is False
    assert payload["runtime_connected"] is False


def test_sprint_daily_risks_and_approval_needed_are_clear() -> None:
    daily = client.get("/api/v1/revenue/sprint/daily", headers=CEO_HEADERS)
    risks = client.get("/api/v1/revenue/sprint/risks", headers=CEO_HEADERS)
    approvals = client.get("/api/v1/revenue/sprint/approval-needed", headers=CEO_HEADERS)

    assert daily.status_code == 200
    assert risks.status_code == 200
    assert approvals.status_code == 200
    approval_payload = approvals.json()
    assert "ingresos reales: 0" in daily.json()["daily_tracking"]
    assert any("No inventar ventas" in risk["title"] for risk in risks.json())
    assert approval_payload["status"] == "ok"
    assert approval_payload["mode"] == "prepared"
    assert approval_payload["count"] == len(approval_payload["items"])
    assert approval_payload["requires_ceo_action"] == (approval_payload["count"] > 0)
    assert all(route["approval_required"] is True for route in approval_payload["items"])


def test_approval_needed_returns_empty_safe_payload_when_no_routes(monkeypatch) -> None:
    monkeypatch.setattr(revenue_service, "list_sprint_routes", lambda: [])

    payload = revenue_service.get_revenue_sprint_approval_needed()

    assert payload.status == "ok"
    assert payload.mode == "prepared"
    assert payload.approval_required is False
    assert payload.items == []
    assert payload.count == 0
    assert payload.requires_ceo_action is False
    assert payload.fallback is False


def test_approval_needed_returns_fallback_safe_payload_when_route_loading_fails(monkeypatch) -> None:
    def broken_routes() -> list:
        raise RuntimeError("legacy payload_json failure")

    monkeypatch.setattr(revenue_service, "list_sprint_routes", broken_routes)

    payload = revenue_service.get_revenue_sprint_approval_needed()

    assert payload.status == "ok"
    assert payload.items == []
    assert payload.count == 0
    assert payload.fallback is True
    assert payload.real_revenue_confirmed is False
    assert payload.payment_connected is False


def test_payload_parser_accepts_dict_and_string_and_ignores_null() -> None:
    assert revenue_service.parse_payload_json(None) is None
    assert revenue_service.parse_payload_json("") is None
    assert revenue_service.parse_payload_json({"id": "route"}) == {"id": "route"}
    assert revenue_service.parse_payload_json('{"id": "route"}') == {"id": "route"}
    assert revenue_service.parse_payload_json("not-json") is None


def test_approval_needed_endpoint_does_not_invent_approvals() -> None:
    response = client.get("/api/v1/revenue/sprint/approval-needed", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["count"] == len(payload["items"])
    assert all(item["approval_required"] is True for item in payload["items"])
    assert all(item["real_revenue_confirmed"] is False for item in payload["items"])


def test_sprint_report_keeps_actual_revenue_zero() -> None:
    response = client.post(
        "/api/v1/revenue/sprint/report",
        headers=CEO_HEADERS,
        json={
            "summary": "Reporte preparado; no hay ventas reales.",
            "risks": ["No inventar metricas."],
            "next_actions": ["Validar demanda organica."],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["actual_revenue_usd"] == 0
    assert payload["real_revenue_confirmed"] is False


def test_ceo_daily_center_shows_revenue_sprint() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["revenue_sprint"]["status"] == "revenue_execution_sprint_prepared_internal"
    assert "Revenue Sprint 30 dias" in payload["executive_summary"]


def test_control_center_shows_revenue_sprint_without_false_money_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "revenue-execution-sprint" in html.text
    assert "/api/v1/revenue/sprint/status" in js.text
    assert "renderRevenueSprint" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "venta real confirmada",
        "ingreso real confirmado",
        "campana pagada lanzada",
        "campaÃ±a pagada lanzada",
        "pago real conectado",
    ]:
        assert false_claim not in normalized
