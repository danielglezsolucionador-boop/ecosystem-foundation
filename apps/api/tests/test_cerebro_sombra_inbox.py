from datetime import UTC, datetime
import json
from uuid import uuid4

from fastapi.testclient import TestClient

import app.services.cerebro as cerebro_service
from app.main import app
from app.schemas.auth import ControlCenterRole
from app.services.arsenal import get_catalog_item
from app.services.audit import list_audit_events
from app.services.bunker_vault import list_sealed_reports
from app.services.cerebro import list_commercial_drafts, list_cerebro_tasks, list_sombra_inbox_messages
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
                "paid_programs": ["Bitso", "HostGator LATAM", "Nubank", "QuintoAndar"],
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
    assert report_payload["used_context"]["productive_classification"] == "PENDIENTE_EVIDENCIA"
    assert report_payload["used_context"]["audit_event_id"]
    for section in ("dinero:", "informes:", "forja:", "linkedin:", "centinela:", "auditoria:", "decision ceo:"):
        assert section in reply
    assert "bitso" in reply
    assert "hostgator latam" in reply
    assert "nubank" in reply
    assert "quintoandar" in reply
    assert "programas analizados: 4" in reply
    assert "programas pagados: 4" in reply
    assert "senales detectadas: 3" in reply
    assert "coincidencias: 0" in reply
    assert "matches cantidad: 0" in reply
    assert "oportunidades reportables: 0" in reply
    assert "no hay plata reclamable todavia" in reply
    assert "puedo ayudarte a revisar reportes si me los envias" not in reply
    assert "sin empresa vulnerable" in reply
    assert "sin endpoint" in reply
    assert "sin explotacion" in reply
    assert "sin datos sensibles" in reply

    bounty_question = client.post(
        "/api/v1/cerebro/chat",
        json={"message": "Hay plata para reclamar por bug bounty?"},
        headers=CEO_HEADERS,
    )
    assert bounty_question.status_code == 200
    bounty_reply = bounty_question.json()["reply"].lower()
    assert "no hay plata reclamable todavia" in bounty_reply
    assert "no registra oportunidades reportables confirmadas" in bounty_reply

    explicit_centinela_question = client.post(
        "/api/v1/cerebro/chat",
        json={
            "message": "Consulta el ultimo escaneo del sistema discreto SOMBRA.",
            "action": "centinela",
        },
        headers=CEO_HEADERS,
    )
    assert explicit_centinela_question.status_code == 200
    explicit_payload = explicit_centinela_question.json()
    assert explicit_payload["actions"][0]["type"] == "sombra_inbox_reviewed"
    assert explicit_payload["used_context"]["used_sombra_context"] is True


def test_sombra_reportable_bug_bounty_generates_private_ceo_outputs(monkeypatch) -> None:
    monkeypatch.setattr(cerebro_service, "generate_cerebro_reply", lambda **_kwargs: None)
    token = enable_sombra_inbox(monkeypatch)
    message = sample_message(
        type="scan_report",
        severity="high",
        title="Bug bounty reportable scope match",
        summary="SOMBRA detecto oportunidad reportable en programa pagado con evidencia pendiente de revision CEO.",
        audience=["cerebro", "centinela", "forja"],
        payload={
            "scan_summary": {
                "programs_analyzed": 2,
                "paid_programs": ["Programa Pagado Uno"],
                "paid_program_count": 1,
                "matches": 1,
                "reportable_opportunities": 1,
                "reportable_items": ["hallazgo privado sanitizado para revision CEO"],
                "next_step": "Daniel revisa evidencia privada y sube manualmente el informe al programa.",
            }
        },
        metadata={"case": "reportable-bug-bounty"},
    )

    stored = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stored.status_code == 200

    response = client.post(
        "/api/v1/cerebro/chat",
        json={"message": "Hay plata para reclamar por bug bounty?"},
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    reply = payload["reply"].lower()
    assert payload["used_context"]["productive_classification"] == "INFORME_BUG_BOUNTY"
    assert payload["used_context"]["ready_reports"] == 1
    assert "informes listos para revision del ceo" in reply
    assert "informe(s) privado(s) listo(s)" in reply
    assert "daniel revisa evidencia privada" in reply
    assert "sin publicacion automatica" in reply
    assert "payload sensible retenido" in reply


def test_sombra_operational_defensive_report_runs_double_channel_operational_flow(monkeypatch) -> None:
    monkeypatch.setattr(cerebro_service, "generate_cerebro_reply", lambda **_kwargs: None)
    token = enable_sombra_inbox(monkeypatch)
    message = sample_message(
        classification="OPERATIVO_DEFENSIVO",
        type="scan_report",
        severity="high",
        title="Reporte operativo defensivo para regla API skill",
        summary=(
            "CENTINELA debe evaluar una regla defensiva, preparar API interna, skill y herramienta "
            "sin publicar endpoints ni tocar proveedores."
        ),
        audience=["cerebro"],
        safe_for_commercial_use=True,
        metadata={
            "case": "double-channel-operational",
            "requires_api": True,
            "requires_skill": True,
            "requires_tool": True,
            "requires_defensive_rule": True,
        },
    )

    response = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["classification"] == "OPERATIVO_DEFENSIVO"
    assert payload["sealed"] is False
    assert "centinela" in payload["routed_to"]
    actions = {action["type"]: action for action in payload["internal_actions"]}
    assert "centinela_analysis_created" in actions
    assert actions["centinela_analysis_created"]["requires_forja_task"] == "true"
    assert "forja_task_created" in actions
    assert "arsenal_artifact_registered" in actions
    assert "commercial_draft_created" in actions
    assert "auditoria_flow_registered" in actions

    task_id = actions["forja_task_created"]["id"]
    task = next(item for item in list_cerebro_tasks() if item.id == task_id)
    assert task.destination == "forja"
    assert "CENTINELA" in task.description

    artifact = get_catalog_item(actions["arsenal_artifact_registered"]["id"])
    assert artifact.metadata["message_id"] == message["message_id"]
    assert artifact.metadata["content_included"] is False
    assert artifact.item_type in {"api", "skill", "herramienta", "regla_reutilizable"}

    draft = next(item for item in list_commercial_drafts() if item.id == actions["commercial_draft_created"]["id"])
    assert draft.source == "sombra_operativo_defensivo"
    assert draft.source_message_id == message["message_id"]
    assert draft.status == "prepared_pending_ceo_approval"
    assert draft.requires_ceo_approval is True
    assert draft.publish_allowed is False

    audit = next(event for event in list_audit_events() if event.id == actions["auditoria_flow_registered"]["id"])
    assert audit.action == "sombra_operational_report_flow"
    assert audit.metadata["destination"] == "centinela_forja_arsenal_pluma_auditoria"


def test_trace_event_returns_exact_trace_without_local_path_or_prompt_side_effects(monkeypatch) -> None:
    monkeypatch.setattr(cerebro_service, "generate_cerebro_reply", lambda **_kwargs: None)
    token = enable_sombra_inbox(monkeypatch)
    message_id = f"bug-bounty-hunter-20260618T123146Z-09c6fa327386-{uuid4().hex[:8]}"
    message = sample_message(
        message_id=message_id,
        classification="OPERATIVO_DEFENSIVO",
        type="scan_report",
        severity="medium",
        title="Bug bounty hunter opportunities",
        summary=(
            "SOMBRA genero un informe operativo de oportunidades bug bounty. "
            "No hay construccion tecnica solicitada por CENTINELA."
        ),
        audience=["cerebro", "centinela", "bunker"],
        safe_for_commercial_use=False,
        metadata={
            "case": "trace-event",
            "report_path": r"C:\Users\admin\Documents\CENTINELA\reportes\bugbounty\opportunities_2026-06-18.pdf",
        },
    )

    stored = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stored.status_code == 200

    tasks_before = {item.id for item in list_cerebro_tasks()}
    drafts_before = {item.id for item in list_commercial_drafts()}

    response = client.post(
        "/api/v1/cerebro/chat",
        json={
            "message": (
                f"CEREBRO, con el evento {message_id} responde solo trazabilidad: "
                "BUNKER / CENTINELA / FORJA / ARSENAL / LINKEDIN / AUDITORIA."
            )
        },
        headers=CEO_HEADERS,
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["actions"][0]["type"] == "event_trace"
    assert payload["used_context"]["intent_detected"] == "event_trace"
    assert "dinero:" not in payload["reply"].lower()
    trace = json.loads(payload["reply"])
    assert list(trace.keys()) == list(cerebro_service.EVENT_TRACE_FIELDS)
    assert trace["message_id"] == message_id
    assert trace["source"] == "sombra"
    assert trace["classification"] == "OPERATIVO_DEFENSIVO"
    assert trace["bunker_status"] == "si"
    assert trace["bunker_id"]
    assert trace["bunker_path_or_key"].startswith("BUNKER/SOMBRA/")
    assert r"C:\Users\admin" not in trace["bunker_path_or_key"]
    assert "opportunities_2026-06-18.pdf" not in trace["bunker_path_or_key"]
    assert trace["centinela_status"] == "si"
    assert trace["centinela_alert_id"]
    assert trace["audit_status"] == "si"
    assert trace["audit_id"]
    assert trace["forja_status"] == "no aplica"
    assert trace["forja_task_id"] is None
    assert trace["arsenal_status"] == "no aplica"
    assert trace["arsenal_artifact_id"] is None
    assert trace["linkedin_status"] == "no aplica"
    assert trace["draft_id"] is None
    assert trace["missing_steps"] == []

    direct_trace = cerebro_service.trace_event(message_id)
    assert direct_trace == trace
    endpoint = client.get(f"/api/v1/cerebro/events/{message_id}/trace", headers=CEO_HEADERS)
    assert endpoint.status_code == 200
    assert endpoint.json() == trace

    assert {item.id for item in list_cerebro_tasks()} == tasks_before
    assert {item.id for item in list_commercial_drafts()} == drafts_before


def test_sombra_secret_military_ceo_report_is_sealed_without_cerebro_reading(monkeypatch) -> None:
    token = enable_sombra_inbox(monkeypatch)
    secret_marker = f"ULTRA-SEALED-{uuid4().hex}"

    def fail_if_read(*_args, **_kwargs):
        raise AssertionError("sealed content must not be processed by CEREBRO")

    monkeypatch.setattr(cerebro_service, "apply_cyber_intelligence_protocol", fail_if_read)
    monkeypatch.setattr(cerebro_service, "route_sombra_message", fail_if_read)
    monkeypatch.setattr(cerebro_service, "generate_cerebro_reply", fail_if_read)

    message = sample_message(
        classification="SECRETO_MILITAR_CEO",
        type="briefing",
        severity="critical",
        title="Paquete sellado CEO",
        summary=f"Contenido sellado no legible {secret_marker}",
        audience=["cerebro", "centinela", "forja", "pluma", "bunker"],
        payload={"sealed_blob": secret_marker, "do_not_read": True},
        metadata={"filename": "sealed-package.bin", "case": "sealed-channel"},
    )

    response = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    body = response.text
    payload = response.json()
    assert payload["classification"] == "SECRETO_MILITAR_CEO"
    assert payload["sealed"] is True
    assert payload["bunker_entry_id"]
    assert payload["routed_to"] == ["bunker"]
    assert payload["executive_summary"] is None
    assert payload["commercial_draft_ready"] is False
    assert payload["manual_review_required"] is True
    assert "sealed_report_archived" in {action["type"] for action in payload["internal_actions"]}
    assert secret_marker not in body

    assert all(item.message_id != message["message_id"] for item in list_sombra_inbox_messages(limit=100))
    sealed = next(item for item in list_sealed_reports(limit=100) if item.original_message_id == message["message_id"])
    assert sealed.id == payload["bunker_entry_id"]
    assert sealed.status == "SELLADO"
    assert sealed.access == "CEO_ONLY"
    assert sealed.vault_path.startswith("BUNKER/SOMBRA/")
    assert len(sealed.content_sha256) == 64
    assert sealed.content_size_bytes > 0
    assert sealed.metadata["content_indexed"] is False
    assert sealed.metadata["llm_allowed"] is False
    assert sealed.metadata["embeddings_allowed"] is False
    assert sealed.metadata["routed_to_centinela"] is False
    assert sealed.metadata["routed_to_forja"] is False
    assert sealed.metadata["routed_to_pluma"] is False
    assert secret_marker not in sealed.model_dump_json()

    audit_text = "\n".join(event.model_dump_json() for event in list_audit_events())
    assert payload["bunker_entry_id"] in audit_text
    assert secret_marker not in audit_text


def test_bunker_sealed_reports_are_ceo_only_metadata_and_status_can_change(monkeypatch) -> None:
    token = enable_sombra_inbox(monkeypatch)
    message = sample_message(
        classification="SECRETO_MILITAR_CEO",
        message_id=f"sombra_sealed_status_{uuid4().hex}",
        title="Paquete sellado para cambio de estado",
        summary="Contenido reservado exclusivamente para CEO.",
        audience=["bunker"],
        payload={"sealed_blob": f"private-{uuid4().hex}"},
    )
    stored = client.post(
        "/api/v1/cerebro/inbox/sombra",
        json=message,
        headers={"Authorization": f"Bearer {token}"},
    )
    assert stored.status_code == 200
    report_id = stored.json()["bunker_entry_id"]

    operator_headers = auth_headers(client, ControlCenterRole.operator)
    denied = client.get("/api/v1/cerebro/bunker/sombra/sealed", headers=operator_headers)
    assert denied.status_code == 403

    listed = client.get("/api/v1/cerebro/bunker/sombra/sealed?limit=20", headers=CEO_HEADERS)
    assert listed.status_code == 200
    report = next(item for item in listed.json() if item["id"] == report_id)
    assert report["status"] == "SELLADO"
    assert report["access"] == "CEO_ONLY"
    assert "content" not in report
    assert "payload" not in report
    assert report["vault_path"].count("/") >= 3

    updated = client.patch(
        f"/api/v1/cerebro/bunker/sombra/sealed/{report_id}",
        json={"status": "COMPARTIR_CON_CEREBRO", "reason": "CEO autoriza revision posterior."},
        headers=CEO_HEADERS,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "COMPARTIR_CON_CEREBRO"
    assert "payload" not in updated.text
    assert "sealed_blob" not in updated.text
    assert str(message["payload"]["sealed_blob"]) not in updated.text
