from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def test_cerebro_chat_requires_auth() -> None:
    response = client.post("/api/v1/cerebro/chat", json={"message": "Hola CEREBRO"})

    assert response.status_code == 401


def test_cerebro_chat_authenticated_message_returns_reply() -> None:
    response = client.post(
        "/api/v1/cerebro/chat",
        json={"message": "Hola CEREBRO, dame estado interno."},
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["reply"]
    assert payload["provider"] == "internal"
    assert payload["state"]["sombra_connected"] is False


def test_cerebro_chat_mission_message_creates_action() -> None:
    response = client.post(
        "/api/v1/cerebro/chat",
        json={
            "message": "Crea una mision interna QA para seguimiento ejecutivo.",
            "action": "mission",
        },
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    action = payload["actions"][0]
    assert action["type"] == "mission_created"
    assert action["status"] == "created"
    assert action["id"].startswith("cerebro_mission_")


def test_cerebro_chat_forja_message_creates_task_action() -> None:
    response = client.post(
        "/api/v1/cerebro/chat",
        json={
            "message": "FORJA, prepara una tarea interna de QA controlada.",
            "action": "forja",
        },
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    action = payload["actions"][0]
    assert action["type"] == "forja_task_created"
    assert action["status"] == "created"
    assert action["id"].startswith("cerebro-task-")
    assert payload["state"]["forja_tasks"] >= 1


def test_cerebro_chat_centinela_status_does_not_connect_sombra() -> None:
    response = client.post(
        "/api/v1/cerebro/chat",
        json={
            "message": "Consulta CENTINELA y riesgos internos sin tocar SOMBRA.",
            "action": "centinela",
        },
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    action = payload["actions"][0]
    assert action["type"] == "centinela_status"
    assert action["status"] == "prepared"
    assert payload["state"]["centinela_status"] == "prepared"
    assert payload["state"]["sombra_connected"] is False
    assert "No consulte el servidor externo de SOMBRA" in payload["reply"]


def test_cerebro_chat_generates_sanitized_commercial_draft() -> None:
    response = client.post(
        "/api/v1/cerebro/chat",
        json={"message": "Prepara una publicacion LinkedIn y mensaje comercial para un cliente."},
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    action = payload["actions"][0]
    assert action["type"] == "commercial_draft_created"
    assert action["status"] == "created"
    assert action["id"].startswith("cerebro-commercial-draft-")
    assert "no publica automaticamente" in payload["reply"].lower()


def test_cerebro_commercial_draft_endpoint_requires_auth() -> None:
    response = client.post(
        "/api/v1/cerebro/commercial-draft",
        json={"title": "LinkedIn", "summary": "Borrador defensivo"},
    )

    assert response.status_code == 401


def test_cerebro_commercial_draft_endpoint_is_sanitized() -> None:
    response = client.post(
        "/api/v1/cerebro/commercial-draft",
        json={
            "title": "Riesgos de credenciales expuestas",
            "summary": "Preparar contenido sin fuentes ni datos sensibles.",
            "client_context": {"country": "PE", "sector": "ciberseguridad"},
            "safe_for_commercial_use": True,
        },
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    combined = " ".join(
        [
            payload["linkedin_post_idea"],
            payload["private_message"],
            payload["centinela_angle"],
        ]
    ).lower()
    assert "sombra" not in combined
    assert payload["publish_allowed"] is False
    assert payload["contact_allowed"] is False
    assert payload["mentions_sombra"] is False


def test_cerebro_chat_reviews_internal_sombra_inbox_without_external_runtime() -> None:
    response = client.post(
        "/api/v1/cerebro/chat",
        json={"message": "Revisa inteligencia entrante y mensajes de SOMBRA."},
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["actions"][0]["type"] == "sombra_inbox_reviewed"
    assert "no consulte" in payload["reply"].lower() or "inbox interno" in payload["reply"].lower()


def test_centinela_status_endpoint_is_internal_only() -> None:
    response = client.get("/api/v1/centinela/status", headers=CEO_HEADERS)

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "prepared"
    assert payload["sombra_connected"] is False
    assert payload["source"] == "internal_control_center"


def test_control_center_uses_operational_cerebro_chat_copy() -> None:
    response = client.get("/control-center/assets/app.js")

    assert response.status_code == 200
    assert "/api/v1/cerebro/chat" in response.text
    assert "CEREBRO no tiene chat LLM conectado aqui" not in response.text
