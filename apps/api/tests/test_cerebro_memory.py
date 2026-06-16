import pytest
from fastapi.testclient import TestClient

import app.services.cerebro as cerebro_service
from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)


@pytest.fixture(autouse=True)
def _force_internal_cerebro_reply(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(cerebro_service, "generate_cerebro_reply", lambda **_kwargs: None)


def test_cerebro_chat_creates_and_continues_postgres_conversation() -> None:
    headers = auth_headers(client, ControlCenterRole.ceo)

    first = client.post(
        "/api/v1/cerebro/chat",
        json={
            "message": "Hola CEREBRO, esta conversacion debe guardarse.",
            "context": "control_center",
            "app_context": {"test": "memory"},
        },
        headers=headers,
    )

    assert first.status_code == 200
    first_payload = first.json()
    conversation_id = first_payload["conversation_id"]
    assert conversation_id.startswith("cerebro-conv-")
    assert first_payload["message_id"].startswith("cerebro-msg-")
    assert first_payload["assistant_message_id"].startswith("cerebro-msg-")
    assert first_payload["response"] == first_payload["reply"]

    listed = client.get("/api/v1/cerebro/conversations", headers=headers)
    assert listed.status_code == 200
    conversations = listed.json()
    stored_summary = next(item for item in conversations if item["id"] == conversation_id)
    assert stored_summary["message_count"] == 2
    assert stored_summary["latest_message"]

    detail = client.get(f"/api/v1/cerebro/conversations/{conversation_id}", headers=headers)
    assert detail.status_code == 200
    messages = detail.json()["messages"]
    assert [message["role"] for message in messages] == ["user", "assistant"]
    assert messages[0]["content"] == "Hola CEREBRO, esta conversacion debe guardarse."

    second = client.post(
        "/api/v1/cerebro/chat",
        json={
            "message": "Segundo mensaje: no reinicies el historial.",
            "conversation_id": conversation_id,
            "context": "control_center",
        },
        headers=headers,
    )

    assert second.status_code == 200
    assert second.json()["conversation_id"] == conversation_id

    continued = client.get(f"/api/v1/cerebro/conversations/{conversation_id}", headers=headers)
    assert continued.status_code == 200
    continued_messages = continued.json()["messages"]
    assert len(continued_messages) == 4
    assert continued_messages[0]["content"] == "Hola CEREBRO, esta conversacion debe guardarse."
    assert continued_messages[2]["content"] == "Segundo mensaje: no reinicies el historial."
