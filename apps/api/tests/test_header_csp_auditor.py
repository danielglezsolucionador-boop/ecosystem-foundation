from contextlib import contextmanager
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from threading import Thread

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.schemas.auth import ControlCenterRole
from app.schemas.header_audit import HeaderAuditClassification
from app.services import header_csp_auditor as auditor
from app.services.arsenal import seed_initial_core_resources
from app.services.cerebro import list_commercial_drafts, list_cerebro_tasks
from auth_helpers import auth_headers


client = TestClient(app)
CEO_HEADERS = auth_headers(client, ControlCenterRole.ceo)


class DefensiveHeaderHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_HEAD(self) -> None:
        self.send_response(200)
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; object-src 'none'; base-uri 'self'; "
            "frame-ancestors 'none'",
        )
        self.send_header("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header(
            "Permissions-Policy",
            "camera=(), microphone=(), geolocation=()",
        )
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, _format: str, *_args: object) -> None:
        return None


@contextmanager
def local_header_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), DefensiveHeaderHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}/headers"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_header_csp_auditor_runs_against_loopback_and_returns_json_markdown() -> None:
    tasks_before = {item.id for item in list_cerebro_tasks()}
    drafts_before = {item.id for item in list_commercial_drafts()}
    resources_before = client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
    ).json()

    with local_header_server() as url:
        response = client.post(
            "/api/v1/arsenal/tools/header-csp-auditor/analyze",
            headers=CEO_HEADERS,
            json={
                "url": url,
                "mode": "localhost",
                "requesting_office": "CENTINELA",
                "event_metadata": {
                    "event_id": "local-header-audit-test",
                    "source": "pytest",
                    "classification": "OPERATIVO_DEFENSIVO",
                },
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["resource_id"] == "arsenal-tool-header-csp-auditor"
    assert payload["resource_version"] == "1.0.0"
    assert payload["mode"] == "localhost"
    assert payload["request_method"] == "HEAD"
    assert payload["network_request_executed"] is True
    assert payload["secrets_stored"] is False
    assert payload["event_metadata"]["event_id"] == "local-header-audit-test"
    assert payload["overall_classification"] == "pendiente_evidencia"

    json_text = json.dumps(payload["json_output"], ensure_ascii=False)
    normalized_json = json.loads(json_text)
    assert normalized_json["report_id"] == payload["id"]
    assert normalized_json["target"]["mode"] == "localhost"
    assert normalized_json["classification"] == "pendiente_evidencia"

    markdown = payload["markdown_output"]
    assert markdown.startswith("# Header/CSP Auditor")
    assert "## Hallazgos" in markdown
    assert "Referrer-Policy" in markdown
    assert "no guarda secretos" in markdown

    finding_headers = {finding["header"] for finding in payload["findings"]}
    assert finding_headers == {
        "Content-Security-Policy",
        "Strict-Transport-Security",
        "X-Frame-Options",
        "X-Content-Type-Options",
        "Referrer-Policy",
        "Permissions-Policy",
        "Access-Control-Allow-Origin",
    }

    stored = client.get(
        f"/api/v1/arsenal/tools/header-csp-auditor/results/{payload['id']}",
        headers=CEO_HEADERS,
    )
    assert stored.status_code == 200
    assert stored.json()["id"] == payload["id"]

    assert {item.id for item in list_cerebro_tasks()} == tasks_before
    assert {item.id for item in list_commercial_drafts()} == drafts_before
    assert client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
    ).json() == resources_before


def test_missing_headers_are_defensive_or_pending_evidence() -> None:
    findings = auditor.analyze_headers(
        {},
        final_url="https://example.test/",
        http_status=200,
    )

    assert findings
    assert {
        finding.classification for finding in findings
    } <= {
        HeaderAuditClassification.defensive,
        HeaderAuditClassification.pending_evidence,
    }
    assert next(
        finding
        for finding in findings
        if finding.header == "Access-Control-Allow-Origin"
    ).classification == HeaderAuditClassification.defensive
    assert next(
        finding
        for finding in findings
        if finding.header == "Content-Security-Policy"
    ).classification == HeaderAuditClassification.pending_evidence


def test_risky_header_values_are_flagged_for_potential_review() -> None:
    findings = auditor.analyze_headers(
        {
            "Content-Security-Policy": "default-src *; script-src 'unsafe-inline'",
            "Referrer-Policy": "unsafe-url",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Credentials": "true",
        },
        final_url="https://example.test/",
        http_status=200,
    )
    by_header = {finding.header: finding for finding in findings}

    assert (
        by_header["Content-Security-Policy"].classification
        == HeaderAuditClassification.potential_review
    )
    assert (
        by_header["Referrer-Policy"].classification
        == HeaderAuditClassification.potential_review
    )
    assert (
        by_header["Access-Control-Allow-Origin"].classification
        == HeaderAuditClassification.potential_review
    )


def test_scope_guards_reject_credentials_queries_and_private_external_targets() -> None:
    with pytest.raises(auditor.HeaderAuditError) as credentials_error:
        auditor._normalized_url("https://user:password@example.test/")
    assert (
        credentials_error.value.detail["error"]
        == "header_audit_embedded_credentials_rejected"
    )

    with pytest.raises(auditor.HeaderAuditError) as query_error:
        auditor._normalized_url("https://example.test/?token=not-stored")
    assert (
        query_error.value.detail["error"]
        == "header_audit_query_or_fragment_rejected"
    )

    with pytest.raises(auditor.HeaderAuditError) as port_error:
        auditor._validate_scope(
            "https://example.test:444/",
            auditor.HeaderAuditMode.authorized_scope,
            "ticket:SEC-122",
        )
    assert (
        port_error.value.detail["error"]
        == "header_audit_external_port_rejected"
    )

    request = auditor.HeaderAuditRequest(
        url="http://127.0.0.1/",
        mode="authorized_scope",
        requesting_office="CENTINELA",
        authorization_reference="ticket:SEC-123",
    )
    with pytest.raises(auditor.HeaderAuditError) as private_error:
        auditor.run_header_audit(request)
    assert (
        private_error.value.detail["error"]
        == "header_audit_non_public_target_rejected"
    )


def test_cerebro_reads_saved_header_results_without_operational_side_effects(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        auditor,
        "_validate_scope",
        lambda *_args, **_kwargs: ("https://example.test/", "example.test"),
    )
    monkeypatch.setattr(
        auditor,
        "_fetch_headers",
        lambda _request: (
            "https://example.test/",
            "example.test",
            200,
            "HEAD",
            {"referrer-policy": "no-referrer"},
        ),
    )
    created = client.post(
        "/api/v1/arsenal/tools/header-csp-auditor/analyze",
        headers=CEO_HEADERS,
        json={
            "url": "https://example.test/",
            "mode": "authorized_scope",
            "requesting_office": "AUDITORIA",
            "authorization_reference": "ticket:SEC-456",
        },
    )
    assert created.status_code == 200

    tasks_before = {item.id for item in list_cerebro_tasks()}
    drafts_before = {item.id for item in list_commercial_drafts()}
    resources_before = client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
    ).json()
    reports_before = {
        report.id for report in auditor.list_header_audits(limit=100)
    }

    response = client.post(
        "/api/v1/cerebro/chat",
        headers=CEO_HEADERS,
        json={"message": "resultados header csp"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["provider"] == "internal"
    assert payload["actions"][0]["type"] == "header_audit_results"
    assert payload["used_context"]["header_audit_read_only"] is True
    assert "HEADER/CSP AUDITOR: PASS" in payload["reply"]
    assert "sin ejecutar nuevos escaneos" in payload["reply"]
    assert {item.id for item in list_cerebro_tasks()} == tasks_before
    assert {item.id for item in list_commercial_drafts()} == drafts_before
    assert client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
    ).json() == resources_before
    assert {
        report.id for report in auditor.list_header_audits(limit=100)
    } == reports_before


def test_header_csp_resource_is_promoted_without_duplication() -> None:
    seed_initial_core_resources()
    seed_initial_core_resources()

    resources = client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
    ).json()
    matches = [
        resource
        for resource in resources
        if resource["id"] == "arsenal-tool-header-csp-auditor"
    ]
    sombra_resources = client.get(
        "/api/v1/arsenal/resources",
        headers=CEO_HEADERS,
        params={"office": "SOMBRA"},
    ).json()

    assert len(matches) == 1
    assert matches[0]["status"] == "active"
    assert matches[0]["readiness"] == "operational_defensive"
    assert matches[0]["available_for_sombra"] is True
    assert matches[0]["secrets_stored"] is False
    assert {resource["name"] for resource in sombra_resources} == {
        "Header/CSP Auditor",
        "Sombra Toolbelt",
    }
