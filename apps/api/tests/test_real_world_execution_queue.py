from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_real_world_execution_endpoints_require_auth() -> None:
    paths = [
        ("GET", "/api/v1/real-world-execution/status"),
        ("GET", "/api/v1/real-world-execution/queue"),
        ("GET", "/api/v1/real-world-execution/approval-needed"),
        ("POST", "/api/v1/real-world-execution/queue"),
        ("POST", "/api/v1/real-world-execution/queue/s8_marketing_paid_campaign_roi/mark-prepared"),
        ("POST", "/api/v1/real-world-execution/queue/s8_marketing_paid_campaign_roi/request-approval"),
        ("POST", "/api/v1/real-world-execution/queue/s8_marketing_paid_campaign_roi/block"),
    ]

    for method, path in paths:
        assert client.request(method, path, json={}).status_code == 401


def test_execution_status_is_safe_prepared_queue() -> None:
    response = client.get("/api/v1/real-world-execution/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "real_world_execution_queue_prepared"
    assert payload["total_items"] >= 10
    assert payload["prepared"] >= 1
    assert payload["ready_internal"] >= 1
    assert payload["approval_needed"] >= 1
    assert payload["money_needed"] >= 1
    assert payload["credentials_needed"] >= 1
    assert payload["external_execution_enabled"] is False
    assert payload["payment_executed"] is False
    assert payload["publication_executed"] is False
    assert payload["account_created"] is False
    assert payload["credentials_stored"] is False


def test_internal_action_does_not_require_ceo_and_does_not_execute() -> None:
    response = client.post(
        "/api/v1/real-world-execution/queue",
        headers=CEO_HEADERS,
        json={
            "action": f"Preparar checklist interno {uuid4()}",
            "area": "AUDITORIA",
            "owner": "AUDITORIA",
            "priority": "medium",
            "state": "ready_internal",
            "evidence": "internal_docs",
            "economic_impact": "mejora control sin gasto",
            "next_action": "Preparar documento interno.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "ready_internal"
    assert payload["requires_ceo"] is False
    assert payload["can_execute_internally"] is True
    assert payload["external_execution_enabled"] is False
    assert payload["manual_execution_confirmed"] is False


def test_paid_action_requires_ceo_and_stays_waiting_paid_approval() -> None:
    response = client.post(
        "/api/v1/real-world-execution/queue",
        headers=CEO_HEADERS,
        json={
            "action": f"Evaluar pauta pagada {uuid4()}",
            "area": "MARKETING",
            "owner": "MARKETING",
            "priority": "high",
            "state": "prepared",
            "requires_money": True,
            "economic_impact": "posible demanda si ROI positivo",
            "dependency": "ROI",
            "next_action": "Pedir aprobacion CEO antes de pagar.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "waiting_paid_approval"
    assert payload["requires_ceo"] is True
    assert payload["requires_money"] is True
    assert payload["payment_executed"] is False


def test_credentials_and_external_account_require_ceo() -> None:
    response = client.post(
        "/api/v1/real-world-execution/queue",
        headers=CEO_HEADERS,
        json={
            "action": f"Crear cuenta marketplace {uuid4()}",
            "area": "E-Commerce",
            "owner": "CEREBRO",
            "priority": "high",
            "state": "prepared",
            "requires_credentials": True,
            "requires_external_account": True,
            "risk": "sensitive",
            "next_action": "Esperar CEO; no crear cuenta.",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "waiting_credentials"
    assert payload["requires_ceo"] is True
    assert payload["requires_credentials"] is True
    assert payload["requires_external_account"] is True
    assert payload["account_created"] is False
    assert payload["credentials_stored"] is False


def test_prepared_does_not_execute_and_mark_prepared_respects_guards() -> None:
    response = client.post(
        "/api/v1/real-world-execution/queue/s8_ecommerce_payment_provider_decision/mark-prepared",
        headers=CEO_HEADERS,
        json={"note": "Solo preparar comparativo; no conectar pasarela."},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["state"] == "waiting_paid_approval"
    assert payload["requires_ceo"] is True
    assert payload["payment_executed"] is False
    assert payload["external_execution_enabled"] is False


def test_secret_like_values_are_rejected() -> None:
    response = client.post(
        "/api/v1/real-world-execution/queue",
        headers=CEO_HEADERS,
        json={
            "action": "Guardar token=DoNotStore",
            "area": "APIs/Skills",
            "owner": "CEREBRO",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "real_world_execution_secret_like_value_rejected"

    response = client.post(
        "/api/v1/real-world-execution/queue/s8_pluma_content_batch/request-approval",
        headers=CEO_HEADERS,
        json={"reason": "api_key=DoNotStore"},
    )
    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "real_world_execution_secret_like_value_rejected"


def test_block_and_approval_needed_are_safe_fallback_200() -> None:
    blocked = client.post(
        "/api/v1/real-world-execution/queue/s8_block_external_api_without_vault/block",
        headers=CEO_HEADERS,
        json={"reason": "Mantener bloqueado sin vault."},
    )
    approvals = client.get("/api/v1/real-world-execution/approval-needed", headers=CEO_HEADERS)

    assert blocked.status_code == 200
    assert blocked.json()["state"] == "blocked"
    assert blocked.json()["external_execution_enabled"] is False
    assert approvals.status_code == 200
    assert len(approvals.json()) >= 1
    assert all(item["external_execution_enabled"] is False for item in approvals.json()[:10])


def test_ceo_daily_center_reads_execution_queue() -> None:
    response = client.get("/api/v1/ceo/daily-center", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["real_world_execution"]["status"] == "real_world_execution_queue_prepared"
    assert payload["real_world_execution"]["total_items"] >= 10
    assert "Real World Execution Queue" in payload["executive_summary"]
    assert "no ejecuta acciones reales" in payload["executive_summary"]


def test_control_center_shows_execution_queue_without_false_execution_claims() -> None:
    html = client.get("/control-center")
    js = client.get("/control-center/assets/app.js")

    assert html.status_code == 200
    assert js.status_code == 200
    assert "real-world-execution-queue" in html.text
    assert "/api/v1/real-world-execution/status" in js.text
    assert "renderRealWorldExecutionQueue" in js.text
    normalized = js.text.lower()
    for false_claim in [
        "payment_executed=true",
        "publication_executed=true",
        "account_created=true",
        "credentials_stored=true",
        "api_execution_confirmed=true",
    ]:
        assert false_claim not in normalized
