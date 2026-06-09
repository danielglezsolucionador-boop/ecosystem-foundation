from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)
AUDITOR_HEADERS = auth_headers(client, ControlCenterRole.auditor)


def test_department_endpoints_require_auth() -> None:
    paths = [
        "/api/v1/departments",
        "/api/v1/departments/pluma",
        "/api/v1/departments/pluma/audit",
        "/api/v1/departments/audits",
        "/api/v1/departments/audits/not-real",
    ]
    for path in paths:
        assert client.get(path).status_code == 401

    assert client.post("/api/v1/departments/pluma/audit", json={}).status_code == 401


def test_department_inventory_maps_names_without_duplicates() -> None:
    response = client.get("/api/v1/departments", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    ids = [item["id"] for item in payload]
    assert len(ids) == len(set(ids))
    for expected in [
        "cerebro",
        "auditoria",
        "nube",
        "forja",
        "hermes",
        "pluma",
        "lente",
        "marketing",
        "marca_personal",
        "buscador_de_tendencias",
        "web_factory",
        "creador_de_apis_y_skills",
        "ecommerce",
        "sniff_amazon",
        "dcft",
        "sentinela",
        "arsenal",
    ]:
        assert expected in ids
    assert all(item["external_connection_enabled"] is False for item in payload)
    assert all(item["runtime_connected"] is False for item in payload)


def create_audit(department_id: str, *, mission: bool = False) -> dict:
    response = client.post(
        f"/api/v1/departments/{department_id}/audit",
        headers=CEO_HEADERS,
        json={
            "requested_by": "CEREBRO",
            "instruction": f"Revisar {department_id} desde Bloque I.",
            "create_cerebro_mission": mission,
        },
    )
    assert response.status_code == 201
    return response.json()


def test_pluma_audit_detects_content_gaps_and_missing_cabins() -> None:
    audit = create_audit("pluma")

    assert audit["department_id"] == "pluma"
    assert audit["heart_cabin"]["status"] == "missing"
    assert audit["technical_cabin"]["status"] in {"partial", "unknown"}
    assert audit["human_cabin"]["status"] in {"partial", "unknown"}
    assert audit["requires_forja"] is True
    assert any("bestseller" in gap.lower() for gap in audit["gaps"])
    assert any("ingles" in gap.lower() or "inglés" in gap.lower() for gap in audit["gaps"])
    assert audit["external_connection_enabled"] is False
    assert audit["runtime_connected"] is False


def test_lente_audit_supports_video_avatar_channel_review() -> None:
    audit = create_audit("lente")
    text = " ".join([*audit["gaps"], *audit["suggested_tasks"], audit["recommendation"]]).lower()

    assert audit["department_id"] == "lente"
    assert audit["requires_forja"] is True
    assert "avatar" in text or "avatares" in text
    assert "100k" in text or "canales" in text
    assert audit["sunat_enabled"] is False


def test_marketing_audit_keeps_paid_campaigns_under_ceo_control() -> None:
    audit = create_audit("marketing")
    text = " ".join([*audit["gaps"], audit["economic_impact"], audit["risk"]]).lower()

    assert audit["department_id"] == "marketing"
    assert "roi" in text
    assert "campanas pagadas" in text or "campañas pagadas" in text
    assert audit["runtime_connected"] is False


def test_dcft_audit_does_not_invent_own_sales_goal_or_sunat() -> None:
    audit = create_audit("dcft")
    text = str(audit).lower()

    assert audit["department_id"] == "dcft"
    assert audit["requires_forja"] is False
    assert audit["requires_ceo"] is True
    assert "no asignar meta de venta propia" in text
    assert "sunat_enabled': true" not in text
    assert audit["sunat_enabled"] is False
    assert audit["external_connection_enabled"] is False


def test_sentinela_audit_does_not_claim_b2b_future_product() -> None:
    audit = create_audit("sentinela")
    text = str(audit).lower()

    assert audit["department_id"] == "sentinela"
    assert audit["requires_forja"] is False
    assert audit["requires_ceo"] is True
    assert "producto b2b futuro" not in text
    assert "meta de venta propia" in text
    assert audit["runtime_connected"] is False


def test_missing_unknown_is_explicit_and_unknown_department_is_not_invented() -> None:
    pluma = client.get("/api/v1/departments/pluma", headers=CEO_HEADERS).json()
    unknown = client.get("/api/v1/departments/no-existe", headers=CEO_HEADERS)

    assert pluma["heart_cabin"]["status"] == "missing"
    assert pluma["technical_cabin"]["status"] in {"partial", "unknown"}
    assert pluma["human_cabin"]["status"] in {"partial", "unknown"}
    assert unknown.status_code == 404
    assert unknown.json()["detail"]["error"] == "department_not_found"


def test_send_to_forja_creates_prepared_task_and_audit_trail() -> None:
    audit = create_audit("pluma")
    response = client.post(
        f"/api/v1/departments/audits/{audit['id']}/send-to-forja",
        headers=CEO_HEADERS,
        json={"reason": "Preparar paquete FORJA para brechas PLUMA."},
    )
    payload = response.json()
    tasks = client.get("/api/v1/cerebro/tasks", headers=CEO_HEADERS).json()

    assert response.status_code == 200
    assert payload["status"] == "sent_to_forja"
    assert payload["forja_task_id"]
    assert payload["audit_trail"]
    task = next(item for item in tasks if item["id"] == payload["forja_task_id"])
    assert task["destination"] == "forja"
    assert task["external_connection_enabled"] is False
    assert task["runtime_connected"] is False


def test_cerebro_can_create_department_audit_mission_and_receive_report() -> None:
    audit = create_audit("lente", mission=True)
    report = client.post(
        f"/api/v1/departments/audits/{audit['id']}/send-to-cerebro",
        headers=CEO_HEADERS,
        json={"reason": "CEREBRO debe reportar brechas de LENTE al CEO."},
    )

    assert audit["cerebro_mission_id"]
    assert report.status_code == 200
    assert report.json()["status"] == "sent_to_cerebro"
    assert report.json()["cerebro_mission_id"]


def test_auditor_can_mark_department_audit_reviewed() -> None:
    audit = create_audit("marketing")
    response = client.post(
        f"/api/v1/departments/audits/{audit['id']}/mark-reviewed",
        headers=AUDITOR_HEADERS,
        json={"evidence": "Auditoria reviso brechas y prioridad."},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "reviewed"
    assert response.json()["audit_trail"]


def test_ceo_daily_center_reflects_department_audits_pending() -> None:
    create_audit("pluma")
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["auditoria"]["department_audits_pending"] >= 1
    assert payload["auditoria"]["department_audits"]
    assert "auditorias departamentales" in payload["executive_summary"]


def test_control_center_exposes_department_audit_panel_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "Auditoría de Departamentos" in html.text
    assert "/api/v1/departments" in js.text
    assert "renderDepartmentAudits" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "forja ya implemento",
        "forja ya implementó",
        "sunat activo",
        "dcft real conectado",
        "sentinela real conectado",
        "producto b2b futuro",
    ]:
        assert false_claim not in normalized
