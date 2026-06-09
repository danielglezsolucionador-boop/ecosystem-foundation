from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
OPERATOR_HEADERS = auth_headers(client, ControlCenterRole.operator)


def test_chief_of_staff_endpoints_require_auth() -> None:
    paths = [
        "/api/v1/cerebro/chief-of-staff/status",
        "/api/v1/cerebro/goals",
        "/api/v1/cerebro/departments/goals",
        "/api/v1/cerebro/missions",
        "/api/v1/cerebro/alerts",
        "/api/v1/cerebro/revenue",
        "/api/v1/cerebro/approval-requests",
        "/api/v1/cerebro/checkpoints/morning",
        "/api/v1/cerebro/checkpoints/midday",
        "/api/v1/cerebro/checkpoints/evening",
    ]

    for path in paths:
        assert client.get(path).status_code == 401


def test_chief_of_staff_status_exposes_goals_and_authority_matrix() -> None:
    response = client.get("/api/v1/cerebro/chief-of-staff/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "cerebro_chief_of_staff_os_prepared"
    assert payload["motto"] == "El tiempo es dinero"
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["sunat_enabled"] is False
    assert payload["local_agent_enabled"] is False
    assert any(goal["monthly_target_usd"] == 6000 for goal in payload["company_goals"])
    assert any(goal["monthly_target_usd"] == 10000 for goal in payload["company_goals"])

    matrix = {item["action_type"]: item for item in payload["authority_matrix"]}
    assert matrix["local_agent_activation"]["level"] == "NO_APPROVAL_REQUIRED"
    assert matrix["organic_post_configured_account"]["level"] == "NO_APPROVAL_REQUIRED"
    assert matrix["controlled_production_deploy"]["level"] == "NO_APPROVAL_REQUIRED"
    assert matrix["real_money_payment"]["level"] == "CEO_APPROVAL_REQUIRED"
    assert all(item["runtime_connected"] is False for item in payload["authority_matrix"])


def test_cerebro_mission_for_local_agent_is_prepared_without_ceo_approval() -> None:
    response = client.post(
        "/api/v1/cerebro/missions",
        headers=CEO_HEADERS,
        json={
            "title": f"Preparar Local Agent {uuid4()}",
            "objective": "Activar politica preparada sin encender runtime real.",
            "leader_department": "CEREBRO",
            "involved_departments": ["HERMES", "AUDITORIA"],
            "action_type": "local_agent_activation",
            "requires_money": False,
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["authority_level"] == "NO_APPROVAL_REQUIRED"
    assert payload["requires_ceo_approval"] is False
    assert payload["technical_status"] == "prepared"
    assert payload["runtime_connected"] is False
    assert payload["local_agent_enabled"] is False


def test_money_mission_requires_ceo_approval_and_clear_economic_matrix() -> None:
    response = client.post(
        "/api/v1/cerebro/missions",
        headers=CEO_HEADERS,
        json={
            "title": f"Campana pagada controlada {uuid4()}",
            "objective": "Evaluar gasto real antes de ejecutar.",
            "leader_department": "MARKETING",
            "involved_departments": ["CEREBRO", "AUDITORIA"],
            "action_type": "paid_campaign",
            "requires_money": True,
            "investment_required": 100,
            "expected_revenue": 600,
            "risks": ["riesgo reputacional controlado"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    matrix = payload["economic_matrix"]
    assert payload["authority_level"] == "CEO_APPROVAL_REQUIRED"
    assert payload["requires_ceo_approval"] is True
    assert payload["state"] == "waiting_ceo_approval"
    assert matrix["investment_required"] == 100
    assert matrix["expected_revenue"] == 600
    assert matrix["expected_net_profit"] == 500
    assert matrix["monthly_goal"] == 6000
    assert matrix["monthly_goal_contribution_percent"] == 8.33


def test_low_relevance_alert_does_not_interrupt_high_alert_does() -> None:
    low_title = f"Senal baja {uuid4()}"
    high_title = f"Oportunidad fuerte {uuid4()}"
    low = client.post(
        "/api/v1/cerebro/alerts",
        headers=CEO_HEADERS,
        json={
            "title": low_title,
            "summary": "Dato de baja relevancia.",
            "relevance_score": 20,
            "risk_level": "low",
        },
    )
    high = client.post(
        "/api/v1/cerebro/alerts",
        headers=CEO_HEADERS,
        json={
            "title": high_title,
            "summary": "Esto puede generar ingresos.",
            "relevance_score": 92,
            "risk_level": "medium",
            "economic_impact": 900,
            "dafo": {
                "strengths": ["Velocidad"],
                "weaknesses": ["Validacion pendiente"],
                "opportunities": ["Ingreso organico"],
                "threats": ["Competencia"],
            },
        },
    )
    listed = client.get("/api/v1/cerebro/alerts", headers=CEO_HEADERS)

    assert low.status_code == 201
    assert low.json()["interrupt_ceo"] is False
    assert high.status_code == 201
    assert high.json()["interrupt_ceo"] is True
    titles = {item["title"] for item in listed.json()}
    assert high_title in titles
    assert low_title not in titles


def test_revenue_opportunity_separates_global_and_ecommerce_goals() -> None:
    global_response = client.post(
        "/api/v1/cerebro/revenue/opportunities",
        headers=CEO_HEADERS,
        json={
            "title": f"Oferta API {uuid4()}",
            "description": "API vendible preparada sin cobro real.",
            "department": "CREADOR DE APIS Y SKILLS",
            "investment_required": 100,
            "expected_revenue": 600,
            "return_time": "7 dias",
            "recommendation": "CEO, USD 100 podria retornar USD 600.",
        },
    )
    ecommerce_response = client.post(
        "/api/v1/cerebro/revenue/opportunities",
        headers=CEO_HEADERS,
        json={
            "title": f"Producto e-commerce {uuid4()}",
            "description": "Senal e-commerce separada.",
            "department": "SNIFF AMAZON",
            "expected_revenue": 1000,
            "ecommerce_separate": True,
        },
    )

    assert global_response.status_code == 201
    assert global_response.json()["requires_ceo_approval"] is True
    assert global_response.json()["economic_matrix"]["monthly_goal"] == 6000
    assert global_response.json()["economic_matrix"]["monthly_goal_contribution_percent"] == 8.33
    assert ecommerce_response.status_code == 201
    assert ecommerce_response.json()["requires_ceo_approval"] is False
    assert ecommerce_response.json()["economic_matrix"]["monthly_goal"] == 10000


def test_approval_request_can_only_be_closed_by_ceo_or_admin() -> None:
    created = client.post(
        "/api/v1/cerebro/approval-requests",
        headers=CEO_HEADERS,
        json={
            "title": f"Pago proveedor {uuid4()}",
            "description": "Pago real pendiente de aprobacion CEO.",
            "action_type": "real_money_payment",
            "requested_by_department": "MARKETING",
            "investment_required": 100,
            "expected_revenue": 600,
            "recommendation": "Aprobar solo si el retorno esperado justifica el riesgo.",
        },
    )
    request_id = created.json()["id"]
    denied = client.post(
        f"/api/v1/cerebro/approval-requests/{request_id}/approve",
        headers=OPERATOR_HEADERS,
        json={"evidence": "operator attempt"},
    )
    approved = client.post(
        f"/api/v1/cerebro/approval-requests/{request_id}/approve",
        headers=CEO_HEADERS,
        json={"evidence": "CEO reviso matriz economica."},
    )

    assert created.status_code == 201
    assert created.json()["requires_ceo_approval"] is True
    assert denied.status_code == 403
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["approved_by"]


def test_ceo_daily_center_includes_chief_of_staff_without_false_runtime() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    chief = payload["cerebro"]["chief_of_staff"]
    assert chief["motto"] == "El tiempo es dinero"
    assert chief["runtime_connected"] is False
    assert chief["external_connection_enabled"] is False
    assert "Chief of Staff OS" in payload["executive_summary"]


def test_control_center_shows_chief_of_staff_panel_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "CEREBRO Chief of Staff" in html.text
    assert "El tiempo es dinero" in html.text
    assert "/api/v1/cerebro/chief-of-staff/status" in js.text
    assert "renderCerebroChiefOfStaff" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "local agent activo",
        "sunat activo",
        "apis externas conectadas",
        "dcft real conectado",
        "sentinela real conectado",
    ]:
        assert false_claim not in normalized
