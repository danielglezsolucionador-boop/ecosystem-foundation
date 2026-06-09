from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def create_audit(department_id: str = "pluma") -> dict:
    response = client.post(
        f"/api/v1/departments/{department_id}/audit",
        headers=CEO_HEADERS,
        json={
            "requested_by": "CEREBRO",
            "instruction": f"Detectar brechas para upgrade {uuid4()}",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()


def create_package(**overrides) -> dict:
    payload = {
        "department_id": "pluma",
        "gaps": ["Falta paquete de contenido vendible."],
        "required_changes": ["Preparar plantilla de contenido sin publicar externamente."],
        "business_impact": "Puede acelerar contenido orgánico y apoyar meta USD 6,000.",
        "risk": "controlled",
    }
    payload.update(overrides)
    response = client.post("/api/v1/upgrades/packages", headers=CEO_HEADERS, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_upgrade_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/upgrades/status"),
        ("GET", "/api/v1/upgrades/packages"),
        ("POST", "/api/v1/upgrades/packages"),
        ("GET", "/api/v1/upgrades/department/pluma"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_create_package_from_audit_gap() -> None:
    audit = create_audit("pluma")
    package = create_package(
        department_id="pluma",
        source_audit_id=audit["id"],
        gaps=[],
        required_changes=[],
    )

    assert package["source_audit_id"] == audit["id"]
    assert package["department_id"] == "pluma"
    assert package["gaps"]
    assert package["required_changes"]
    assert package["status"] == "prioritized"
    assert package["forge_status"] == "not_sent"
    assert package["audit_status"] == "not_requested"


def test_send_to_forja_is_prepared_not_real_execution() -> None:
    package = create_package()
    response = client.post(
        f"/api/v1/upgrades/packages/{package['id']}/send-to-forja",
        headers=CEO_HEADERS,
        json={"instruction": "Preparar upgrade interno; no tocar FORJA externa."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "sent_to_forja"
    assert payload["forge_status"] == "prepared"
    assert payload["technical_status"] == "pending_execution"
    assert payload["forge_task_id"]
    assert payload["runtime_connected"] is False


def test_cannot_mark_implemented_without_evidence() -> None:
    package = create_package()
    response = client.post(
        f"/api/v1/upgrades/packages/{package['id']}/mark-implemented",
        headers=CEO_HEADERS,
        json={"evidence": ""},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "upgrade_evidence_required"


def test_mark_implemented_with_evidence_waits_for_audit() -> None:
    package = create_package()
    response = client.post(
        f"/api/v1/upgrades/packages/{package['id']}/mark-implemented",
        headers=CEO_HEADERS,
        json={"evidence": "Archivo local de evidencia y pruebas.", "implemented_by": "FORJA preparada"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "implemented_pending_audit"
    assert payload["forge_status"] == "implemented_with_evidence"
    assert payload["technical_status"] == "evidence_recorded_pending_audit"
    assert payload["audit_status"] != "approved"


def test_request_review_links_auditoria() -> None:
    package = create_package()
    response = client.post(
        f"/api/v1/upgrades/packages/{package['id']}/request-review",
        headers=CEO_HEADERS,
        json={"reason": "Revisión posterior obligatoria."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "waiting_audit"
    assert payload["audit_status"] == "pending_review"
    assert payload["audit_review_id"]
    assert payload["review_links"]


def test_approve_requires_auditoria_review() -> None:
    package = create_package()
    rejected = client.post(
        f"/api/v1/upgrades/packages/{package['id']}/approve",
        headers=CEO_HEADERS,
        json={"reason": "Intento sin revisión."},
    )
    reviewed = client.post(
        f"/api/v1/upgrades/packages/{package['id']}/request-review",
        headers=CEO_HEADERS,
        json={"reason": "AUDITORÍA revisa antes de aprobar."},
    )
    approved = client.post(
        f"/api/v1/upgrades/packages/{package['id']}/approve",
        headers=CEO_HEADERS,
        json={"reason": "AUDITORÍA enlazada revisó el paquete."},
    )

    assert rejected.status_code == 400
    assert rejected.json()["detail"]["error"] == "auditoria_review_required"
    assert reviewed.status_code == 200
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"
    assert approved.json()["audit_status"] == "approved"


def test_reject_records_reason() -> None:
    package = create_package()
    response = client.post(
        f"/api/v1/upgrades/packages/{package['id']}/reject",
        headers=CEO_HEADERS,
        json={"reason": "Evidencia insuficiente para cierre."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "rejected"
    assert payload["audit_status"] == "rejected"
    assert "Evidencia insuficiente" in payload["risk"]


def test_dcft_and_sentinela_are_governed_not_prohibited() -> None:
    dcft = create_package(
        department_id="dcft",
        gaps=["Actualizar readiness contable sin SUNAT real."],
        required_changes=["Preparar documentación gobernada."],
        business_impact="Primer producto comercial prioritario, sin runtime real.",
    )
    sentinela = create_package(
        department_id="sentinela",
        gaps=["Revisar defensa futura del ecosistema."],
        required_changes=["Preparar paquete de seguridad sin activar runtime."],
        business_impact="Futuro producto B2B protegido.",
    )
    send = client.post(
        f"/api/v1/upgrades/packages/{dcft['id']}/send-to-forja",
        headers=CEO_HEADERS,
        json={},
    )

    assert dcft["governance_status"] == "governed_no_touch"
    assert sentinela["governance_status"] == "governed_no_touch"
    assert dcft["sunat_enabled"] is False
    assert sentinela["runtime_connected"] is False
    assert send.status_code == 200
    assert send.json()["technical_status"] == "governed_pending_execution"


def test_unknown_department_is_marked_missing_without_inventing_data() -> None:
    package = create_package(
        department_id=f"ghost-{uuid4()}",
        gaps=["Brecha declarada por CEO, datos no encontrados."],
        required_changes=["Investigar existencia real antes de implementar."],
        business_impact="unknown",
    )

    assert package["department_status"] == "missing/unknown"
    assert package["business_impact"] == "unknown"
    assert package["external_connection_enabled"] is False


def test_department_filter_returns_packages() -> None:
    package = create_package(department_id="marketing")
    response = client.get("/api/v1/upgrades/department/marketing", headers=CEO_HEADERS)

    assert response.status_code == 200
    assert package["id"] in {item["id"] for item in response.json()}


def test_ceo_daily_center_shows_upgrades() -> None:
    create_package(department_id="lente")
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["upgrades"]["status"] == "department_upgrade_pipeline_prepared_internal"
    assert "Upgrade Pipeline" in payload["executive_summary"]


def test_frontend_exposes_upgrade_pipeline_without_false_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "department-upgrade-pipeline" in html.text
    assert "/api/v1/upgrades/status" in js.text
    assert "renderDepartmentUpgradePipeline" in js.text
    assert "implementación completada sin evidencia" not in js.text.lower()
    assert "sunat real activo" not in js.text.lower()
