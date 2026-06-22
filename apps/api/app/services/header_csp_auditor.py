from __future__ import annotations

from datetime import UTC, datetime
from email.message import Message
import ipaddress
import re
import socket
from typing import Mapping
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin, urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.core.safe_data import safe_payload
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.arsenal import ArsenalOffice
from app.schemas.auth import AuthenticatedUser
from app.schemas.header_audit import (
    HeaderAuditClassification,
    HeaderAuditEventMetadata,
    HeaderAuditFinding,
    HeaderAuditMode,
    HeaderAuditReport,
    HeaderAuditRequest,
)
from app.services.audit import create_audit_event


HEADER_AUDIT_TABLE = "arsenal_header_csp_audits"
HEADER_AUDITOR_RESOURCE_ID = "arsenal-tool-header-csp-auditor"
HEADER_AUDITOR_VERSION = "1.0.0"
ALLOWED_OFFICES = {
    ArsenalOffice.cerebro,
    ArsenalOffice.sombra,
    ArsenalOffice.centinela,
    ArsenalOffice.auditoria,
    ArsenalOffice.ceo,
}
REDIRECT_LIMIT = 3


class HeaderAuditError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def ensure_header_audit_schema() -> None:
    initialize_database()
    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {HEADER_AUDIT_TABLE} (
                id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.commit()


def _normalized_url(target_url: str) -> tuple[str, str]:
    raw = str(target_url or "").strip()
    if any(ord(character) < 32 or ord(character) == 127 for character in raw):
        raise HeaderAuditError(
            400,
            {"error": "header_audit_control_character_rejected"},
        )
    try:
        parsed = urlsplit(raw)
        port = parsed.port
    except ValueError as exc:
        raise HeaderAuditError(
            400,
            {"error": "header_audit_url_malformed"},
        ) from exc
    if parsed.scheme.lower() not in {"http", "https"}:
        raise HeaderAuditError(
            400,
            {"error": "header_audit_scheme_not_allowed", "allowed": ["http", "https"]},
        )
    if not parsed.hostname:
        raise HeaderAuditError(400, {"error": "header_audit_host_required"})
    if parsed.username or parsed.password:
        raise HeaderAuditError(400, {"error": "header_audit_embedded_credentials_rejected"})
    if parsed.query or parsed.fragment:
        raise HeaderAuditError(
            400,
            {
                "error": "header_audit_query_or_fragment_rejected",
                "reason": "Use a clean scoped URL without query strings or fragments.",
            },
        )
    host = parsed.hostname.rstrip(".").lower()
    if ":" not in host:
        try:
            host = host.encode("idna").decode("ascii")
        except UnicodeError as exc:
            raise HeaderAuditError(
                400,
                {"error": "header_audit_host_invalid"},
            ) from exc
    netloc = host
    if ":" in host and not host.startswith("["):
        netloc = f"[{host}]"
    if port:
        netloc = f"{netloc}:{port}"
    path = parsed.path or "/"
    return urlunsplit((parsed.scheme.lower(), netloc, path, "", "")), host


def _resolved_addresses(
    host: str,
    port: int,
) -> list[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    try:
        records = socket.getaddrinfo(host, port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise HeaderAuditError(
            422,
            {"error": "header_audit_dns_resolution_failed", "host": host},
        ) from exc
    addresses = []
    for record in records:
        try:
            addresses.append(ipaddress.ip_address(record[4][0]))
        except ValueError:
            continue
    if not addresses:
        raise HeaderAuditError(
            422,
            {"error": "header_audit_dns_resolution_empty", "host": host},
        )
    return list(dict.fromkeys(addresses))


def _validate_scope(
    target_url: str,
    mode: HeaderAuditMode,
    authorization_reference: str | None,
) -> tuple[str, str]:
    normalized_url, host = _normalized_url(target_url)
    parsed = urlsplit(normalized_url)
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    if mode != HeaderAuditMode.localhost and port not in {80, 443}:
        raise HeaderAuditError(
            403,
            {
                "error": "header_audit_external_port_rejected",
                "port": port,
                "allowed": [80, 443],
            },
        )
    addresses = _resolved_addresses(host, port)
    localhost_names = {"localhost", "127.0.0.1", "::1"}

    if mode == HeaderAuditMode.localhost:
        if host not in localhost_names or any(not address.is_loopback for address in addresses):
            raise HeaderAuditError(
                403,
                {"error": "header_audit_localhost_scope_mismatch", "host": host},
            )
        return normalized_url, host

    if not authorization_reference:
        raise HeaderAuditError(
            403,
            {
                "error": "header_audit_authorization_reference_required",
                "mode": mode.value,
            },
        )
    if any(not address.is_global for address in addresses):
        raise HeaderAuditError(
            403,
            {
                "error": "header_audit_non_public_target_rejected",
                "host": host,
                "reason": "Private, link-local, reserved and metadata networks are blocked.",
            },
        )
    return normalized_url, host


def _same_redirect_scope(source_host: str, target_host: str) -> bool:
    return source_host == target_host or target_host.endswith(f".{source_host}")


def _request_once(url: str, method: str, timeout_seconds: float) -> tuple[int, Mapping[str, str], str | None]:
    headers = {
        "User-Agent": f"Ecosystem-Header-CSP-Auditor/{HEADER_AUDITOR_VERSION}",
        "Accept": "*/*",
    }
    if method == "GET":
        headers["Range"] = "bytes=0-0"
    request = Request(url, method=method, headers=headers)
    opener = build_opener(ProxyHandler({}), _NoRedirect())
    try:
        with opener.open(request, timeout=timeout_seconds) as response:
            return int(response.status), response.headers, response.headers.get("Location")
    except HTTPError as exc:
        return int(exc.code), exc.headers or Message(), (exc.headers or {}).get("Location")
    except (URLError, TimeoutError, OSError) as exc:
        raise HeaderAuditError(
            422,
            {
                "error": "header_audit_request_failed",
                "detail": exc.__class__.__name__,
            },
        ) from exc


def _fetch_headers(request: HeaderAuditRequest) -> tuple[str, str, int, str, dict[str, str]]:
    current_url, initial_host = _validate_scope(
        request.url,
        request.mode,
        request.authorization_reference,
    )
    method = "HEAD"
    for redirect_count in range(REDIRECT_LIMIT + 1):
        status_code, response_headers, location = _request_once(
            current_url,
            method,
            request.timeout_seconds,
        )
        if method == "HEAD" and status_code in {405, 501}:
            method = "GET"
            status_code, response_headers, location = _request_once(
                current_url,
                method,
                request.timeout_seconds,
            )
        if status_code not in {301, 302, 303, 307, 308} or not location:
            safe_headers = {
                str(key).lower(): str(value)
                for key, value in response_headers.items()
                if str(key).lower()
                in {
                    "content-security-policy",
                    "content-security-policy-report-only",
                    "strict-transport-security",
                    "x-frame-options",
                    "x-content-type-options",
                    "referrer-policy",
                    "permissions-policy",
                    "access-control-allow-origin",
                    "access-control-allow-credentials",
                }
            }
            return current_url, initial_host, status_code, method, safe_headers
        if redirect_count >= REDIRECT_LIMIT:
            raise HeaderAuditError(422, {"error": "header_audit_redirect_limit"})
        redirected_url = urljoin(current_url, location)
        normalized_redirect, redirect_host = _validate_scope(
            redirected_url,
            request.mode,
            request.authorization_reference,
        )
        if not _same_redirect_scope(initial_host, redirect_host):
            raise HeaderAuditError(
                403,
                {
                    "error": "header_audit_cross_scope_redirect_rejected",
                    "source_host": initial_host,
                    "target_host": redirect_host,
                },
            )
        current_url = normalized_redirect
        method = "HEAD"
    raise HeaderAuditError(422, {"error": "header_audit_request_incomplete"})


def _finding(
    finding_id: str,
    header: str,
    classification: HeaderAuditClassification,
    severity: str,
    summary: str,
    evidence: str,
    recommendation: str,
) -> HeaderAuditFinding:
    return HeaderAuditFinding(
        id=finding_id,
        header=header,
        classification=classification,
        severity=severity,
        summary=summary,
        evidence=evidence,
        recommendation=recommendation,
    )


def _csp_directives(value: str) -> dict[str, list[str]]:
    directives: dict[str, list[str]] = {}
    for segment in value.split(";"):
        parts = segment.strip().split()
        if not parts:
            continue
        directives[parts[0].lower()] = parts[1:]
    return directives


def _analyze_csp(headers: Mapping[str, str]) -> tuple[HeaderAuditFinding, dict[str, list[str]]]:
    enforced = headers.get("content-security-policy", "").strip()
    report_only = headers.get("content-security-policy-report-only", "").strip()
    if not enforced and report_only:
        directives = _csp_directives(report_only)
        return (
            _finding(
                "csp",
                "Content-Security-Policy",
                HeaderAuditClassification.pending_evidence,
                "medium",
                "CSP existe solo en modo report-only.",
                f"directivas report-only: {', '.join(sorted(directives)) or 'ninguna'}",
                "Promover una politica validada a Content-Security-Policy aplicada.",
            ),
            directives,
        )
    if not enforced:
        return (
            _finding(
                "csp",
                "Content-Security-Policy",
                HeaderAuditClassification.pending_evidence,
                "high",
                "No se observo una CSP aplicada.",
                "cabecera ausente",
                "Definir una CSP restrictiva empezando por default-src, script-src, object-src, base-uri y frame-ancestors.",
            ),
            {},
        )
    directives = _csp_directives(enforced)
    source_tokens = [
        token.lower()
        for name in ("default-src", "script-src", "script-src-elem")
        for token in directives.get(name, [])
    ]
    unsafe = sorted(
        {
            token
            for token in source_tokens
            if token in {"'unsafe-inline'", "'unsafe-eval'", "*"}
        }
    )
    if unsafe:
        return (
            _finding(
                "csp",
                "Content-Security-Policy",
                HeaderAuditClassification.potential_review,
                "high",
                "La CSP contiene fuentes de script amplias o inseguras.",
                f"tokens observados: {', '.join(unsafe)}",
                "Reducir comodines y unsafe-*; preferir nonces/hashes y origenes explicitos.",
            ),
            directives,
        )
    missing = [
        directive
        for directive in ("default-src", "object-src", "base-uri", "frame-ancestors")
        if directive not in directives
    ]
    if missing:
        return (
            _finding(
                "csp",
                "Content-Security-Policy",
                HeaderAuditClassification.pending_evidence,
                "medium",
                "La CSP aplicada requiere completar directivas defensivas.",
                f"faltantes: {', '.join(missing)}",
                "Revisar y agregar las directivas faltantes con valores minimos necesarios.",
            ),
            directives,
        )
    return (
        _finding(
            "csp",
            "Content-Security-Policy",
            HeaderAuditClassification.defensive,
            "info",
            "CSP aplicada sin patrones amplios detectados.",
            f"directivas: {', '.join(sorted(directives))}",
            "Mantener pruebas de compatibilidad y revisar cambios de fuentes.",
        ),
        directives,
    )


def _analyze_hsts(headers: Mapping[str, str], scheme: str) -> HeaderAuditFinding:
    value = headers.get("strict-transport-security", "").strip()
    if scheme != "https":
        return _finding(
            "hsts",
            "Strict-Transport-Security",
            HeaderAuditClassification.pending_evidence,
            "medium",
            "HSTS debe evaluarse sobre el endpoint HTTPS final.",
            "objetivo HTTP",
            "Repetir la auditoria sobre HTTPS y confirmar redireccion permanente.",
        )
    if not value:
        return _finding(
            "hsts",
            "Strict-Transport-Security",
            HeaderAuditClassification.pending_evidence,
            "high",
            "No se observo HSTS en HTTPS.",
            "cabecera ausente",
            "Configurar HSTS con max-age suficiente y evaluar includeSubDomains.",
        )
    match = re.search(r"max-age\s*=\s*(\d+)", value, flags=re.IGNORECASE)
    max_age = int(match.group(1)) if match else 0
    include_subdomains = "includesubdomains" in value.lower()
    if max_age < 15552000 or not include_subdomains:
        return _finding(
            "hsts",
            "Strict-Transport-Security",
            HeaderAuditClassification.pending_evidence,
            "medium",
            "HSTS esta presente pero requiere endurecimiento.",
            f"max-age={max_age}; includeSubDomains={str(include_subdomains).lower()}",
            "Evaluar max-age >= 15552000 e includeSubDomains antes de considerar preload.",
        )
    return _finding(
        "hsts",
        "Strict-Transport-Security",
        HeaderAuditClassification.defensive,
        "info",
        "HSTS esta activo con una duracion defensiva.",
        f"max-age={max_age}; includeSubDomains=true",
        "Mantener la politica y revisar cobertura de subdominios.",
    )


def _analyze_x_frame(headers: Mapping[str, str], csp: Mapping[str, list[str]]) -> HeaderAuditFinding:
    value = headers.get("x-frame-options", "").strip().upper()
    if value in {"DENY", "SAMEORIGIN"}:
        return _finding(
            "x_frame_options",
            "X-Frame-Options",
            HeaderAuditClassification.defensive,
            "info",
            "Proteccion anti-framing observada.",
            f"valor: {value}",
            "Mantener alineado con CSP frame-ancestors.",
        )
    if not value and "frame-ancestors" in csp:
        return _finding(
            "x_frame_options",
            "X-Frame-Options",
            HeaderAuditClassification.discarded,
            "info",
            "Ausencia descartada como hallazgo principal por cobertura CSP.",
            "CSP frame-ancestors presente",
            "Mantener frame-ancestors; agregar X-Frame-Options solo por compatibilidad heredada.",
        )
    return _finding(
        "x_frame_options",
        "X-Frame-Options",
        HeaderAuditClassification.pending_evidence,
        "medium",
        "No se observo una proteccion anti-framing valida.",
        f"valor: {value or 'ausente'}",
        "Configurar DENY/SAMEORIGIN o CSP frame-ancestors segun el caso de uso.",
    )


def _analyze_nosniff(headers: Mapping[str, str]) -> HeaderAuditFinding:
    value = headers.get("x-content-type-options", "").strip().lower()
    classification = (
        HeaderAuditClassification.defensive
        if value == "nosniff"
        else HeaderAuditClassification.pending_evidence
    )
    return _finding(
        "x_content_type_options",
        "X-Content-Type-Options",
        classification,
        "info" if classification == HeaderAuditClassification.defensive else "medium",
        "MIME sniffing esta deshabilitado."
        if classification == HeaderAuditClassification.defensive
        else "No se observo nosniff.",
        f"valor: {value or 'ausente'}",
        "Mantener X-Content-Type-Options: nosniff."
        if classification == HeaderAuditClassification.defensive
        else "Configurar X-Content-Type-Options: nosniff.",
    )


def _analyze_referrer_policy(headers: Mapping[str, str]) -> HeaderAuditFinding:
    value = headers.get("referrer-policy", "").strip().lower()
    if not value:
        return _finding(
            "referrer_policy",
            "Referrer-Policy",
            HeaderAuditClassification.pending_evidence,
            "low",
            "No se observo Referrer-Policy.",
            "cabecera ausente",
            "Configurar strict-origin-when-cross-origin, no-referrer u otra politica minima justificada.",
        )
    policies = [item.strip() for item in value.split(",") if item.strip()]
    effective = policies[-1] if policies else ""
    if effective in {"unsafe-url", "no-referrer-when-downgrade"}:
        return _finding(
            "referrer_policy",
            "Referrer-Policy",
            HeaderAuditClassification.potential_review,
            "medium",
            "Referrer-Policy puede exponer mas informacion de navegacion de la necesaria.",
            f"politica efectiva: {effective}",
            "Preferir strict-origin-when-cross-origin o no-referrer segun el caso de uso.",
        )
    return _finding(
        "referrer_policy",
        "Referrer-Policy",
        HeaderAuditClassification.defensive,
        "info",
        "Referrer-Policy esta definida con una politica defensiva.",
        f"politica efectiva: {effective}",
        "Mantener la politica y revisar compatibilidad con flujos legitimos.",
    )


def _analyze_permissions_policy(headers: Mapping[str, str]) -> HeaderAuditFinding:
    value = headers.get("permissions-policy", "").strip()
    if not value:
        return _finding(
            "permissions_policy",
            "Permissions-Policy",
            HeaderAuditClassification.pending_evidence,
            "low",
            "No se observo Permissions-Policy.",
            "cabecera ausente",
            "Definir explicitamente las capacidades de navegador necesarias y deshabilitar el resto.",
        )
    enabled_wildcards = sorted(
        match.group(1)
        for match in re.finditer(r"([a-zA-Z-]+)\s*=\s*\*", value)
    )
    if enabled_wildcards:
        return _finding(
            "permissions_policy",
            "Permissions-Policy",
            HeaderAuditClassification.potential_review,
            "medium",
            "Permissions-Policy habilita capacidades para cualquier origen.",
            f"comodines: {', '.join(enabled_wildcards)}",
            "Limitar las capacidades a self, origenes concretos o listas vacias.",
        )
    features = sorted(
        {
            match.group(1).lower()
            for match in re.finditer(r"(?:^|,)\s*([a-zA-Z-]+)\s*=", value)
        }
    )
    return _finding(
        "permissions_policy",
        "Permissions-Policy",
        HeaderAuditClassification.defensive,
        "info",
        "Permissions-Policy esta definida sin comodines amplios.",
        f"capacidades: {', '.join(features) or 'politica presente'}",
        "Mantener la politica minima y revisar nuevas capacidades del navegador.",
    )


def _analyze_cors(headers: Mapping[str, str]) -> HeaderAuditFinding:
    origin = headers.get("access-control-allow-origin", "").strip()
    credentials = headers.get("access-control-allow-credentials", "").strip().lower() == "true"
    if not origin:
        return _finding(
            "cors",
            "Access-Control-Allow-Origin",
            HeaderAuditClassification.defensive,
            "info",
            "No se observo una exposicion CORS amplia.",
            "cabecera ausente",
            "Mantener CORS deshabilitado salvo necesidad explicita.",
        )
    if origin == "*" and credentials:
        return _finding(
            "cors",
            "Access-Control-Allow-Origin",
            HeaderAuditClassification.potential_review,
            "high",
            "CORS combina origen comodin con credenciales.",
            "origin=*; credentials=true",
            "Eliminar el comodin y usar una allowlist estricta; revisar el comportamiento real del navegador.",
        )
    if origin == "*":
        return _finding(
            "cors",
            "Access-Control-Allow-Origin",
            HeaderAuditClassification.pending_evidence,
            "medium",
            "CORS permite cualquier origen.",
            "origin=*; credentials=false",
            "Confirmar que el recurso es publico y no devuelve datos sensibles; preferir allowlist.",
        )
    return _finding(
        "cors",
        "Access-Control-Allow-Origin",
        HeaderAuditClassification.defensive,
        "info",
        "CORS declara un origen concreto.",
        f"origin={origin[:180]}; credentials={str(credentials).lower()}",
        "Verificar que el origen pertenece al scope autorizado y que no existe reflexion dinamica.",
    )


def analyze_headers(
    headers: Mapping[str, str],
    *,
    final_url: str,
    http_status: int,
) -> list[HeaderAuditFinding]:
    normalized = {str(key).lower(): str(value) for key, value in headers.items()}
    csp_finding, csp_directives = _analyze_csp(normalized)
    findings = [
        csp_finding,
        _analyze_hsts(normalized, urlsplit(final_url).scheme),
        _analyze_x_frame(normalized, csp_directives),
        _analyze_nosniff(normalized),
        _analyze_referrer_policy(normalized),
        _analyze_permissions_policy(normalized),
        _analyze_cors(normalized),
    ]
    if http_status >= 400:
        findings.append(
            _finding(
                "http_status",
                "HTTP status",
                HeaderAuditClassification.pending_evidence,
                "medium",
                "La respuesta no fue exitosa; los headers pueden pertenecer a una pagina de error.",
                f"status={http_status}",
                "Repetir sobre una ruta representativa con respuesta 2xx/3xx dentro del mismo scope.",
            )
        )
    return findings


def _overall_classification(findings: list[HeaderAuditFinding]) -> HeaderAuditClassification:
    priority = (
        HeaderAuditClassification.potential_review,
        HeaderAuditClassification.pending_evidence,
        HeaderAuditClassification.defensive,
        HeaderAuditClassification.discarded,
    )
    observed = {finding.classification for finding in findings}
    return next(item for item in priority if item in observed)


def normalize_audit_result(
    findings: list[HeaderAuditFinding],
) -> tuple[HeaderAuditClassification, dict[str, int]]:
    overall = _overall_classification(findings)
    counts = {
        classification.value: sum(
            finding.classification == classification for finding in findings
        )
        for classification in HeaderAuditClassification
    }
    return overall, counts


def _markdown(
    *,
    target_url: str,
    final_url: str,
    status_code: int,
    office: ArsenalOffice,
    overall: HeaderAuditClassification,
    findings: list[HeaderAuditFinding],
) -> str:
    lines = [
        "# Header/CSP Auditor",
        "",
        f"- Recurso: `{HEADER_AUDITOR_RESOURCE_ID}` v{HEADER_AUDITOR_VERSION}",
        f"- Oficina solicitante: `{office.value}`",
        f"- Objetivo: `{target_url}`",
        f"- URL final: `{final_url}`",
        f"- HTTP: `{status_code}`",
        f"- Clasificacion general: `{overall.value}`",
        "",
        "## Hallazgos",
        "",
    ]
    for finding in findings:
        lines.extend(
            [
                f"### {finding.header}",
                f"- Clasificacion: `{finding.classification.value}`",
                f"- Severidad: `{finding.severity}`",
                f"- Resumen: {finding.summary}",
                f"- Evidencia: {finding.evidence}",
                f"- Recomendacion: {finding.recommendation}",
                "",
            ]
        )
    lines.extend(
        [
            "## Limites",
            "",
            "- Analisis defensivo de cabeceras HTTP; no explota vulnerabilidades.",
            "- No envia credenciales, no guarda secretos y no publica resultados.",
        ]
    )
    return "\n".join(lines)


def render_audit_markdown(
    *,
    target_url: str,
    final_url: str,
    status_code: int,
    office: ArsenalOffice,
    overall: HeaderAuditClassification,
    findings: list[HeaderAuditFinding],
) -> str:
    return _markdown(
        target_url=target_url,
        final_url=final_url,
        status_code=status_code,
        office=office,
        overall=overall,
        findings=findings,
    )


def render_audit_json(
    *,
    report_id: str,
    target_url: str,
    final_url: str,
    host: str,
    status_code: int,
    mode: HeaderAuditMode,
    event_metadata: HeaderAuditEventMetadata | None,
    overall: HeaderAuditClassification,
    counts: dict[str, int],
    findings: list[HeaderAuditFinding],
) -> dict[str, object]:
    return {
        "report_id": report_id,
        "resource": {
            "id": HEADER_AUDITOR_RESOURCE_ID,
            "version": HEADER_AUDITOR_VERSION,
        },
        "target": {
            "url": target_url,
            "final_url": final_url,
            "host": host,
            "http_status": status_code,
            "mode": mode.value,
        },
        "event_metadata": (
            event_metadata.model_dump(exclude_none=True)
            if event_metadata is not None
            else None
        ),
        "classification": overall.value,
        "classification_counts": counts,
        "findings": [finding.model_dump(mode="json") for finding in findings],
    }


def _save_report(report: HeaderAuditReport) -> None:
    ensure_header_audit_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {HEADER_AUDIT_TABLE} (id, payload_json, created_at)
            VALUES ({placeholder}, {placeholder}, {placeholder})
            """,
            (report.id, report.model_dump_json(), report.created_at),
        )
        connection.commit()


def _report_from_payload(payload: dict) -> HeaderAuditReport:
    return HeaderAuditReport(**payload)


def list_header_audits(limit: int = 20) -> list[HeaderAuditReport]:
    ensure_header_audit_schema()
    placeholder = sql_placeholder()
    safe_limit = max(1, min(int(limit), 100))
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {HEADER_AUDIT_TABLE}
            ORDER BY created_at DESC
            LIMIT {placeholder}
            """,
            (safe_limit,),
        ).fetchall()
    reports: list[HeaderAuditReport] = []
    for row in rows:
        payload = safe_payload(row)
        if payload is None:
            continue
        try:
            reports.append(_report_from_payload(payload))
        except Exception:
            continue
    return reports


def get_header_audit(report_id: str) -> HeaderAuditReport:
    ensure_header_audit_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {HEADER_AUDIT_TABLE} WHERE id = {placeholder}",
            (report_id,),
        ).fetchone()
    payload = safe_payload(row) if row else None
    if payload is None:
        raise HeaderAuditError(
            404,
            {"error": "header_audit_report_not_found", "report_id": report_id},
        )
    return _report_from_payload(payload)


def run_header_audit(
    request: HeaderAuditRequest,
    actor: AuthenticatedUser | None = None,
) -> HeaderAuditReport:
    if request.requesting_office not in ALLOWED_OFFICES:
        raise HeaderAuditError(
            403,
            {
                "error": "header_audit_office_not_authorized",
                "office": request.requesting_office.value,
            },
        )
    target_url, host = _validate_scope(
        request.url,
        request.mode,
        request.authorization_reference,
    )
    final_url, _, status_code, method, headers = _fetch_headers(
        request.model_copy(update={"url": target_url})
    )
    findings = analyze_headers(headers, final_url=final_url, http_status=status_code)
    overall, counts = normalize_audit_result(findings)
    created_at = utc_now()
    report_id = f"header-audit-{uuid4()}"
    markdown_output = render_audit_markdown(
        target_url=target_url,
        final_url=final_url,
        status_code=status_code,
        office=request.requesting_office,
        overall=overall,
        findings=findings,
    )
    json_output = render_audit_json(
        report_id=report_id,
        target_url=target_url,
        final_url=final_url,
        host=host,
        status_code=status_code,
        mode=request.mode,
        event_metadata=request.event_metadata,
        overall=overall,
        counts=counts,
        findings=findings,
    )
    actor_label = actor.email if actor else "internal_service"
    event_metadata = (
        request.event_metadata.model_dump(exclude_none=True)
        if request.event_metadata is not None
        else {}
    )
    audit_event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.security,
            severity=(
                AuditSeverity.high
                if overall == HeaderAuditClassification.potential_review
                else AuditSeverity.info
            ),
            source="arsenal.header_csp_auditor",
            action="header_audit_executed",
            status=overall.value,
            detail="Header/CSP Auditor completed an authorized defensive header review.",
            metadata={
                "actor": actor_label,
                "resource_id": HEADER_AUDITOR_RESOURCE_ID,
                "resource_version": HEADER_AUDITOR_VERSION,
                "requesting_office": request.requesting_office.value,
                "mode": request.mode.value,
                "authorization_reference": request.authorization_reference,
                "event_metadata": event_metadata,
                "host": host,
                "http_status": status_code,
                "finding_count": len(findings),
                "classification_counts": counts,
                "network_request_executed": True,
                "external_connection_enabled": False,
                "runtime_connected": False,
                "secrets_stored": False,
            },
        )
    )
    report = HeaderAuditReport(
        id=report_id,
        resource_id=HEADER_AUDITOR_RESOURCE_ID,
        resource_version=HEADER_AUDITOR_VERSION,
        target_url=target_url,
        final_url=final_url,
        host=host,
        requesting_office=request.requesting_office,
        mode=request.mode,
        authorization_reference=request.authorization_reference,
        event_metadata=request.event_metadata,
        http_status=status_code,
        request_method=method,
        overall_classification=overall,
        findings=findings,
        classification_counts=counts,
        json_output=json_output,
        markdown_output=markdown_output,
        audit_event_id=audit_event.id,
        network_request_executed=True,
        external_connection_enabled=False,
        runtime_connected=False,
        secrets_stored=False,
        created_at=created_at,
    )
    _save_report(report)
    return report
