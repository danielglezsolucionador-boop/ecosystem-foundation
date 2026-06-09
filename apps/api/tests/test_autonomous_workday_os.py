from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_workday_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/workday/status"),
        ("POST", "/api/v1/workday/start"),
        ("GET", "/api/v1/workday/morning"),
        ("POST", "/api/v1/workday/morning/generate"),
        ("GET", "/api/v1/workday/midday"),
        ("POST", "/api/v1/workday/midday/generate"),
        ("GET", "/api/v1/workday/evening"),
        ("POST", "/api/v1/workday/evening/generate"),
        ("GET", "/api/v1/workday/alerts"),
        ("POST", "/api/v1/workday/alerts/evaluate"),
        ("GET", "/api/v1/workday/priority-changes"),
        ("POST", "/api/v1/workday/priority-changes"),
        ("GET", "/api/v1/workday/report"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_start_workday_uses_peru_timezone_and_manual_scheduler() -> None:
    response = client.post("/api/v1/workday/start", headers=CEO_HEADERS)

    assert response.status_code == 201
    payload = response.json()
    assert payload["timezone"] == "America/Lima"
    assert payload["scheduler_status"] == "prepared"
    assert payload["manual_trigger_available"] is True
    assert payload["generated_at"].endswith("-05:00")
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False


def test_status_reports_schedule_and_no_real_scheduler() -> None:
    response = client.get("/api/v1/workday/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "autonomous_workday_os_prepared_internal"
    assert payload["schedule"]["morning_time"] == "08:00"
    assert payload["schedule"]["midday_time"] == "13:00"
    assert payload["schedule"]["evening_time"] == "19:00"
    assert payload["scheduler_status"] == "prepared"
    assert payload["manual_trigger_available"] is True


def test_morning_generate_includes_goals_missions_and_action_plan() -> None:
    response = client.post("/api/v1/workday/morning/generate", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "morning"
    assert payload["schedule_time"] == "08:00"
    assert "USD 6,000" in payload["summary"]
    assert "USD 10,000" in payload["summary"]
    assert payload["action_plan"]
    assert payload["external_connection_enabled"] is False


def test_midday_generate_tracks_priorities_alerts_and_blockers() -> None:
    response = client.post("/api/v1/workday/midday/generate", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "midday"
    assert payload["schedule_time"] == "13:00"
    assert "Mediodía" in payload["report"]
    assert payload["decisions_by_cerebro"]


def test_evening_generate_reports_revenue_auditoria_nube_and_tomorrow() -> None:
    response = client.post("/api/v1/workday/evening/generate", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["phase"] == "evening"
    assert payload["schedule_time"] == "19:00"
    assert "Global USD" in payload["report"]
    assert "e-commerce USD" in payload["report"]
    assert any("NUBE" in item for item in payload["decisions_by_cerebro"])


def test_low_relevance_alert_does_not_interrupt_ceo() -> None:
    response = client.post(
        "/api/v1/workday/alerts/evaluate",
        headers=CEO_HEADERS,
        json={
            "title": f"Señal baja {uuid4()}",
            "summary": "Comentario menor sin impacto económico ni riesgo.",
            "category": "low_signal",
            "relevance_score": 20,
            "recommended_action": "Registrar sin interrumpir.",
        },
    )
    payload = response.json()
    alerts = client.get("/api/v1/workday/alerts", headers=CEO_HEADERS).json()

    assert response.status_code == 200
    assert payload["interrupt_ceo"] is False
    assert payload["included_in_ceo_feed"] is False
    assert payload["id"] not in {alert["id"] for alert in alerts}


def test_high_relevance_alert_appears_in_ceo_feed() -> None:
    title = f"Oportunidad temporal {uuid4()}"
    response = client.post(
        "/api/v1/workday/alerts/evaluate",
        headers=CEO_HEADERS,
        json={
            "title": title,
            "summary": "Nueva tendencia con oportunidad de ingresos hoy.",
            "category": "revenue_opportunity",
            "relevance_score": 88,
            "why_it_matters": "Puede mover la meta global si se prepara sin gasto real.",
            "opportunity": "Contenido orgánico vendible.",
            "recommended_action": "Pedir a PLUMA y LENTE propuesta sin publicar.",
            "departments_involved": ["PLUMA", "LENTE", "MARKETING"],
            "economic_impact_usd": 900,
        },
    )
    alerts = client.get("/api/v1/workday/alerts", headers=CEO_HEADERS)

    assert response.status_code == 200
    assert response.json()["interrupt_ceo"] is True
    assert response.json()["included_in_ceo_feed"] is True
    assert title in {alert["title"] for alert in alerts.json()}


def test_priority_change_does_not_require_ceo_and_registers_audit() -> None:
    response = client.post(
        "/api/v1/workday/priority-changes",
        headers=CEO_HEADERS,
        json={
            "previous_priority": "Revisar documentación interna.",
            "new_priority": "Preparar oportunidad orgánica para Revenue OS.",
            "reason": "Apareció ventana temporal sin gasto real.",
            "opportunity_or_risk": "temporary_opportunity",
            "economic_impact_usd": 400,
            "departments_affected": ["CEREBRO", "PLUMA", "MARKETING"],
        },
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["requires_ceo_approval"] is False
    assert payload["audit_event_id"]
    assert payload["external_connection_enabled"] is False


def test_money_alert_requires_ceo_approval() -> None:
    response = client.post(
        "/api/v1/workday/alerts/evaluate",
        headers=CEO_HEADERS,
        json={
            "title": f"API con costo {uuid4()}",
            "summary": "Proveedor externo pagado podría acelerar una oportunidad.",
            "category": "revenue_opportunity",
            "relevance_score": 90,
            "recommended_action": "Pedir decisión CEO antes de gastar.",
            "requires_money": True,
            "economic_impact_usd": 1500,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["requires_ceo_approval"] is True
    assert payload["payment_connected"] is False


def test_report_consolidates_workday_sections() -> None:
    client.post("/api/v1/workday/morning/generate", headers=CEO_HEADERS)
    client.post("/api/v1/workday/midday/generate", headers=CEO_HEADERS)
    client.post("/api/v1/workday/evening/generate", headers=CEO_HEADERS)
    response = client.get("/api/v1/workday/report", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "workday_report_prepared_internal"
    assert payload["morning"]["phase"] == "morning"
    assert payload["midday"]["phase"] == "midday"
    assert payload["evening"]["phase"] == "evening"


def test_ceo_daily_center_shows_workday() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["workday"]["status"] == "autonomous_workday_os_prepared_internal"
    assert "Workday OS" in payload["executive_summary"]


def test_frontend_exposes_workday_os_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "workday-os" in html.text
    assert "/api/v1/workday/status" in js.text
    assert "renderWorkdayOs" in js.text
    assert "SUNAT real activo" not in js.text
    assert "campaña pagada real ejecutada" not in js.text
