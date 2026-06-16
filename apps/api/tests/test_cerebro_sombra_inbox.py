from datetime import UTC, datetime
from uuid import uuid4

from fastapi.testclient import TestClient

import app.services.cerebro as cerebro_service
from app.main import app
from app.schemas.auth import ControlCenterRole
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


def sample_message(**overrides: object) -> dict[str, object]:
    payload: dict[str, object] = {
        "message_id": f"sombra_{uuid4().hex}",
        "source": "sombra",
        "type": "alert",
        "severity": "critical",
        "created_at": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        "title": "Credencial expuesta",
        "summary": "Inteligencia entrante para CEREBRO, sin ejecutar acciones externas.",
        "audience": ["cerebro", "centinela", "bunker"],
        "client_context": {
            "company": "Example Corp",
            "domain": "example.test",
            "country": "PE",
            "sector": "finanzas",
        },
        "safe_for_commercial_use": False,
        "sensitive": True,
        "encrypted": True,
        "payload": {"ciphertext": "redacted-for-test"},
        "metadata": {"case": "unit-test"},
    }
    payload.update(overrides)
    return payload


def enable_sombra_inbox(monkeypatch) -> str:
    token = f"test-token-{uuid4()}"
    monkeypatch.setenv("SOMBRA_INBOX_ENABLED", "true")
    monkeypatch.setenv("SOMBRA_TO_CEREBRO_TOKEN", token)
    monkeypatch.delenv("SOMBRA_WEBHOOK_SECRET", raising=False)
    return token


def test_sombra_inbox_disabled_returns_503(monkeypatch) -> None:
    monkeypatch.setenv("SOMBRA_INBOX_ENABLED", "false")
    monkeypatch.setenv("SOMBRA_TO_CEREBRO_TOKEN", "configured-but-disabled")

    response = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=sample_message(),
        headers={"Authorization": "Bearer configured-but-disabled"},
    )

    assert response.status_code == 503
    assert response.json()["detail"]["error"] == "sombra_inbox_disabled"


def test_sombra_inbox_requires_bearer_token(monkeypatch) -> None:
    enable_sombra_inbox(monkeypatch)

    missing = client.post("/api/v1/cerebro/inbox/sombra", json=sample_message())
    invalid = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=sample_message(),
        headers={"Authorization": "Bearer wrong-token"},
    )

    assert missing.status_code == 401
    assert missing.json()["detail"]["error"] == "sombra_inbox_token_missing"
    assert invalid.status_code == 403
    assert invalid.json()["detail"]["error"] == "sombra_inbox_token_invalid"


def test_sombra_inbox_validates_schema(monkeypatch) -> None:
    token = enable_sombra_inbox(monkeypatch)
    bad_payload = sample_message(message_id="not_sombra_prefixed", severity="urgent")

    response = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=bad_payload,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 422


def test_sombra_inbox_stores_and_routes_high_severity_message(monkeypatch) -> None:
    token = enable_sombra_inbox(monkeypatch)
    message = sample_message()

    response = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={
            "Authorization": f"Bearer {token}",
            "X-Sombra-Message-Id": str(message["message_id"]),
            "X-Sombra-Timestamp": "2026-06-11T00:00:00Z",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["received"] is True
    assert payload["message_id"] == message["message_id"]
    assert payload["stored"] is True
    assert payload["routed_to"] == ["cerebro", "centinela", "bunker"]
    assert payload["severity"] == "critical"
    assert payload["ceo_code"] == "A1-PARA-1"
    assert payload["immediate_ceo_attention"] is True
    assert payload["commercial_draft_ready"] is False
    assert payload["manual_review_required"] is False

    recent = client.get("/api/v1/cerebro/inbox/sombra/recent", headers=CEO_HEADERS)
    assert recent.status_code == 200
    stored = next(item for item in recent.json() if item["message_id"] == message["message_id"])
    assert stored["payload_redacted"] is True
    assert stored["payload_type"] == "object"
    assert "payload" not in stored
    assert stored["routed_to"] == ["cerebro", "centinela", "bunker"]
    assert stored["safe_for_commercial_use"] is False
    assert stored["sensitive"] is True
    assert stored["metadata"]["case"] == "unit-test"
    assert stored["metadata"]["source_hidden_from_clients"] is True

    centinela = client.get("/api/v1/centinela/status", headers=CEO_HEADERS)
    assert centinela.status_code == 200
    centinela_payload = centinela.json()
    assert centinela_payload["sombra_connected"] is True
    assert centinela_payload["external_intel_messages"] >= 1
    assert centinela_payload["critical_alerts"] >= 1
    assert centinela_payload["threat_level"] == "critical"
    assert "No consulta servidor SOMBRA real" in centinela_payload["message"]


def test_sombra_inbox_rejects_header_message_id_mismatch(monkeypatch) -> None:
    token = enable_sombra_inbox(monkeypatch)

    response = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=sample_message(),
        headers={
            "Authorization": f"Bearer {token}",
            "X-Sombra-Message-Id": "sombra_different",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "sombra_message_id_mismatch"


def test_sombra_inbox_recent_requires_internal_auth() -> None:
    response = client.get("/api/v1/cerebro/inbox/sombra/recent")

    assert response.status_code == 401


def test_sombra_lead_signal_creates_sanitized_commercial_route(monkeypatch) -> None:
    token = enable_sombra_inbox(monkeypatch)
    message = sample_message(
        type="lead_signal",
        severity="medium",
        title="Senal defensiva de mercado",
        summary="Prospecto podria requerir diagnostico defensivo sin revelar fuentes.",
        audience=["cerebro"],
        safe_for_commercial_use=True,
        metadata={
            "case": "lead-test",
            "api_key": "must-not-leak",
            "nested": {"password": "must-not-leak"},
        },
    )

    response = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert "pluma" in payload["routed_to"]
    assert "marketing" in payload["routed_to"]

    recent = client.get("/api/v1/cerebro/inbox/sombra/recent", headers=CEO_HEADERS)
    assert recent.status_code == 200
    stored = next(item for item in recent.json() if item["message_id"] == message["message_id"])
    assert stored["type"] == "lead_signal"
    assert stored["safe_for_commercial_use"] is True
    assert stored["metadata"]["api_key"] == "[redacted]"
    assert stored["metadata"]["nested"]["password"] == "[redacted]"
    assert "payload" not in stored


def test_sombra_bug_bounty_report_is_idempotent_and_used_by_cerebro(monkeypatch) -> None:
    monkeypatch.setattr(cerebro_service, "generate_cerebro_reply", lambda **_kwargs: None)
    token = enable_sombra_inbox(monkeypatch)
    message = sample_message(
        type="scan_report",
        severity="medium",
        title="Bug bounty passive scope scan",
        summary=(
            "SOMBRA detecto programas pagados y senales locales; "
            "sin coincidencias confirmadas ni oportunidades reportables."
        ),
        audience=["cerebro", "centinela"],
        payload={
            "scan_summary": {
                "programs_analyzed": 4,
                "local_signal_count": 3,
                "matches": 0,
                "reportable_opportunities": 0,
                "program_names": ["Bitso", "HostGator LATAM", "Nubank", "QuintoAndar"],
                "local_signals": [
                    "cabecera desactualizada en activo local",
                    "subdominio historico sin match de scope",
                ],
                "scope_signal_matches": [],
                "next_step": (
                    "Cruzar senales con scope autorizado de Bitso, HostGator LATAM, "
                    "Nubank y QuintoAndar."
                ),
            }
        },
        metadata={"case": "bug-bounty-context"},
    )

    first = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={"Authorization": f"Bearer {token}"},
    )
    duplicate = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert first.status_code == 200
    assert duplicate.status_code == 200
    assert first.json()["stored"] is True
    assert duplicate.json()["stored"] is True

    recent = client.get("/api/v1/cerebro/inbox/sombra/recent?limit=100", headers=CEO_HEADERS)
    assert recent.status_code == 200
    stored = [item for item in recent.json() if item["message_id"] == message["message_id"]]
    assert len(stored) == 1

    latest_report = client.post(
        "/api/v1/cerebro/chat",
        json={"message": "CEREBRO, que dice el ultimo reporte de SOMBRA?"},
        headers=CEO_HEADERS,
    )
    assert latest_report.status_code == 200
    report_payload = latest_report.json()
    reply = report_payload["reply"].lower()
    assert report_payload["used_context"]["used_sombra_context"] is True
    assert report_payload["used_context"]["sombra_latest_message_id"] == message["message_id"]
    assert "bitso" in reply
    assert "hostgator latam" in reply
    assert "nubank" in reply
    assert "quintoandar" in reply
    assert "programas analizados: 4" in reply
    assert "senales detectadas: 3" in reply
    assert "coincidencias: 0" in reply
    assert "oportunidades reportables: 0" in reply
    assert "no hay plata reclamable todavia" in reply
    assert "puedo ayudarte a revisar reportes si me los envias" not in reply

    bounty_question = client.post(
        "/api/v1/cerebro/chat",
        json={"message": "Hay plata para reclamar por bug bounty?"},
        headers=CEO_HEADERS,
    )
    assert bounty_question.status_code == 200
    bounty_reply = bounty_question.json()["reply"].lower()
    assert "no hay plata reclamable todavia" in bounty_reply
    assert "no registra oportunidades reportables confirmadas" in bounty_reply
