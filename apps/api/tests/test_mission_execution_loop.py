from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
AUDITOR_HEADERS = auth_headers(client, ControlCenterRole.auditor)


def mission_payload(**overrides):
    payload = {
        "title": f"Revisar PLUMA y LENTE {uuid4()}",
        "ceo_instruction": "Revisa PLUMA y LENTE y dime qué les falta para generar contenido que venda.",
        "leader_department": "CEREBRO",
        "priority": "p1",
        "action_type": "create_internal_mission",
        "expected_business_impact": "Impacto comercial por estimar.",
        "requires_money": False,
    }
    payload.update(overrides)
    return payload


def create_mission(**overrides):
    response = client.post("/api/v1/missions", headers=CEO_HEADERS, json=mission_payload(**overrides))
    assert response.status_code == 201, response.text
    return response.json()


def test_mission_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/missions"),
        ("POST", "/api/v1/missions"),
        ("GET", "/api/v1/missions/active"),
        ("GET", "/api/v1/missions/reports/daily"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_create_mission_from_ceo_instruction() -> None:
    payload = create_mission()

    assert payload["status"] == "created"
    assert payload["source"] == "ceo_instruction"
    assert "PLUMA" in payload["involved_departments"]
    assert "LENTE" in payload["involved_departments"]
    assert "AUDITORIA" in payload["involved_departments"]
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False
    assert payload["sunat_enabled"] is False


def test_plan_mission_creates_steps() -> None:
    mission = create_mission()
    response = client.post(
        f"/api/v1/missions/{mission['id']}/plan",
        headers=CEO_HEADERS,
        json={
            "steps": [
                "Revisar mensajes de PLUMA.",
                "Revisar capacidad visual de LENTE.",
                "Preparar reporte CEO.",
            ],
            "involved_departments": ["PLUMA", "LENTE", "AUDITORIA"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "planned"
    assert len(payload["steps"]) == 3
    assert payload["next_action"]


def test_assign_mission_to_departments() -> None:
    mission = create_mission()
    response = client.post(
        f"/api/v1/missions/{mission['id']}/assign",
        headers=CEO_HEADERS,
        json={
            "departments": ["PLUMA", "LENTE"],
            "instruction": "Revisar brechas y entregar hallazgos a CEREBRO.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "assigned"
    assigned = {item["department"] for item in payload["assignments"]}
    assert {"PLUMA", "LENTE"}.issubset(assigned)


def test_dispatch_mission_is_internal_only() -> None:
    mission = create_mission()
    response = client.post(
        f"/api/v1/missions/{mission['id']}/dispatch",
        headers=CEO_HEADERS,
        json={"department": "PLUMA", "instruction": "Preparar copy orgánico para revisión."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "in_progress"
    assert payload["external_connection_enabled"] is False
    assert payload["runtime_connected"] is False


def test_request_audit_links_auditoria_review() -> None:
    mission = create_mission()
    response = client.post(
        f"/api/v1/missions/{mission['id']}/request-audit",
        headers=CEO_HEADERS,
        json={"criteria": ["functional_quality", "security"], "reason": "Validar antes de FORJA."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "waiting_audit"
    assert payload["audit_reviews"]
    assert payload["audit_reviews"][0]["status"] == "pending_review"


def test_send_to_forja_is_prepared_not_external_execution() -> None:
    mission = create_mission()
    response = client.post(
        f"/api/v1/missions/{mission['id']}/send-to-forja",
        headers=CEO_HEADERS,
        json={"instruction": "Preparar mejora interna; no tocar FORJA externa."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "waiting_forge"
    assert payload["forge_requests"]
    assert payload["forge_requests"][0]["technical_status"] == "prepared_no_external_forja_execution"
    assert payload["runtime_connected"] is False


def test_update_complete_and_timeline() -> None:
    mission = create_mission()
    update = client.post(
        f"/api/v1/missions/{mission['id']}/update",
        headers=CEO_HEADERS,
        json={"message": "PLUMA y LENTE enviaron brechas.", "department": "CEREBRO"},
    )
    complete = client.post(
        f"/api/v1/missions/{mission['id']}/complete",
        headers=CEO_HEADERS,
        json={"summary": "Misión cerrada con reporte CEO.", "evidence": "local_report"},
    )
    timeline = client.get(f"/api/v1/missions/{mission['id']}/timeline", headers=CEO_HEADERS)

    assert update.status_code == 200
    assert complete.status_code == 200
    assert complete.json()["status"] == "completed"
    assert timeline.status_code == 200
    assert any(item["timeline_type"] == "reports" for item in timeline.json()["timeline"])


def test_block_mission_records_safe_block() -> None:
    mission = create_mission()
    response = client.post(
        f"/api/v1/missions/{mission['id']}/block",
        headers=CEO_HEADERS,
        json={"reason": "Falta aprobación CEO para cuenta externa.", "blocked_by": "CEREBRO"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "blocked"
    assert "CEO" in payload["next_action"]


def test_money_requires_ceo_approval() -> None:
    payload = create_mission(
        title=f"Campaña pagada {uuid4()}",
        ceo_instruction="Preparar pauta pagada solo si CEO aprueba presupuesto.",
        action_type="paid_campaign",
        requires_money=True,
        investment_required=100,
        expected_revenue=600,
    )

    assert payload["requires_ceo_approval"] is True
    assert payload["status"] == "waiting_ceo_approval"
    assert payload["payment_connected"] is False


def test_organic_post_does_not_require_ceo_approval() -> None:
    payload = create_mission(
        title=f"Post orgánico {uuid4()}",
        ceo_instruction="Preparar publicación orgánica en cuenta ya configurada.",
        action_type="organic_post_configured_account",
        requires_money=False,
    )

    assert payload["requires_ceo_approval"] is False
    assert payload["status"] == "created"


def test_local_agent_policy_does_not_create_runtime() -> None:
    payload = create_mission(
        title=f"Local Agent preparado {uuid4()}",
        ceo_instruction="Preparar checklist interno para Local Agent sin activar runtime.",
        action_type="local_agent_activation",
        requires_money=False,
    )

    assert payload["requires_ceo_approval"] is False
    assert payload["local_agent_enabled"] is False
    assert payload["runtime_connected"] is False


def test_forja_internal_policy_does_not_require_ceo_approval() -> None:
    payload = create_mission(
        title=f"FORJA interna {uuid4()}",
        ceo_instruction="Enviar tarea interna preparada a FORJA sin tocar FORJA externa.",
        action_type="send_task_to_forja",
        requires_money=False,
    )

    assert payload["requires_ceo_approval"] is False
    assert payload["runtime_connected"] is False


def test_protected_external_action_waits_for_ceo_and_does_not_execute() -> None:
    payload = create_mission(
        title=f"SUNAT real bloqueado {uuid4()}",
        ceo_instruction="Activar SUNAT real.",
        action_type="activate_sunat",
        requires_money=False,
    )

    assert payload["requires_ceo_approval"] is True
    assert payload["status"] == "waiting_ceo_approval"
    assert payload["sunat_enabled"] is False
    assert payload["external_connection_enabled"] is False


def test_unknown_economic_impact_is_reported_not_invented() -> None:
    payload = create_mission(
        title=f"Capacidad incierta {uuid4()}",
        ceo_instruction="Analiza una idea interna sin datos económicos.",
        expected_business_impact="unknown",
    )

    assert payload["expected_business_impact"] == "unknown"
    assert payload["revenue_links"] == []


def test_auditor_cannot_write_mission_actions() -> None:
    mission = create_mission()
    response = client.post(
        f"/api/v1/missions/{mission['id']}/dispatch",
        headers=AUDITOR_HEADERS,
        json={"department": "PLUMA", "instruction": "Intento no permitido."},
    )

    assert response.status_code == 403


def test_ceo_daily_center_includes_mission_loop() -> None:
    create_mission(title=f"Misión visible CEO {uuid4()}")
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["missions"]["status"] == "mission_execution_loop_operational_internal"
    assert payload["missions"]["active_missions"] >= 1
    assert "Mission Loop" in payload["executive_summary"]


def test_frontend_exposes_mission_loop_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "mission-execution-loop" in html.text
    assert "/api/v1/missions/active" in js.text
    assert "renderMissionExecutionLoop" in js.text
    assert "Mission Execution Loop" in js.text
    assert "venta real automática" not in js.text.lower()
    assert "sunat real activo" not in js.text.lower()
