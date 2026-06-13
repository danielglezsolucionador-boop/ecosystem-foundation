from datetime import UTC, datetime
import hashlib
import hmac
import json
from os import environ
from uuid import uuid4
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.core.database import connect, get_database_backend, get_row_value, initialize_database, sql_placeholder
from app.core.safe_data import SAFE_FALLBACK_MESSAGE, safe_payload
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser, ControlCenterRole, UserStatus
from app.schemas.cerebro import (
    CerebroAlert,
    CerebroAlertCreate,
    CerebroApprovalActionRequest,
    CerebroApprovalRequest,
    CerebroApprovalRequestCreate,
    CerebroAuthorityLevel,
    CerebroAuthorityRule,
    CerebroChatAction,
    CerebroChatRequest,
    CerebroChatResponse,
    CerebroChatState,
    CerebroCheckpoint,
    CerebroChiefOfStaffStatus,
    CerebroCommercialDraft,
    CerebroCommercialDraftCreate,
    CerebroCompanyGoal,
    CerebroCompanyGoalCreate,
    CerebroDailyBrief,
    CerebroDafo,
    CerebroDecision,
    CerebroDecisionCreate,
    CerebroDepartmentGoal,
    CerebroDepartmentGoalCreate,
    CerebroEconomicMatrix,
    CerebroMission,
    CerebroMissionCreate,
    CerebroMissionDispatchRequest,
    CerebroMissionState,
    CerebroMissionStep,
    CerebroMissionUpdate,
    CerebroMissionUpdateCreate,
    CerebroRevenueOpportunity,
    CerebroRevenueOpportunityCreate,
    CerebroState,
    CerebroStatus,
    CerebroTask,
    CerebroTaskCreate,
    CerebroTaskStateUpdate,
    SombraInboxMessageCreate,
    SombraInboxMessageResponse,
    SombraInboxRecentMessage,
)
from app.schemas.integration_bus import IntegrationDispatchRequest
from app.services.audit import create_audit_event
from app.services.centinela import get_centinela_status
from app.services.integration_bus import dispatch_message, route_id_for_cerebro_target

CEREBRO_DECISIONS_TABLE = "cerebro_decisions"
CEREBRO_TASKS_TABLE = "cerebro_tasks"
CEREBRO_COMPANY_GOALS_TABLE = "cerebro_company_goals"
CEREBRO_DEPARTMENT_GOALS_TABLE = "cerebro_department_goals"
CEREBRO_MISSIONS_TABLE = "cerebro_missions"
CEREBRO_MISSION_STEPS_TABLE = "cerebro_mission_steps"
CEREBRO_MISSION_UPDATES_TABLE = "cerebro_mission_updates"
CEREBRO_ALERTS_TABLE = "cerebro_alerts"
CEREBRO_REVENUE_TABLE = "cerebro_revenue_opportunities"
CEREBRO_APPROVAL_REQUESTS_TABLE = "cerebro_approval_requests"
CEREBRO_PRIORITY_CHANGES_TABLE = "cerebro_priority_changes"
CEREBRO_CEO_CHECKPOINTS_TABLE = "cerebro_ceo_checkpoints"
CEREBRO_SOMBRA_INBOX_TABLE = "cerebro_sombra_inbox"
CEREBRO_COMMERCIAL_DRAFTS_TABLE = "cerebro_commercial_drafts"

PERU_TZ = ZoneInfo("America/Lima")
GLOBAL_MONTHLY_GOAL_USD = 6000.0
ECOMMERCE_MONTHLY_GOAL_USD = 10000.0

CEREBRO_CYBER_INTELLIGENCE_POLICY = {
    "name": "CEREBRO Cyber Intelligence Core",
    "ceo_codes": {
        "critical": "A1-PARA-1",
        "high": "A2-PARA-1",
    },
    "fallback": (
        "Recibi informacion de inteligencia que requiere revision manual. "
        "CEO: revisar bandeja de Sombra."
    ),
    "vocabulary": {
        "CVE": "Vulnerabilidad conocida en software.",
        "Ransomware": "Ataque que secuestra o cifra datos para exigir pago.",
        "Credential exposure": "Contrasenas, accesos o credenciales filtradas.",
        "Zero day": "Vulnerabilidad activa sin parche disponible.",
        "Threat actor": "Grupo o persona atacante.",
        "Dark web": (
            "Zona no indexada de internet donde pueden circular datos robados, "
            "accesos filtrados o mercados ilegales."
        ),
    },
    "guardrails": [
        "No ejecutar acciones ofensivas.",
        "No exponer payload sensible completo.",
        "No publicar automaticamente.",
        "No contactar clientes automaticamente.",
        "No consultar servidor externo desde CEREBRO.",
    ],
}

NO_APPROVAL_REQUIRED_ACTIONS = {
    "local_agent_activation": "Permitido por politica del Chief of Staff; en Bloque H queda preparado, sin activar runtime real.",
    "organic_post_configured_account": "Publicacion organica en cuenta oficial ya configurada; sin gasto ni cuenta nueva.",
    "send_task_to_forja": "Delegacion interna a FORJA preparada, con auditoria y sin tocar FORJA externa.",
    "change_strategic_priority": "CEREBRO puede cambiar prioridad diaria si no implica gasto real.",
    "create_internal_mission": "Mision interna preparada para mover departamentos.",
    "request_audit_report": "AUDITORIA puede recibir solicitud interna sin conexion externa.",
    "prepare_product": "Preparacion de producto sin venta real ni pago.",
    "controlled_production_deploy": "Deploy controlado permitido por politica con backup, tests, auditoria y trazabilidad; no ejecutado por este bloque.",
    "governed_update_dcft": "DCFT puede recibir actualizacion gobernada/preparada; sin SUNAT real ni runtime externo.",
    "governed_update_sentinela": "SENTINELA puede recibir actualizacion gobernada/preparada; sin runtime productivo.",
}

CEO_APPROVAL_REQUIRED_ACTIONS = {
    "real_money_payment": "Implica dinero real.",
    "paid_campaign": "Implica pauta pagada.",
    "contract_service": "Implica contrato o servicio externo.",
    "paid_api": "Implica API o herramienta pagada.",
    "new_official_external_account": "Implica crear cuenta oficial externa.",
    "sensitive_credentials": "Implica credenciales sensibles.",
    "legal_tax_high_risk": "Implica riesgo legal, tributario o reputacional alto.",
    "activate_sunat": "SUNAT real requiere aprobacion CEO y frente DCFT separado.",
}

PROTECTED_DESTINATIONS = {
    "doctor_contable_financiero_tributario": "DCFT",
    "centinela": "SENTINELA",
    "arsenal": "ARSENAL",
}

ALLOWED_DESTINATIONS = {
    "forja": "FORJA",
    "hermes": "HERMES",
    "creador_de_apis_y_skills": "CREADOR DE APIS Y SKILLS",
    "web_factory": "WEB FACTORY",
    "buscador_de_tendencias": "BUSCADOR DE TENDENCIAS",
    "pluma": "PLUMA",
    "lente": "LENTE",
    "marketing": "MARKETING",
    "marca_personal": "MARCA PERSONAL",
    "auditor": "AUDITORIA",
    "nube": "NUBE",
    "sniff_amazon": "SNIFF AMAZON",
    "comercio_autonomo": "COMERCIO AUTONOMO",
}

DESTINATION_ALIASES = {
    "auditoria": "auditor",
    "auditoría": "auditor",
    "apis": "creador_de_apis_y_skills",
    "api": "creador_de_apis_y_skills",
    "api_creator": "creador_de_apis_y_skills",
    "creador de apis y skills": "creador_de_apis_y_skills",
    "creador de apis": "creador_de_apis_y_skills",
    "creador_de_apis": "creador_de_apis_y_skills",
    "dcft": "doctor_contable_financiero_tributario",
    "doctor contable financiero tributario": "doctor_contable_financiero_tributario",
    "sentinela": "centinela",
    "sniff amazon": "sniff_amazon",
    "comercio autónomo": "comercio_autonomo",
    "comercio autonomo": "comercio_autonomo",
    "marca personal": "marca_personal",
    "web factory": "web_factory",
    "buscador de tendencias": "buscador_de_tendencias",
    "local agent": "local_agent",
    "sunat": "sunat",
    "produccion": "production",
    "producción": "production",
}

FORBIDDEN_DESTINATIONS = {
    "local_agent": "Local Agent is prohibited in this block.",
    "sunat": "SUNAT real is prohibited in this block.",
    "production": "Direct production operations are prohibited in this block.",
    "runtime_externo": "External runtime connections are prohibited in this block.",
    "external_api": "External API connections are prohibited in this block.",
}


class CerebroError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize_destination(value: str) -> str:
    normalized = " ".join(str(value or "").strip().lower().split())
    normalized = DESTINATION_ALIASES.get(normalized, normalized)
    normalized = normalized.replace(" ", "_").replace("-", "_")
    return DESTINATION_ALIASES.get(normalized, normalized)


def ensure_cerebro_schema() -> None:
    initialize_database()
    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CEREBRO_DECISIONS_TABLE} (
                id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CEREBRO_TASKS_TABLE} (
                id TEXT PRIMARY KEY,
                payload_json TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        for table_name in [
            CEREBRO_COMPANY_GOALS_TABLE,
            CEREBRO_DEPARTMENT_GOALS_TABLE,
            CEREBRO_MISSIONS_TABLE,
            CEREBRO_MISSION_STEPS_TABLE,
            CEREBRO_MISSION_UPDATES_TABLE,
            CEREBRO_ALERTS_TABLE,
            CEREBRO_REVENUE_TABLE,
            CEREBRO_APPROVAL_REQUESTS_TABLE,
            CEREBRO_PRIORITY_CHANGES_TABLE,
            CEREBRO_CEO_CHECKPOINTS_TABLE,
            CEREBRO_COMMERCIAL_DRAFTS_TABLE,
        ]:
            connection.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id TEXT PRIMARY KEY,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
        connection.commit()


def add_column_if_missing(connection, table_name: str, column_definition: str) -> None:
    column_name = column_definition.split()[0]
    if get_database_backend(get_settings().database_url) == "sqlite":
        rows = connection.execute(f"PRAGMA table_info({table_name})").fetchall()
        existing = {get_row_value(row, "name") for row in rows}
        if column_name in existing:
            return
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")
        return
    try:
        connection.execute(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_definition}")
    except Exception:
        connection.rollback()
        pass


def ensure_sombra_inbox_schema() -> None:
    initialize_database()
    with connect() as connection:
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CEREBRO_SOMBRA_INBOX_TABLE} (
                id TEXT PRIMARY KEY,
                message_id TEXT NOT NULL UNIQUE,
                source TEXT NOT NULL,
                message_type TEXT NOT NULL,
                severity TEXT NOT NULL,
                source_created_at TEXT NOT NULL,
                received_at TEXT NOT NULL,
                title TEXT NOT NULL,
                summary TEXT NOT NULL,
                audience_json TEXT NOT NULL,
                routed_to_json TEXT NOT NULL,
                client_context_json TEXT NOT NULL DEFAULT '{{}}',
                safe_for_commercial_use INTEGER NOT NULL DEFAULT 0,
                sensitive INTEGER NOT NULL DEFAULT 1,
                ceo_code TEXT,
                immediate_ceo_attention INTEGER NOT NULL DEFAULT 0,
                top_points_json TEXT NOT NULL DEFAULT '[]',
                executive_summary TEXT,
                commercial_summary TEXT,
                commercial_draft_ready INTEGER NOT NULL DEFAULT 0,
                manual_review_required INTEGER NOT NULL DEFAULT 0,
                encrypted INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                metadata_json TEXT NOT NULL,
                status TEXT NOT NULL,
                header_message_id TEXT,
                header_timestamp TEXT,
                signature_present INTEGER NOT NULL DEFAULT 0,
                received_count INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            )
            """
        )
        add_column_if_missing(
            connection,
            CEREBRO_SOMBRA_INBOX_TABLE,
            "client_context_json TEXT NOT NULL DEFAULT '{}'",
        )
        add_column_if_missing(
            connection,
            CEREBRO_SOMBRA_INBOX_TABLE,
            "safe_for_commercial_use INTEGER NOT NULL DEFAULT 0",
        )
        add_column_if_missing(
            connection,
            CEREBRO_SOMBRA_INBOX_TABLE,
            "sensitive INTEGER NOT NULL DEFAULT 1",
        )
        add_column_if_missing(connection, CEREBRO_SOMBRA_INBOX_TABLE, "ceo_code TEXT")
        add_column_if_missing(
            connection,
            CEREBRO_SOMBRA_INBOX_TABLE,
            "immediate_ceo_attention INTEGER NOT NULL DEFAULT 0",
        )
        add_column_if_missing(
            connection,
            CEREBRO_SOMBRA_INBOX_TABLE,
            "top_points_json TEXT NOT NULL DEFAULT '[]'",
        )
        add_column_if_missing(connection, CEREBRO_SOMBRA_INBOX_TABLE, "executive_summary TEXT")
        add_column_if_missing(connection, CEREBRO_SOMBRA_INBOX_TABLE, "commercial_summary TEXT")
        add_column_if_missing(
            connection,
            CEREBRO_SOMBRA_INBOX_TABLE,
            "commercial_draft_ready INTEGER NOT NULL DEFAULT 0",
        )
        add_column_if_missing(
            connection,
            CEREBRO_SOMBRA_INBOX_TABLE,
            "manual_review_required INTEGER NOT NULL DEFAULT 0",
        )
        connection.commit()


def bool_env(name: str) -> bool:
    return environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def sombra_inbox_enabled() -> bool:
    return bool_env("SOMBRA_INBOX_ENABLED")


def read_sombra_receiver_token() -> str | None:
    token = environ.get("SOMBRA_TO_CEREBRO_TOKEN", "").strip()
    return token or None


def extract_bearer_token(authorization: str | None) -> str | None:
    if not authorization:
        return None
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token.strip():
        return None
    return token.strip()


def validate_sombra_inbox_auth(authorization: str | None) -> None:
    if not sombra_inbox_enabled():
        raise CerebroError(
            status_code=503,
            detail={"error": "sombra_inbox_disabled", "enabled": False},
        )
    expected = read_sombra_receiver_token()
    if not expected:
        raise CerebroError(
            status_code=503,
            detail={"error": "sombra_receiver_token_not_configured"},
        )
    received = extract_bearer_token(authorization)
    if not received:
        raise CerebroError(
            status_code=401,
            detail={"error": "sombra_inbox_token_missing"},
        )
    if not hmac.compare_digest(received, expected):
        raise CerebroError(
            status_code=403,
            detail={"error": "sombra_inbox_token_invalid"},
        )


def validate_sombra_signature(signature: str | None, raw_body: bytes) -> None:
    secret = environ.get("SOMBRA_WEBHOOK_SECRET", "").strip()
    if not secret or not signature:
        return
    expected = hmac.new(secret.encode("utf-8"), raw_body, hashlib.sha256).hexdigest()
    normalized = signature.removeprefix("sha256=").strip()
    if not hmac.compare_digest(normalized, expected):
        raise CerebroError(
            status_code=403,
            detail={"error": "sombra_signature_invalid"},
        )


def sombra_inbox_accepting_messages() -> bool:
    return sombra_inbox_enabled() and read_sombra_receiver_token() is not None


def service_actor() -> AuthenticatedUser:
    return AuthenticatedUser(
        id="cerebro_sombra_inbox_service",
        email="sombra-to-cerebro@internal.local",
        name="SOMBRA to CEREBRO receiver",
        role=ControlCenterRole.service,
        status=UserStatus.active,
        session_id="sombra-inbox",
        created_at=utc_now(),
        updated_at=utc_now(),
    )


def determine_sombra_routes(message: SombraInboxMessageCreate) -> list[str]:
    routes = list(dict.fromkeys(str(item) for item in message.audience))
    if message.severity in {"high", "critical"} and "cerebro" not in routes:
        routes.insert(0, "cerebro")
    if message.severity in {"high", "critical"} and "centinela" not in routes:
        routes.append("centinela")
    if message.severity in {"high", "critical"} and "bunker" not in routes:
        routes.append("bunker")
    if message.type.value == "lead_signal":
        for target in ["cerebro", "pluma", "marketing"]:
            if target not in routes:
                routes.append(target)
    if sombra_message_needs_forja(message) and "forja" not in routes:
        routes.append("forja")
    return routes


def safe_lower_blob(*values: object) -> str:
    return " ".join(str(value or "").lower() for value in values)


def sombra_message_needs_forja(message: SombraInboxMessageCreate) -> bool:
    if message.type.value in {"scan_report", "order_result"}:
        return True
    blob = safe_lower_blob(message.title, message.summary, message.payload)
    return any(
        token in blob
        for token in (
            "patch",
            "parche",
            "diagnostico",
            "vulnerab",
            "remedi",
            "configuracion",
            "hardening",
            "technical",
            "tecnico",
        )
    )


def payload_type(value: object) -> str:
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    return "unknown"


SENSITIVE_METADATA_TOKENS = {
    "token",
    "secret",
    "password",
    "passwd",
    "credential",
    "credencial",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "bearer",
    "private_key",
}


def sanitize_metadata(value: object, depth: int = 0) -> object:
    if depth > 4:
        return "[redacted]"
    if isinstance(value, dict):
        sanitized: dict[str, object] = {}
        for key, item in value.items():
            normalized = str(key).lower()
            if any(token in normalized for token in SENSITIVE_METADATA_TOKENS):
                sanitized[str(key)] = "[redacted]"
            else:
                sanitized[str(key)] = sanitize_metadata(item, depth + 1)
        return sanitized
    if isinstance(value, list):
        return [sanitize_metadata(item, depth + 1) for item in value[:20]]
    return value


def sanitize_public_text(value: object, max_length: int = 420) -> str:
    text = " ".join(str(value or "").replace("\n", " ").split())
    for token in SENSITIVE_METADATA_TOKENS:
        text = text.replace(token, "[redacted]")
        text = text.replace(token.upper(), "[redacted]")
    return (text or "Inteligencia recibida requiere revision manual.")[:max_length]


def cyber_ceo_code(severity: str) -> str | None:
    return CEREBRO_CYBER_INTELLIGENCE_POLICY["ceo_codes"].get(severity)


def extract_executive_top_points(message: SombraInboxMessageCreate) -> list[str]:
    candidates: list[str] = []
    for raw in [message.title, message.summary]:
        text = sanitize_public_text(raw, 520)
        parts = [
            part.strip(" .:-")
            for part in text.replace(";", ".").replace("|", ".").split(".")
            if part.strip(" .:-")
        ]
        candidates.extend(parts)
    if isinstance(message.payload, dict):
        for key in ("finding", "risk", "recommendation", "summary"):
            if key in message.payload:
                candidates.append(sanitize_public_text(message.payload.get(key), 220))
    elif isinstance(message.payload, str) and message.payload and len(candidates) < 3:
        candidates.append(sanitize_public_text(message.payload, 220))

    fallback_points = [
        "Senal de inteligencia recibida y registrada en CEREBRO.",
        "Requiere lectura ejecutiva sin exponer payload sensible.",
        "No se ejecutaron acciones externas ni contacto con clientes.",
    ]
    top_points: list[str] = []
    for item in candidates + fallback_points:
        clean = sanitize_public_text(item, 220)
        if clean and clean not in top_points:
            top_points.append(clean)
        if len(top_points) == 3:
            break
    return top_points


def build_ceo_security_briefing(
    message: SombraInboxMessageCreate,
    top_points: list[str],
    ceo_code: str | None,
    manual_review_required: bool,
) -> str:
    if manual_review_required:
        return CEREBRO_CYBER_INTELLIGENCE_POLICY["fallback"]
    code_copy = f" Alerta {ceo_code} pendiente de revision CEO." if ceo_code else ""
    severity_copy = message.severity.value.upper()
    point_copy = " ".join(f"{index + 1}) {point}" for index, point in enumerate(top_points))
    return (
        f"Daniel, CEREBRO proceso inteligencia de ciberseguridad {severity_copy}."
        f"{code_copy} Lectura ejecutiva: {point_copy}"
    )


def build_commercial_safe_summary(message: SombraInboxMessageCreate, top_points: list[str]) -> str:
    topic = top_points[0] if top_points else sanitize_public_text(message.title, 160)
    return (
        "Borrador seguro para PLUMA/LinkedIn: educar sobre reduccion de riesgo digital "
        f"a partir de senales defensivas como '{topic}', sin mencionar fuentes, sin acusar "
        "empresas y sin compartir credenciales ni evidencia sensible."
    )


def build_forja_signal(message: SombraInboxMessageCreate) -> str:
    severity = message.severity.value
    return (
        "FORJA: preparar diagnostico/parche defensivo derivado de inteligencia "
        f"{severity}. No ejecutar codigo, no tocar repos externos y no desplegar automaticamente."
    )


def build_centinela_signal(message: SombraInboxMessageCreate) -> str:
    if message.severity.value == "critical":
        return "CENTINELA: activar defensa interna preparada y priorizar revision inmediata."
    if message.severity.value == "high":
        return "CENTINELA: ejecutar revision prioritaria de inteligencia recibida por CEREBRO."
    return "CENTINELA: observar inteligencia recibida y mantener lectura interna preparada."


def apply_cyber_intelligence_protocol(message: SombraInboxMessageCreate) -> dict[str, object]:
    ceo_code = cyber_ceo_code(message.severity.value)
    immediate_ceo_attention = message.severity.value in {"critical", "high"}
    manual_review_required = bool(
        message.metadata.get("force_manual_review")
        or message.metadata.get("manual_review_required")
        or message.metadata.get("requires_manual_review")
    )
    top_points = extract_executive_top_points(message)
    executive_summary = build_ceo_security_briefing(
        message,
        top_points,
        ceo_code,
        manual_review_required,
    )
    commercial_draft_ready = (
        message.type.value in {"briefing", "scan_report", "lead_signal"}
        and not manual_review_required
    )
    commercial_summary = (
        build_commercial_safe_summary(message, top_points)
        if commercial_draft_ready
        else None
    )
    return {
        "policy": CEREBRO_CYBER_INTELLIGENCE_POLICY["name"],
        "ceo_code": ceo_code,
        "immediate_ceo_attention": immediate_ceo_attention,
        "top_points": top_points,
        "executive_summary": executive_summary,
        "commercial_summary": commercial_summary,
        "commercial_draft_ready": commercial_draft_ready,
        "manual_review_required": manual_review_required,
        "centinela_signal": build_centinela_signal(message),
        "forja_signal": build_forja_signal(message) if sombra_message_needs_forja(message) else None,
        "heartbeat_received": message.type.value == "heartbeat",
        "safe_for_public_draft": commercial_draft_ready,
    }


def process_sombra_intelligence_message(message: SombraInboxMessageCreate) -> dict[str, object]:
    return apply_cyber_intelligence_protocol(message)


def _json_dump(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _json_load(value: str, fallback: object) -> object:
    try:
        return json.loads(value)
    except (TypeError, json.JSONDecodeError):
        return fallback


def row_bool(row: object, key: str, default: bool = False) -> bool:
    value = get_row_value(row, key, default=1 if default else 0)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def audit_sombra_inbox_message(
    *,
    message: SombraInboxMessageCreate,
    routed_to: list[str],
    duplicate: bool = False,
) -> str:
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.integration,
            severity=AuditSeverity(message.severity.value),
            source="cerebro.sombra_inbox",
            action="receive_sombra_message",
            status="duplicate" if duplicate else "received",
            detail="CEREBRO received an inbox message for internal routing; no external action executed.",
            metadata={
                "message_id": message.message_id,
                "message_type": message.type.value,
                "severity": message.severity.value,
                "audience": list(message.audience),
                "routed_to": routed_to,
                "encrypted": message.encrypted,
                "safe_for_commercial_use": message.safe_for_commercial_use,
                "sensitive": message.sensitive,
                "external_connection_enabled": False,
                "runtime_connected": False,
                "sombra_runtime_called": False,
            },
        )
    )
    return event.id


def _row_to_sombra_recent(row: object) -> SombraInboxRecentMessage:
    audience = _json_load(get_row_value(row, "audience_json", default="[]"), [])
    routed_to = _json_load(get_row_value(row, "routed_to_json", default="[]"), [])
    client_context = _json_load(get_row_value(row, "client_context_json", default="{}"), {})
    top_points = _json_load(get_row_value(row, "top_points_json", default="[]"), [])
    metadata = _json_load(get_row_value(row, "metadata_json", default="{}"), {})
    payload = _json_load(get_row_value(row, "payload_json", default='""'), "")
    return SombraInboxRecentMessage(
        id=get_row_value(row, "id"),
        message_id=get_row_value(row, "message_id"),
        source=get_row_value(row, "source"),
        type=get_row_value(row, "message_type"),
        severity=get_row_value(row, "severity"),
        created_at=get_row_value(row, "source_created_at"),
        received_at=get_row_value(row, "received_at"),
        title=get_row_value(row, "title"),
        summary=get_row_value(row, "summary"),
        audience=list(audience) if isinstance(audience, list) else [],
        routed_to=list(routed_to) if isinstance(routed_to, list) else [],
        ceo_code=get_row_value(row, "ceo_code", default=None),
        immediate_ceo_attention=row_bool(row, "immediate_ceo_attention"),
        top_points=list(top_points) if isinstance(top_points, list) else [],
        executive_summary=get_row_value(row, "executive_summary", default=None),
        commercial_summary=get_row_value(row, "commercial_summary", default=None),
        commercial_draft_ready=row_bool(row, "commercial_draft_ready"),
        manual_review_required=row_bool(row, "manual_review_required"),
        client_context=client_context if isinstance(client_context, dict) else {},
        safe_for_commercial_use=row_bool(row, "safe_for_commercial_use"),
        sensitive=row_bool(row, "sensitive", default=True),
        encrypted=row_bool(row, "encrypted", default=True),
        payload_type=payload_type(payload),
        metadata=sanitize_metadata(metadata) if isinstance(metadata, dict) else {},
        status=get_row_value(row, "status"),
    )


def receive_sombra_inbox_message(
    message: SombraInboxMessageCreate,
    *,
    authorization: str | None,
    header_message_id: str | None = None,
    header_timestamp: str | None = None,
    signature: str | None = None,
    raw_body: bytes = b"",
) -> SombraInboxMessageResponse:
    validate_sombra_inbox_auth(authorization)
    validate_sombra_signature(signature, raw_body)
    if header_message_id and header_message_id != message.message_id:
        raise CerebroError(
            status_code=400,
            detail={
                "error": "sombra_message_id_mismatch",
                "message_id": message.message_id,
                "header_message_id": header_message_id,
            },
        )

    ensure_sombra_inbox_schema()
    now = utc_now()
    protocol = apply_cyber_intelligence_protocol(message)
    routed_to = determine_sombra_routes(message)
    placeholder = sql_placeholder()
    with connect() as connection:
        existing = connection.execute(
            f"SELECT * FROM {CEREBRO_SOMBRA_INBOX_TABLE} WHERE message_id = {placeholder}",
            (message.message_id,),
        ).fetchone()
        if existing is not None:
            connection.execute(
                f"""
                UPDATE {CEREBRO_SOMBRA_INBOX_TABLE}
                SET received_count = received_count + 1, updated_at = {placeholder}
                WHERE message_id = {placeholder}
                """,
                (now, message.message_id),
            )
            connection.commit()
            audit_sombra_inbox_message(message=message, routed_to=routed_to, duplicate=True)
            return SombraInboxMessageResponse(
                ok=True,
                received=True,
                message_id=message.message_id,
                stored=True,
                severity=message.severity,
                ceo_code=get_row_value(existing, "ceo_code", default=None),
                immediate_ceo_attention=row_bool(existing, "immediate_ceo_attention"),
                routed_to=list(_json_load(get_row_value(existing, "routed_to_json"), routed_to)),
                executive_summary=get_row_value(existing, "executive_summary", default=None),
                commercial_draft_ready=row_bool(existing, "commercial_draft_ready"),
                manual_review_required=row_bool(existing, "manual_review_required"),
            )
    internal_actions = route_sombra_message(message, routed_to, protocol)
    stored_metadata = sanitize_metadata(
        {
            **message.metadata,
            "cyber_intelligence_protocol": protocol,
            "internal_actions": internal_actions,
            "source_hidden_from_clients": True,
            "publish_allowed": False,
            "contact_allowed": False,
        }
    )
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {CEREBRO_SOMBRA_INBOX_TABLE} (
                id,
                message_id,
                source,
                message_type,
                severity,
                source_created_at,
                received_at,
                title,
                summary,
                audience_json,
                routed_to_json,
                client_context_json,
                safe_for_commercial_use,
                sensitive,
                ceo_code,
                immediate_ceo_attention,
                top_points_json,
                executive_summary,
                commercial_summary,
                commercial_draft_ready,
                manual_review_required,
                encrypted,
                payload_json,
                metadata_json,
                status,
                header_message_id,
                header_timestamp,
                signature_present,
                received_count,
                updated_at
            )
            VALUES (
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder},
                {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}
            )
            """,
            (
                f"sombra-inbox-{uuid4()}",
                message.message_id,
                message.source,
                message.type.value,
                message.severity.value,
                message.created_at,
                now,
                message.title,
                message.summary,
                _json_dump(list(message.audience)),
                _json_dump(routed_to),
                message.client_context.model_dump_json(),
                1 if message.safe_for_commercial_use else 0,
                1 if message.sensitive else 0,
                protocol["ceo_code"],
                1 if protocol["immediate_ceo_attention"] else 0,
                _json_dump(protocol["top_points"]),
                protocol["executive_summary"],
                protocol["commercial_summary"],
                1 if protocol["commercial_draft_ready"] else 0,
                1 if protocol["manual_review_required"] else 0,
                1 if message.encrypted else 0,
                _json_dump(message.payload),
                _json_dump(stored_metadata),
                "received_routed" if internal_actions else "received_prepared",
                header_message_id,
                header_timestamp,
                1 if signature else 0,
                1,
                now,
            ),
        )
        connection.commit()
    audit_sombra_inbox_message(message=message, routed_to=routed_to)
    return SombraInboxMessageResponse(
        ok=True,
        received=True,
        message_id=message.message_id,
        stored=True,
        severity=message.severity,
        ceo_code=protocol["ceo_code"],
        immediate_ceo_attention=bool(protocol["immediate_ceo_attention"]),
        routed_to=routed_to,
        executive_summary=str(protocol["executive_summary"]),
        commercial_draft_ready=bool(protocol["commercial_draft_ready"]),
        manual_review_required=bool(protocol["manual_review_required"]),
    )


def receive_sombra_inbox(
    message: SombraInboxMessageCreate,
    *,
    authorization: str | None,
    header_message_id: str | None = None,
    header_timestamp: str | None = None,
    signature: str | None = None,
    raw_body: bytes = b"",
) -> SombraInboxMessageResponse:
    return receive_sombra_inbox_message(
        message,
        authorization=authorization,
        header_message_id=header_message_id,
        header_timestamp=header_timestamp,
        signature=signature,
        raw_body=raw_body,
    )


def store_sombra_message(
    message: SombraInboxMessageCreate,
    *,
    authorization: str | None,
) -> SombraInboxMessageResponse:
    return receive_sombra_inbox_message(message, authorization=authorization)


def list_sombra_inbox_messages(limit: int = 20) -> list[SombraInboxRecentMessage]:
    ensure_sombra_inbox_schema()
    safe_limit = max(1, min(int(limit or 20), 100))
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM {CEREBRO_SOMBRA_INBOX_TABLE}
            ORDER BY received_at DESC
            LIMIT {safe_limit}
            """
        ).fetchall()
    return [_row_to_sombra_recent(row) for row in rows]


def get_sombra_inbox_metrics() -> dict[str, object]:
    messages = list_sombra_inbox_messages(limit=100)
    severity_rank = {"unknown": 0, "low": 1, "medium": 2, "high": 3, "critical": 4}
    threat_level = "unknown"
    for message in messages:
        level = message.severity.value
        if severity_rank[level] > severity_rank[threat_level]:
            threat_level = level
    critical_alerts = sum(1 for item in messages if item.severity.value == "critical")
    high_alerts = sum(1 for item in messages if item.severity.value == "high")
    lead_signals = sum(1 for item in messages if item.type.value == "lead_signal")
    heartbeats = [item for item in messages if item.type.value == "heartbeat"]
    ceo_codes_pending = list(dict.fromkeys(
        item.ceo_code for item in messages if item.ceo_code and item.immediate_ceo_attention
    ))
    return {
        "messages": messages,
        "external_intel_messages": len(messages),
        "critical_alerts": critical_alerts,
        "high_alerts": high_alerts,
        "lead_signals": lead_signals,
        "threat_level": threat_level,
        "last_intel_at": messages[0].received_at if messages else None,
        "last_heartbeat_at": heartbeats[0].received_at if heartbeats else None,
        "ceo_codes_pending": ceo_codes_pending,
        "sombra_connected": bool(messages) and sombra_inbox_accepting_messages(),
    }


def list_sombra_recent(limit: int = 20) -> list[SombraInboxRecentMessage]:
    return list_sombra_inbox_messages(limit=limit)


def create_cerebro_commercial_draft(
    request: CerebroCommercialDraftCreate,
    actor: AuthenticatedUser,
) -> CerebroCommercialDraft:
    ensure_cerebro_schema()
    now = utc_now()
    country = request.client_context.country or "LATAM"
    sector = request.client_context.sector or "empresas"
    title = cerebro_chat_title(request.title, "Borrador comercial defensivo")
    linkedin_post_idea = (
        f"Publicacion LinkedIn sobre reduccion de riesgo por credenciales expuestas en {country}, "
        f"orientada a {sector}, sin revelar fuentes, dominios ni datos sensibles."
    )
    draft = CerebroCommercialDraft(
        id=f"cerebro-commercial-draft-{uuid4()}",
        source=request.source,
        source_message_id=request.source_message_id,
        title=title,
        draft_type="linkedin_post",
        draft=linkedin_post_idea,
        linkedin_post_idea=linkedin_post_idea,
        private_message=(
            "Mensaje privado profesional: ofrecer un diagnostico defensivo de exposicion digital "
            "sin afirmar incidentes, sin acusaciones y sin compartir evidencia sensible."
        ),
        centinela_angle=(
            "CENTINELA puede convertir la senal en lectura de riesgo defensiva y priorizar "
            "controles preventivos para decision del CEO."
        ),
        guardrails=[
            "No mencionar la fuente de inteligencia.",
            "No publicar automaticamente.",
            "No contactar clientes automaticamente.",
            "No incluir credenciales, secretos, dominios sensibles ni payload completo.",
            "Mantener tono defensivo, profesional y no acusatorio.",
        ],
        client_context=request.client_context,
        safe_for_commercial_use=request.safe_for_commercial_use,
        safe_for_public_review=True,
        requires_ceo_approval=True,
        created_at=now,
    )
    insert_payload(CEREBRO_COMMERCIAL_DRAFTS_TABLE, draft.id, draft.model_dump_json())
    audit_cerebro_action(
        action="create_commercial_draft",
        actor=actor,
        status=draft.status,
        detail="CEREBRO prepared a sanitized commercial draft; no publishing or outreach executed.",
        state=CerebroState.proposed,
        destination="pluma_marketing",
        reason=request.summary,
        requires_ceo_approval=True,
    )
    return draft


def list_commercial_drafts() -> list[CerebroCommercialDraft]:
    return safe_models(CerebroCommercialDraft, fetch_payloads(CEREBRO_COMMERCIAL_DRAFTS_TABLE))


def route_sombra_message(
    message: SombraInboxMessageCreate,
    routed_to: list[str],
    protocol: dict[str, object] | None = None,
) -> list[dict[str, str]]:
    protocol = protocol or apply_cyber_intelligence_protocol(message)
    actor = service_actor()
    actions: list[dict[str, str]] = []
    if message.severity.value in {"high", "critical"}:
        try:
            ceo_code = str(protocol.get("ceo_code") or "")
            alert = create_alert(
                CerebroAlertCreate(
                    title=(
                        f"Alerta {ceo_code} pendiente de revision CEO"
                        if ceo_code
                        else cerebro_chat_title(message.title, "Inteligencia defensiva entrante")
                    ),
                    summary=str(protocol.get("executive_summary") or message.summary),
                    source="cerebro_sombra_inbox_internal",
                    relevance_score=96 if message.severity.value == "critical" else 84,
                    risk_level=message.severity.value,
                    dafo=CerebroDafo(
                        opportunities=[
                            "Convertir inteligencia entrante en diagnostico defensivo gobernado."
                        ],
                        threats=[
                            "Riesgo externo reportado sin exponer payload sensible ni ejecutar acciones."
                        ],
                    ),
                ),
                actor,
            )
            actions.append({
                "type": "alert_created",
                "id": alert.id,
                "target": "cerebro_centinela_bunker",
                "ceo_code": ceo_code,
            })
        except Exception as exc:
            actions.append({"type": "alert_failed", "id": "unavailable", "target": str(exc)[:120]})

    if sombra_message_needs_forja(message):
        try:
            task = create_cerebro_task(
                CerebroTaskCreate(
                    title="Revisar oportunidad de parche/diagnostico defensivo",
                    description=str(protocol.get("forja_signal") or build_forja_signal(message)),
                    destination="FORJA",
                    priority="p0" if message.severity.value == "critical" else "p1",
                    reason="origen=cerebro/sombra_inbox; tarea interna preparada sin ejecucion automatica.",
                    requires_ceo_approval=False,
                ),
                actor,
            )
            actions.append({"type": "forja_task_created", "id": task.id, "target": "forja"})
        except Exception as exc:
            actions.append({"type": "forja_task_failed", "id": "unavailable", "target": str(exc)[:120]})

    if message.type.value in {"briefing", "scan_report", "lead_signal"} and not protocol.get("manual_review_required"):
        try:
            if message.type.value == "lead_signal":
                opportunity = create_revenue_opportunity(
                    CerebroRevenueOpportunityCreate(
                        title="Oportunidad comercial defensiva sanitizada",
                        description=(
                            "Oportunidad interna para diagnostico de riesgo defensivo. "
                            "No revela fuentes, no publica y no contacta clientes sin aprobacion CEO."
                        ),
                        department="PLUMA/MARKETING",
                        risk="controlled",
                        recommendation="Preparar borrador y esperar aprobacion CEO.",
                        requires_ceo_approval=True,
                    ),
                    actor,
                )
                actions.append({"type": "revenue_opportunity_created", "id": opportunity.id, "target": "cerebro"})
            if protocol.get("commercial_draft_ready"):
                draft = create_cerebro_commercial_draft(
                    CerebroCommercialDraftCreate(
                        source="sombra_inbox",
                        source_message_id=message.message_id,
                        title=message.title,
                        summary=str(protocol.get("commercial_summary") or message.summary),
                        client_context=message.client_context,
                        safe_for_commercial_use=True,
                    ),
                    actor,
                )
                actions.append({"type": "commercial_draft_created", "id": draft.id, "target": "pluma_marketing"})
        except Exception as exc:
            actions.append({"type": "lead_signal_route_failed", "id": "unavailable", "target": str(exc)[:120]})

    return [action for action in actions if action.get("target") in routed_to or action["type"].endswith("created") or action["type"].endswith("failed")]


def actor_name(user: AuthenticatedUser) -> str:
    return user.email or user.name or user.id


def actor_role(user: AuthenticatedUser) -> str:
    return user.role.value.lower()


def safe_reason(value: str | None, fallback: str) -> str:
    reason = " ".join(str(value or "").strip().split())
    return reason or fallback


def audit_cerebro_action(
    *,
    action: str,
    actor: AuthenticatedUser,
    status: str,
    detail: str,
    state: CerebroState,
    destination: str | None = None,
    reason: str | None = None,
    requires_ceo_approval: bool = False,
    blocked: bool = False,
) -> str:
    metadata = {
        "actor": actor_name(actor),
        "role": actor_role(actor),
        "action": action,
        "destination": destination,
        "state": state.value,
        "reason": safe_reason(reason, "not_provided"),
        "requires_ceo_approval": requires_ceo_approval,
        "blocked": blocked,
        "timestamp": utc_now(),
        "external_connection_enabled": False,
        "runtime_connected": False,
    }
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.runtime,
            severity=AuditSeverity.high if blocked else AuditSeverity.info,
            source="cerebro.operational_runtime",
            action=action,
            status=status,
            detail=detail,
            metadata=metadata,
        )
    )
    return event.id


def insert_payload(table_name: str, item_id: str, payload: str) -> None:
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (item_id, payload, now, now),
        )
        connection.commit()


def update_payload(table_name: str, item_id: str, payload: str) -> None:
    placeholder = sql_placeholder()
    now = utc_now()
    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {table_name}
            SET payload_json = {placeholder}, updated_at = {placeholder}
            WHERE id = {placeholder}
            """,
            (payload, now, item_id),
        )
        connection.commit()


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_cerebro_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            ORDER BY created_at DESC
            """
        ).fetchall()
    payloads: list[dict] = []
    for row in rows:
        payload = safe_payload(row)
        if payload is not None:
            payloads.append(payload)
    return payloads


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_cerebro_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    return safe_payload(row) if row else None


def safe_models(model_class, payloads: list[dict]) -> list:
    rows: list = []
    for payload in payloads:
        try:
            rows.append(model_class(**payload))
        except Exception:
            continue
    return rows


def upsert_payload(table_name: str, item_id: str, payload: str) -> None:
    existing = fetch_payload(table_name, item_id)
    if existing is None:
        insert_payload(table_name, item_id, payload)
    else:
        update_payload(table_name, item_id, payload)


def peru_now() -> str:
    return datetime.now(PERU_TZ).isoformat()


def safe_identifier(value: str, fallback: str) -> str:
    normalized = normalize_destination(value)
    return normalized or fallback


def authority_rule_for_action(
    action_type: str,
    *,
    requires_money: bool = False,
    investment_required: float = 0,
    risk: str | None = None,
) -> tuple[CerebroAuthorityLevel, str]:
    action = normalize_destination(action_type)
    risk_text = normalize_destination(risk or "")
    if (
        requires_money
        or investment_required > 0
        or action in CEO_APPROVAL_REQUIRED_ACTIONS
        or risk_text in {"high", "critical", "legal", "tax", "reputational"}
    ):
        return (
            CerebroAuthorityLevel.ceo_approval_required,
            CEO_APPROVAL_REQUIRED_ACTIONS.get(
                action,
                "Requiere CEO porque implica dinero real, proveedor externo, credenciales o riesgo alto.",
            ),
        )
    if action in NO_APPROVAL_REQUIRED_ACTIONS:
        return CerebroAuthorityLevel.no_approval_required, NO_APPROVAL_REQUIRED_ACTIONS[action]
    return (
        CerebroAuthorityLevel.no_approval_required,
        "Mision interna preparada; CEREBRO puede avanzar sin gasto real ni runtime externo.",
    )


def build_authority_matrix() -> list[CerebroAuthorityRule]:
    no_approval = [
        CerebroAuthorityRule(
            action_type=action,
            level=CerebroAuthorityLevel.no_approval_required,
            reason=reason,
            technical_status="prepared",
        )
        for action, reason in sorted(NO_APPROVAL_REQUIRED_ACTIONS.items())
    ]
    ceo_required = [
        CerebroAuthorityRule(
            action_type=action,
            level=CerebroAuthorityLevel.ceo_approval_required,
            reason=reason,
            technical_status="requires_ceo_decision",
        )
        for action, reason in sorted(CEO_APPROVAL_REQUIRED_ACTIONS.items())
    ]
    return no_approval + ceo_required


def economic_matrix(
    *,
    investment_required: float = 0,
    expected_revenue: float = 0,
    currency: str = "USD",
    return_time: str = "not_estimated",
    recommendation: str = "Preparar sin gasto real.",
    ecommerce_separate: bool = False,
) -> CerebroEconomicMatrix:
    goal = ECOMMERCE_MONTHLY_GOAL_USD if ecommerce_separate else GLOBAL_MONTHLY_GOAL_USD
    net_profit = expected_revenue - investment_required
    contribution = (net_profit / goal) * 100 if goal else 0
    return CerebroEconomicMatrix(
        currency=currency,
        investment_required=investment_required,
        expected_revenue=expected_revenue,
        expected_net_profit=round(net_profit, 2),
        monthly_goal=goal,
        monthly_goal_contribution_percent=round(contribution, 2),
        return_time=return_time,
        recommendation=recommendation,
        ecommerce_separate=ecommerce_separate,
    )


def default_company_goal_payloads() -> list[CerebroCompanyGoal]:
    now = utc_now()
    return [
        CerebroCompanyGoal(
            id="ecosystem_global_6000_usd",
            name="Meta global Ecosistema IA",
            description="Generar USD 6,000 mensuales fuera de e-commerce.",
            monthly_target_usd=GLOBAL_MONTHLY_GOAL_USD,
            ecommerce_separate=False,
            status="active",
            created_at=now,
            updated_at=now,
        ),
        CerebroCompanyGoal(
            id="ecommerce_10000_usd",
            name="Meta e-commerce separada",
            description="Generar USD 10,000 mensuales desde e-commerce, separado de la meta global.",
            monthly_target_usd=ECOMMERCE_MONTHLY_GOAL_USD,
            ecommerce_separate=True,
            status="active",
            created_at=now,
            updated_at=now,
        ),
    ]


def default_department_goal_payloads() -> list[CerebroDepartmentGoal]:
    now = utc_now()
    rows = [
        ("pluma", "PLUMA", "Crear contenido ejecutivo y comercial.", "Aumenta confianza y ventas organicas."),
        ("lente", "LENTE", "Preparar visuales y video.", "Mejora conversion y claridad de oferta."),
        ("marketing", "MARKETING", "Preparar campanas organicas y estrategia.", "Genera demanda sin gasto por defecto."),
        ("marca_personal", "MARCA PERSONAL", "Convertir autoridad del CEO en oportunidades.", "Atrae leads y alianzas."),
        ("buscador_de_tendencias", "BUSCADOR DE TENDENCIAS", "Detectar senales utiles.", "Encuentra oportunidades antes que el mercado."),
        ("auditoria", "AUDITORIA", "Revisar riesgo, evidencia y calidad.", "Evita perdida por errores."),
        ("nube", "NUBE", "Controlar URLs, costos y deploys preparados.", "Reduce friccion operativa."),
        ("creador_de_apis_y_skills", "CREADOR DE APIS Y SKILLS", "Preparar APIs y skills vendibles.", "Convierte capacidades en productos."),
        ("ecommerce", "E-COMMERCE", "Operar meta separada de USD 10,000 mensuales.", "Linea comercial independiente."),
        ("sniff_amazon", "SNIFF AMAZON", "Detectar productos y senales Amazon.", "Alimenta oportunidades e-commerce."),
        ("dcft", "DCFT", "Producto contable financiero tributario gobernado.", "Primer producto comercial prioritario; sin SUNAT real en este bloque."),
        ("sentinela", "SENTINELA", "Producto futuro de seguridad y proteccion.", "Futuro B2B; protegido sin runtime productivo."),
        ("forja", "FORJA", "Construir entregables cuando la politica lo permite.", "Convierte misiones en software controlado."),
        ("hermes", "HERMES", "Automatizacion ligera y soporte.", "Acelera trabajo repetible sin runtime externo."),
        ("web_factory", "WEB FACTORY", "Preparar landings y sitios.", "Canaliza oferta y conversion."),
        ("arsenal", "ARSENAL", "Registrar APIs, modelos, conectores y capacidades.", "Memoria estrategica de capacidades futuras."),
    ]
    return [
        CerebroDepartmentGoal(
            id=row_id,
            department=department,
            goal=goal,
            revenue_role=revenue_role,
            operating_mode="prepared_no_runtime",
            monthly_target_usd=ECOMMERCE_MONTHLY_GOAL_USD if row_id == "ecommerce" else None,
            created_at=now,
            updated_at=now,
        )
        for row_id, department, goal, revenue_role in rows
    ]


def seed_chief_of_staff_defaults() -> None:
    ensure_cerebro_schema()
    if not fetch_payloads(CEREBRO_COMPANY_GOALS_TABLE):
        for goal in default_company_goal_payloads():
            insert_payload(CEREBRO_COMPANY_GOALS_TABLE, goal.id, goal.model_dump_json())
    if not fetch_payloads(CEREBRO_DEPARTMENT_GOALS_TABLE):
        for goal in default_department_goal_payloads():
            insert_payload(CEREBRO_DEPARTMENT_GOALS_TABLE, goal.id, goal.model_dump_json())


def list_company_goals() -> list[CerebroCompanyGoal]:
    seed_chief_of_staff_defaults()
    return safe_models(CerebroCompanyGoal, fetch_payloads(CEREBRO_COMPANY_GOALS_TABLE))


def create_company_goal(request: CerebroCompanyGoalCreate, actor: AuthenticatedUser) -> CerebroCompanyGoal:
    seed_chief_of_staff_defaults()
    now = utc_now()
    goal_id = request.id or f"company_goal_{safe_identifier(request.name, str(uuid4()))}"
    existing = fetch_payload(CEREBRO_COMPANY_GOALS_TABLE, goal_id)
    goal = CerebroCompanyGoal(
        id=goal_id,
        name=request.name,
        description=request.description,
        monthly_target_usd=request.monthly_target_usd,
        ecommerce_separate=request.ecommerce_separate,
        status=request.status,
        created_at=existing.get("created_at", now) if existing else now,
        updated_at=now,
    )
    upsert_payload(CEREBRO_COMPANY_GOALS_TABLE, goal.id, goal.model_dump_json())
    audit_cerebro_action(
        action="upsert_company_goal",
        actor=actor,
        status="active",
        detail="CEREBRO updated a company goal for Chief of Staff OS.",
        state=CerebroState.delegated,
        reason=goal.description,
    )
    return goal


def list_department_goals() -> list[CerebroDepartmentGoal]:
    seed_chief_of_staff_defaults()
    return safe_models(CerebroDepartmentGoal, fetch_payloads(CEREBRO_DEPARTMENT_GOALS_TABLE))


def create_department_goal(
    request: CerebroDepartmentGoalCreate,
    actor: AuthenticatedUser,
) -> CerebroDepartmentGoal:
    seed_chief_of_staff_defaults()
    now = utc_now()
    goal_id = request.id or f"department_goal_{safe_identifier(request.department, str(uuid4()))}"
    existing = fetch_payload(CEREBRO_DEPARTMENT_GOALS_TABLE, goal_id)
    goal = CerebroDepartmentGoal(
        id=goal_id,
        department=request.department,
        goal=request.goal,
        revenue_role=request.revenue_role,
        operating_mode=request.operating_mode,
        monthly_target_usd=request.monthly_target_usd,
        requires_ceo_approval_for_money=request.requires_ceo_approval_for_money,
        created_at=existing.get("created_at", now) if existing else now,
        updated_at=now,
    )
    upsert_payload(CEREBRO_DEPARTMENT_GOALS_TABLE, goal.id, goal.model_dump_json())
    audit_cerebro_action(
        action="upsert_department_goal",
        actor=actor,
        status="prepared",
        detail="CEREBRO updated a department goal for Chief of Staff OS.",
        state=CerebroState.delegated,
        destination=request.department,
        reason=request.goal,
    )
    return goal


def default_mission_steps(request: CerebroMissionCreate, now: str) -> list[CerebroMissionStep]:
    departments = request.involved_departments or [request.leader_department]
    return [
        CerebroMissionStep(
            id=f"mission_step_{uuid4()}",
            title=f"Preparar accion con {department}",
            owner_department=department,
            status="pending",
            notes="Preparado sin runtime externo.",
            created_at=now,
            updated_at=now,
        )
        for department in departments[:8]
    ]


def mission_relation_text(request: CerebroMissionCreate, matrix: CerebroEconomicMatrix) -> str:
    if request.relation_to_monthly_goal:
        return request.relation_to_monthly_goal
    if matrix.expected_net_profit:
        return (
            f"Aporta {matrix.monthly_goal_contribution_percent}% a la meta mensual "
            f"de USD {matrix.monthly_goal:g}."
        )
    return "Sin impacto economico cuantificado todavia; CEREBRO debe estimarlo antes de pedir gasto."


def list_missions() -> list[CerebroMission]:
    seed_chief_of_staff_defaults()
    return safe_models(CerebroMission, fetch_payloads(CEREBRO_MISSIONS_TABLE))


def get_mission(mission_id: str) -> CerebroMission:
    payload = fetch_payload(CEREBRO_MISSIONS_TABLE, mission_id)
    if payload is None:
        raise CerebroError(404, {"error": "cerebro_mission_not_found", "mission_id": mission_id})
    return CerebroMission(**payload)


def create_mission(request: CerebroMissionCreate, actor: AuthenticatedUser) -> CerebroMission:
    seed_chief_of_staff_defaults()
    now = utc_now()
    level, reason = authority_rule_for_action(
        request.action_type,
        requires_money=request.requires_money,
        investment_required=request.investment_required,
        risk="high" if any("alto" in normalize_destination(risk) for risk in request.risks) else None,
    )
    requires_ceo = (
        request.requires_ceo_approval
        if request.requires_ceo_approval is not None
        else level == CerebroAuthorityLevel.ceo_approval_required
    )
    state = request.state or (
        CerebroMissionState.waiting_ceo_approval
        if requires_ceo
        else CerebroMissionState.assigned
    )
    matrix = economic_matrix(
        investment_required=request.investment_required,
        expected_revenue=request.expected_revenue or request.estimated_economic_impact,
        return_time="to_be_reported",
        recommendation=(
            "CEO, esto requiere tu decision antes de gastar."
            if requires_ceo
            else "CEREBRO puede avanzar sin pedir permiso porque no hay gasto real ni runtime externo."
        ),
        ecommerce_separate=request.ecommerce_separate,
    )
    mission_id = f"cerebro_mission_{uuid4()}"
    audit_event_id = audit_cerebro_action(
        action="create_chief_of_staff_mission",
        actor=actor,
        status=state.value,
        detail="CEREBRO created a Chief of Staff OS mission.",
        state=CerebroState.waiting_ceo if requires_ceo else CerebroState.delegated,
        destination=request.leader_department,
        reason=request.objective,
        requires_ceo_approval=requires_ceo,
    )
    mission = CerebroMission(
        id=mission_id,
        title=request.title,
        objective=request.objective,
        origin=request.origin,
        leader_department=request.leader_department,
        involved_departments=request.involved_departments,
        priority=request.priority,
        action_type=request.action_type,
        authority_level=level,
        authority_reason=reason,
        estimated_economic_impact=request.estimated_economic_impact,
        relation_to_monthly_goal=mission_relation_text(request, matrix),
        state=state,
        steps=default_mission_steps(request, now),
        updates=[],
        executed_actions=[],
        pending_actions=["reportar_a_ceo", "registrar_evidencia"],
        risks=request.risks,
        requires_money=request.requires_money,
        requires_ceo_approval=requires_ceo,
        expected_report=request.expected_report,
        economic_matrix=matrix,
        technical_status="prepared",
        audit_trail=[audit_event_id],
        created_at=now,
        updated_at=now,
    )
    insert_payload(CEREBRO_MISSIONS_TABLE, mission.id, mission.model_dump_json())
    for step in mission.steps:
        insert_payload(CEREBRO_MISSION_STEPS_TABLE, step.id, step.model_dump_json())
    return mission


def add_mission_update(
    mission_id: str,
    request: CerebroMissionUpdateCreate,
    actor: AuthenticatedUser,
) -> CerebroMission:
    mission = get_mission(mission_id)
    now = utc_now()
    update = CerebroMissionUpdate(
        id=f"mission_update_{uuid4()}",
        mission_id=mission.id,
        department=request.department,
        status=request.status,
        message=request.message,
        created_at=now,
    )
    mission.updates.insert(0, update)
    if request.state is not None:
        mission.state = request.state
    mission.updated_at = now
    audit_event_id = audit_cerebro_action(
        action="update_chief_of_staff_mission",
        actor=actor,
        status=mission.state.value,
        detail="CEREBRO updated a Chief of Staff OS mission.",
        state=CerebroState.delegated,
        destination=request.department,
        reason=request.message,
        requires_ceo_approval=mission.requires_ceo_approval,
    )
    mission.audit_trail.insert(0, audit_event_id)
    insert_payload(CEREBRO_MISSION_UPDATES_TABLE, update.id, update.model_dump_json())
    update_payload(CEREBRO_MISSIONS_TABLE, mission.id, mission.model_dump_json())
    return mission


def dispatch_mission(
    mission_id: str,
    request: CerebroMissionDispatchRequest,
    actor: AuthenticatedUser,
) -> CerebroMission:
    mission = get_mission(mission_id)
    now = utc_now()
    instruction = f"{request.department}: {request.instruction}"
    mission.pending_actions.insert(0, instruction)
    mission.executed_actions.insert(0, f"dispatch_prepared:{request.department}")
    if mission.state in {CerebroMissionState.created, CerebroMissionState.assigned}:
        mission.state = CerebroMissionState.in_progress
    mission.updated_at = now
    audit_event_id = audit_cerebro_action(
        action="dispatch_chief_of_staff_mission",
        actor=actor,
        status=mission.state.value,
        detail="CEREBRO prepared a department dispatch without external runtime.",
        state=CerebroState.delegated,
        destination=request.department,
        reason=request.instruction,
        requires_ceo_approval=mission.requires_ceo_approval,
    )
    mission.audit_trail.insert(0, audit_event_id)
    update_payload(CEREBRO_MISSIONS_TABLE, mission.id, mission.model_dump_json())
    return mission


def alert_relevance(score: int) -> str:
    if score >= 85:
        return "high"
    if score >= 70:
        return "medium"
    return "low"


def list_alerts(include_low: bool = False) -> list[CerebroAlert]:
    seed_chief_of_staff_defaults()
    alerts = safe_models(CerebroAlert, fetch_payloads(CEREBRO_ALERTS_TABLE))
    if include_low:
        return alerts
    return [alert for alert in alerts if alert.interrupt_ceo]


def create_alert(request: CerebroAlertCreate, actor: AuthenticatedUser) -> CerebroAlert:
    seed_chief_of_staff_defaults()
    now = utc_now()
    relevance = alert_relevance(request.relevance_score)
    alert = CerebroAlert(
        id=f"cerebro_alert_{uuid4()}",
        title=request.title,
        summary=request.summary,
        source=request.source,
        relevance_score=request.relevance_score,
        relevance=relevance,
        interrupt_ceo=request.relevance_score >= 70,
        risk_level=request.risk_level,
        economic_impact=request.economic_impact,
        dafo=request.dafo,
        created_at=now,
    )
    insert_payload(CEREBRO_ALERTS_TABLE, alert.id, alert.model_dump_json())
    audit_cerebro_action(
        action="create_chief_of_staff_alert",
        actor=actor,
        status=relevance,
        detail="CEREBRO evaluated an alert relevance filter.",
        state=CerebroState.proposed,
        reason=request.summary,
        requires_ceo_approval=alert.interrupt_ceo and request.risk_level in {"high", "critical"},
    )
    return alert


def list_revenue_opportunities() -> list[CerebroRevenueOpportunity]:
    seed_chief_of_staff_defaults()
    return safe_models(CerebroRevenueOpportunity, fetch_payloads(CEREBRO_REVENUE_TABLE))


def create_revenue_opportunity(
    request: CerebroRevenueOpportunityCreate,
    actor: AuthenticatedUser,
) -> CerebroRevenueOpportunity:
    seed_chief_of_staff_defaults()
    matrix = economic_matrix(
        investment_required=request.investment_required,
        expected_revenue=request.expected_revenue,
        currency=request.currency,
        return_time=request.return_time,
        recommendation=request.recommendation,
        ecommerce_separate=request.ecommerce_separate,
    )
    requires_ceo = (
        request.requires_ceo_approval
        if request.requires_ceo_approval is not None
        else request.investment_required > 0
    )
    opportunity = CerebroRevenueOpportunity(
        id=f"cerebro_revenue_{uuid4()}",
        title=request.title,
        description=request.description,
        department=request.department,
        economic_matrix=matrix,
        risk=request.risk,
        requires_ceo_approval=requires_ceo,
        status="waiting_ceo_approval" if requires_ceo else "prepared",
        created_at=utc_now(),
    )
    insert_payload(CEREBRO_REVENUE_TABLE, opportunity.id, opportunity.model_dump_json())
    audit_cerebro_action(
        action="create_revenue_opportunity",
        actor=actor,
        status=opportunity.status,
        detail="CEREBRO registered a revenue opportunity with economic matrix.",
        state=CerebroState.waiting_ceo if requires_ceo else CerebroState.delegated,
        destination=request.department,
        reason=request.description,
        requires_ceo_approval=requires_ceo,
    )
    return opportunity


def list_approval_requests() -> list[CerebroApprovalRequest]:
    seed_chief_of_staff_defaults()
    return safe_models(CerebroApprovalRequest, fetch_payloads(CEREBRO_APPROVAL_REQUESTS_TABLE))


def create_approval_request(
    request: CerebroApprovalRequestCreate,
    actor: AuthenticatedUser,
) -> CerebroApprovalRequest:
    seed_chief_of_staff_defaults()
    now = utc_now()
    matrix = economic_matrix(
        investment_required=request.investment_required,
        expected_revenue=request.expected_revenue,
        currency=request.currency,
        return_time=request.return_time,
        recommendation=request.recommendation,
        ecommerce_separate=request.ecommerce_separate,
    )
    audit_event_id = audit_cerebro_action(
        action="create_approval_request",
        actor=actor,
        status="pending_ceo",
        detail="CEREBRO prepared a CEO approval request with money matrix.",
        state=CerebroState.waiting_ceo,
        destination=request.requested_by_department,
        reason=request.description,
        requires_ceo_approval=True,
    )
    approval = CerebroApprovalRequest(
        id=f"cerebro_approval_{uuid4()}",
        title=request.title,
        description=request.description,
        action_type=request.action_type,
        requested_by_department=request.requested_by_department,
        authority_level=CerebroAuthorityLevel.ceo_approval_required,
        economic_matrix=matrix,
        risk=request.risk,
        recommendation=request.recommendation,
        status="pending_ceo",
        requires_ceo_approval=True,
        audit_trail=[audit_event_id],
        created_at=now,
        updated_at=now,
    )
    insert_payload(CEREBRO_APPROVAL_REQUESTS_TABLE, approval.id, approval.model_dump_json())
    return approval


def update_approval_request_status(
    request_id: str,
    action: str,
    request: CerebroApprovalActionRequest,
    actor: AuthenticatedUser,
) -> CerebroApprovalRequest:
    payload = fetch_payload(CEREBRO_APPROVAL_REQUESTS_TABLE, request_id)
    if payload is None:
        raise CerebroError(404, {"error": "cerebro_approval_request_not_found", "request_id": request_id})
    approval = CerebroApprovalRequest(**payload)
    now = utc_now()
    approval.status = "approved" if action == "approve" else "rejected"
    if action == "approve":
        approval.approved_by = actor_name(actor)
    else:
        approval.rejected_by = actor_name(actor)
    approval.updated_at = now
    audit_event_id = audit_cerebro_action(
        action=f"{action}_approval_request",
        actor=actor,
        status=approval.status,
        detail=f"CEO {action}d a CEREBRO approval request.",
        state=CerebroState.approved if action == "approve" else CerebroState.rejected,
        destination=approval.requested_by_department,
        reason=request.evidence or request.reason or approval.description,
        requires_ceo_approval=True,
    )
    approval.audit_trail.insert(0, audit_event_id)
    update_payload(CEREBRO_APPROVAL_REQUESTS_TABLE, approval.id, approval.model_dump_json())
    return approval


def build_checkpoint(checkpoint_type: str) -> CerebroCheckpoint:
    try:
        seed_chief_of_staff_defaults()
    except Exception:
        pass
    goals = safe_call(list_company_goals, [])
    missions = safe_call(list_missions, [])[:6]
    alerts = safe_call(list_alerts, [])[:6]
    approvals = [
        approval
        for approval in safe_call(list_approval_requests, [])
        if approval.status == "pending_ceo"
    ][:6]
    title_map = {
        "morning": "Checkpoint de manana",
        "midday": "Checkpoint de mediodia",
        "evening": "Checkpoint de tarde",
    }
    summary_map = {
        "morning": "CEREBRO fija prioridad, misiones, oportunidades y riesgos antes de operar.",
        "midday": "CEREBRO verifica avances, bloqueos y senales que pueden generar ingresos.",
        "evening": "CEREBRO cierra avances, aprendizajes y pendientes para el siguiente dia.",
    }
    return CerebroCheckpoint(
        id=f"checkpoint_{checkpoint_type}_{peru_now()}",
        type=checkpoint_type,
        title=title_map[checkpoint_type],
        summary=summary_map[checkpoint_type],
        generated_at=peru_now(),
        goals=goals,
        missions=missions,
        alerts=alerts,
        approval_requests=approvals,
    )


def get_chief_of_staff_status() -> CerebroChiefOfStaffStatus:
    fallback = False
    try:
        seed_chief_of_staff_defaults()
    except Exception:
        fallback = True
    goals = safe_call(list_company_goals, [])
    department_goals = safe_call(list_department_goals, [])
    missions = [
        mission
        for mission in safe_call(list_missions, [])
        if mission.state
        not in {CerebroMissionState.completed, CerebroMissionState.rejected}
    ][:8]
    approvals = [
        approval
        for approval in safe_call(list_approval_requests, [])
        if approval.status == "pending_ceo"
    ][:8]
    alerts = safe_call(list_alerts, [])[:8]
    checkpoints = [
        safe_checkpoint("morning"),
        safe_checkpoint("midday"),
        safe_checkpoint("evening"),
    ]
    fallback = fallback or not goals or any(checkpoint.summary == SAFE_FALLBACK_MESSAGE for checkpoint in checkpoints)
    return CerebroChiefOfStaffStatus(
        status="ok" if fallback else "cerebro_chief_of_staff_os_prepared",
        mode="degraded" if fallback else "prepared",
        fallback=fallback,
        count=len(missions),
        requires_ceo_action=bool(approvals),
        message=SAFE_FALLBACK_MESSAGE if fallback else "CEREBRO Chief of Staff status prepared.",
        role="Chief of Staff OS / Jefe de Gabinete IA",
        motto="El tiempo es dinero",
        autonomy_policy="prepared_no_external_runtime",
        autonomy_summary=(
            "CEREBRO puede mover prioridades, misiones, auditorias y departamentos sin pedir permiso "
            "cuando no hay dinero real, credenciales, cuenta externa nueva, SUNAT real ni riesgo alto."
        ),
        pending_definitions_status="tracked_or_unknown",
        company_goals=goals,
        department_goals=department_goals,
        active_missions=missions,
        alerts=alerts,
        approval_requests=approvals,
        authority_matrix=build_authority_matrix(),
        checkpoints=checkpoints,
        memory_policy="Memoria de negocio sin secretos, credenciales ni tokens.",
        business_memory=[
            "Meta global: USD 6,000/mes sin e-commerce.",
            "Meta e-commerce separada: USD 10,000/mes.",
            "Toda solicitud de dinero debe mostrar inversion, ingreso esperado, utilidad neta, riesgo y retorno.",
            "DCFT y SENTINELA solo avanzan por flujo gobernado/preparado; sin runtime real en Bloque H.",
            "Real World Connections se prepara como inventario; CEREBRO no conecta cuentas, pagos, credenciales ni APIs externas sin CEO.",
            "Social Identity Map separa cuentas unknown/prepared/proposed; CEREBRO no crea cuentas ni publica real sin evidencia y CEO.",
            "E-commerce USD 10,000 es meta separada; SNIFF AMAZON / CHIEF AMAZON es radar preparado, sin Amazon Seller, inventario, pagos, scraping ni productos ganadores inventados.",
            "Real World Execution Queue es backlog preparado; CEREBRO prioriza, bloquea o pide aprobacion, pero no ejecuta acciones reales, pagos, cuentas, publicaciones ni APIs externas.",
        ],
        bus_status="prepared_internal_routes",
        auditoria_status="prepared_review_gate",
        forja_status="prepared_internal_department",
        nube_status="prepared_control_tower",
        centro_ceo_status="integrated_with_daily_center",
        generated_at=utc_now(),
    )


def safe_call(factory, fallback):
    try:
        return factory()
    except Exception:
        return fallback


def safe_checkpoint(checkpoint_type: str) -> CerebroCheckpoint:
    try:
        return build_checkpoint(checkpoint_type)
    except Exception:
        title_map = {
            "morning": "Checkpoint de manana",
            "midday": "Checkpoint de mediodia",
            "evening": "Checkpoint de tarde",
        }
        return CerebroCheckpoint(
            id=f"checkpoint_{checkpoint_type}_{peru_now()}",
            type=checkpoint_type,
            title=title_map.get(checkpoint_type, "Checkpoint"),
            summary=SAFE_FALLBACK_MESSAGE,
            generated_at=peru_now(),
            goals=[],
            missions=[],
            alerts=[],
            approval_requests=[],
        )


def list_cerebro_decisions() -> list[CerebroDecision]:
    return safe_models(CerebroDecision, fetch_payloads(CEREBRO_DECISIONS_TABLE))


def list_cerebro_tasks() -> list[CerebroTask]:
    return safe_models(CerebroTask, fetch_payloads(CEREBRO_TASKS_TABLE))


def create_cerebro_decision(
    request: CerebroDecisionCreate,
    actor: AuthenticatedUser,
) -> CerebroDecision:
    ensure_cerebro_schema()
    now = utc_now()
    decision_id = f"cerebro-decision-{uuid4()}"
    audit_event_id = audit_cerebro_action(
        action="create_decision",
        actor=actor,
        status=request.state.value,
        detail="CEREBRO prepared an internal CEO decision.",
        state=request.state,
        reason=request.reason,
        requires_ceo_approval=request.requires_ceo_approval,
    )
    decision = CerebroDecision(
        id=decision_id,
        title=request.title,
        description=request.description,
        priority=request.priority,
        state=request.state,
        requested_by=actor_name(actor),
        actor_role=actor_role(actor),
        reason=request.reason,
        requires_ceo_approval=request.requires_ceo_approval,
        audit_event_id=audit_event_id,
        created_at=now,
        updated_at=now,
    )
    insert_payload(CEREBRO_DECISIONS_TABLE, decision.id, decision.model_dump_json())
    return decision


def resolve_task_route(request: CerebroTaskCreate) -> tuple[str, str, CerebroState, bool, bool, str]:
    destination = normalize_destination(request.destination)
    if destination in PROTECTED_DESTINATIONS:
        label = PROTECTED_DESTINATIONS[destination]
        return (
            destination,
            label,
            CerebroState.blocked,
            True,
            True,
            f"{label} remains protected/no-touch and cannot receive operational tasks.",
        )
    if destination in FORBIDDEN_DESTINATIONS:
        return (
            destination,
            destination.replace("_", " ").upper(),
            CerebroState.blocked,
            True,
            True,
            FORBIDDEN_DESTINATIONS[destination],
        )
    if destination not in ALLOWED_DESTINATIONS:
        return (
            destination,
            destination.replace("_", " ").upper(),
            CerebroState.blocked,
            True,
            True,
            "Destination is not allowed for CEREBRO operational runtime.",
        )
    return (
        destination,
        ALLOWED_DESTINATIONS[destination],
        request.state or CerebroState.delegated,
        False,
        bool(request.requires_ceo_approval) if request.requires_ceo_approval is not None else False,
        "Internal task prepared without external runtime execution.",
    )


def create_cerebro_task(
    request: CerebroTaskCreate,
    actor: AuthenticatedUser,
) -> CerebroTask:
    ensure_cerebro_schema()
    now = utc_now()
    destination, label, state, blocked, requires_ceo, default_reason = resolve_task_route(request)
    reason = safe_reason(request.reason, default_reason)
    task_id = f"cerebro-task-{uuid4()}"
    bus_route_id = None
    bus_dispatch_id = None
    handler_result: dict = {}
    route_dispatched = False
    if not blocked:
        bus_route_id = route_id_for_cerebro_target(destination)
        if bus_route_id:
            dispatch = dispatch_message(
                IntegrationDispatchRequest(
                    route_id=bus_route_id,
                    subject=task_id,
                    payload={
                        "task_id": task_id,
                        "title": request.title,
                        "description": request.description,
                        "destination": destination,
                        "priority": request.priority,
                    },
                    metadata={
                        "source": "cerebro.operational_runtime",
                        "created_by": actor_name(actor),
                        "role": actor_role(actor),
                        "external_connection_enabled": False,
                        "runtime_connected": False,
                    },
                )
            )
            if dispatch:
                bus_dispatch_id = dispatch.id
                handler_result = dispatch.handler_result
                route_dispatched = True
    audit_event_id = audit_cerebro_action(
        action="create_task",
        actor=actor,
        status=state.value,
        detail=(
            "CEREBRO blocked a prohibited operational destination."
            if blocked
            else "CEREBRO delegated an internal task without external runtime execution."
        ),
        state=state,
        destination=destination,
        reason=reason,
        requires_ceo_approval=requires_ceo,
        blocked=blocked,
    )
    task = CerebroTask(
        id=task_id,
        title=request.title,
        description=request.description,
        destination=destination,
        destination_label=label,
        priority=request.priority,
        state=state,
        blocked=blocked,
        reason=reason,
        requested_by=actor_name(actor),
        actor_role=actor_role(actor),
        requires_ceo_approval=requires_ceo,
        route_dispatched=route_dispatched,
        bus_route_id=bus_route_id,
        bus_dispatch_id=bus_dispatch_id,
        handler_result=handler_result,
        audit_event_id=audit_event_id,
        created_at=now,
        updated_at=now,
    )
    insert_payload(CEREBRO_TASKS_TABLE, task.id, task.model_dump_json())
    return task


def update_cerebro_task_state(
    task_id: str,
    request: CerebroTaskStateUpdate,
    actor: AuthenticatedUser,
) -> CerebroTask:
    payload = fetch_payload(CEREBRO_TASKS_TABLE, task_id)
    if payload is None:
        raise CerebroError(
            status_code=404,
            detail={"error": "cerebro_task_not_found", "task_id": task_id},
        )

    task = CerebroTask(**payload)
    if task.blocked and request.state != CerebroState.blocked:
        raise CerebroError(
            status_code=400,
            detail={
                "error": "blocked_task_state_locked",
                "task_id": task.id,
                "destination": task.destination,
                "state": task.state.value,
            },
        )

    task.state = request.state
    task.reason = safe_reason(request.reason, task.reason)
    task.updated_at = utc_now()
    task.audit_event_id = audit_cerebro_action(
        action="update_task_state",
        actor=actor,
        status=task.state.value,
        detail="CEREBRO task state was updated internally.",
        state=task.state,
        destination=task.destination,
        reason=task.reason,
        requires_ceo_approval=task.requires_ceo_approval,
        blocked=task.blocked,
    )
    update_payload(CEREBRO_TASKS_TABLE, task.id, task.model_dump_json())
    return task


def cerebro_chat_title(message: str, fallback: str) -> str:
    clean = " ".join(str(message or "").split())
    if not clean:
        clean = fallback
    return clean[:176]


def cerebro_chat_intent(request: CerebroChatRequest) -> str:
    if request.action != "auto":
        return request.action
    message = str(request.message or "").lower()
    office = normalize_destination(request.office)
    if office == "centinela":
        return "centinela"
    if office == "forja":
        return "forja"
    if any(
        token in message
        for token in (
            "revisa inteligencia",
            "revisa inteligencia externa",
            "alertas externas",
            "alertas de sombra",
            "mensajes de sombra",
            "inteligencia entrante",
            "inteligencia externa",
            "resume briefing",
            "briefing",
            "sombra",
        )
    ):
        return "sombra_inbox"
    if any(token in message for token in ("amenaza", "cliente en riesgo", "consulta centinela")):
        return "centinela"
    if any(token in message for token in ("implementa", "construye", "desarrolla", "parche")):
        return "forja"
    if any(token in message for token in ("organiza esto", "prepara mision", "crea mision")):
        return "mission"
    if any(token in message for token in ("linkedin", "publicacion", "venta", "mensaje", "campana", "cliente", "marketing", "pluma")):
        return "commercial"
    if any(token in message for token in ("centinela", "sentinela", "seguridad", "riesgo", "alerta")):
        return "centinela"
    if any(token in message for token in ("forja", "codigo", "código", "implementar", "construir", "arreglar")):
        return "forja"
    if any(token in message for token in ("mision", "misión", "objetivo", "plan", "prioridad", "seguimiento")):
        return "mission"
    return "info"


def cerebro_chat_state() -> CerebroChatState:
    terminal_states = {
        CerebroMissionState.blocked,
        CerebroMissionState.completed,
        CerebroMissionState.failed,
        CerebroMissionState.rejected,
    }
    missions = [mission for mission in list_missions() if mission.state not in terminal_states]
    forja_tasks = [
        task
        for task in list_cerebro_tasks()
        if task.destination == "forja" and not task.blocked and task.state != CerebroState.blocked
    ]
    centinela_status = get_centinela_status()
    inbox_metrics = safe_call(get_sombra_inbox_metrics, {})
    return CerebroChatState(
        missions_active=len(missions),
        forja_tasks=len(forja_tasks),
        centinela_status=centinela_status.status,
        sombra_connected=centinela_status.sombra_connected,
        external_intel_messages=int(inbox_metrics.get("external_intel_messages", 0) or 0),
        critical_alerts=int(inbox_metrics.get("critical_alerts", 0) or 0),
        high_alerts=int(inbox_metrics.get("high_alerts", 0) or 0),
        lead_signals=int(inbox_metrics.get("lead_signals", 0) or 0),
        commercial_drafts=len(safe_call(list_commercial_drafts, [])),
        ceo_codes_pending=list(inbox_metrics.get("ceo_codes_pending", []) or []),
        last_heartbeat_at=inbox_metrics.get("last_heartbeat_at"),
    )


def run_cerebro_chat(request: CerebroChatRequest, actor: AuthenticatedUser) -> CerebroChatResponse:
    ensure_cerebro_schema()
    intent = cerebro_chat_intent(request)
    message = " ".join(request.message.split())
    actions: list[CerebroChatAction] = []

    if intent == "mission":
        mission = create_mission(
            CerebroMissionCreate(
                title=cerebro_chat_title(message, "Mision interna desde CEREBRO"),
                objective=message,
                origin="ceo_cerebro_chat",
                leader_department="CEREBRO",
                involved_departments=["CEREBRO"],
                priority=request.priority,
                action_type="create_internal_mission",
                state=CerebroMissionState.assigned,
                risks=["Sin acciones externas ejecutadas desde el chat."],
                requires_money=False,
                requires_ceo_approval=False,
                expected_report="Reporte ejecutivo a CEO con accion registrada por CEREBRO.",
            ),
            actor,
        )
        actions.append(
            CerebroChatAction(
                type="mission_created",
                status="created",
                id=mission.id,
                label=mission.title,
                detail="Mision interna trazable creada por CEREBRO.",
            )
        )
        reply = (
            "Daniel, recibi la instruccion y cree una mision interna trazable. "
            "Queda lista para seguimiento ejecutivo sin tocar runtimes externos."
        )
    elif intent == "forja":
        task = create_cerebro_task(
            CerebroTaskCreate(
                title=cerebro_chat_title(message, "Trabajo interno para FORJA"),
                description=message,
                destination="FORJA",
                priority=request.priority,
                reason="Trabajo enviado desde CEREBRO a FORJA en modo interno.",
                requires_ceo_approval=False,
            ),
            actor,
        )
        actions.append(
            CerebroChatAction(
                type="forja_task_created",
                status="blocked" if task.blocked else "created",
                id=task.id,
                label=task.title,
                detail=task.reason,
            )
        )
        reply = (
            "Daniel, envie el trabajo a FORJA como tarea interna. "
            "Queda registrado para construccion controlada, sin ejecutar codigo ni tocar repos externos."
        )
    elif intent == "centinela":
        centinela = get_centinela_status()
        actions.append(
            CerebroChatAction(
                type="centinela_status",
                status="prepared",
                id="centinela-status-internal",
                label="CENTINELA interno",
                detail=centinela.message,
            )
        )
        reply = (
            f"Daniel, CENTINELA esta en modo {centinela.status}. "
            f"Nivel de amenaza: {centinela.threat_level}. Mensajes internos: {centinela.external_intel_messages}. "
            "No consulte el servidor externo de SOMBRA ni expuse payload sensible."
        )
    elif intent == "commercial":
        draft = create_cerebro_commercial_draft(
            CerebroCommercialDraftCreate(
                source="cerebro_chat",
                title=cerebro_chat_title(message, "Borrador comercial defensivo"),
                summary=message,
                safe_for_commercial_use=True,
            ),
            actor,
        )
        actions.append(
            CerebroChatAction(
                type="commercial_draft_created",
                status="created",
                id=draft.id,
                label=draft.title,
                detail="Borrador PLUMA/MARKETING sanitizado creado; no se publico ni se contacto a nadie.",
            )
        )
        reply = (
            "Daniel, prepare un borrador comercial defensivo para LinkedIn/PLUMA/MARKETING. "
            "No menciona fuentes, no contiene secretos, no publica automaticamente y queda pendiente de aprobacion CEO."
        )
    elif intent == "sombra_inbox":
        recent = list_sombra_inbox_messages(limit=5)
        if recent:
            latest = recent[0]
            actions.append(
                CerebroChatAction(
                    type="sombra_inbox_reviewed",
                    status="prepared",
                    id=latest.message_id,
                    label=latest.title,
                    detail=f"{len(recent)} mensajes recientes sanitizados; payload sensible no expuesto.",
                )
            )
            reply = (
                "Daniel, recibi la inteligencia entrante en el inbox interno de CEREBRO. "
                f"La ultima senal esta clasificada como {latest.type.value}/{latest.severity.value}. "
                f"Codigo CEO pendiente: {latest.ceo_code or 'sin codigo inmediato'}. "
                f"Resumen ejecutivo: {latest.executive_summary or latest.summary}. "
                "CENTINELA puede convertirla en diagnostico de riesgo, FORJA queda preparada si requiere soporte tecnico "
                "y PLUMA/MARKETING solo trabaja borradores sanitizados sin revelar fuente ni datos sensibles."
            )
        else:
            actions.append(
                CerebroChatAction(
                    type="sombra_inbox_reviewed",
                    status="prepared",
                    id="sombra-inbox-empty",
                    label="Inbox SOMBRA de CEREBRO",
                    detail="No hay mensajes internos recientes.",
                )
            )
            reply = (
                "Daniel, el inbox interno de CEREBRO esta preparado. "
                "Todavia no hay inteligencia entrante registrada y no consulte el servidor externo de SOMBRA."
            )
    else:
        actions.append(
            CerebroChatAction(
                type="info",
                status="prepared",
                id="cerebro-internal-chat",
                label="CEREBRO operativo",
                detail="Puede crear mision, enviar trabajo a FORJA o consultar CENTINELA.",
            )
        )
        reply = (
            "Daniel, estoy operativo como centro de mando interno: puedo convertir instrucciones "
            "en misiones, tareas para FORJA o lecturas de CENTINELA sin acciones externas."
        )

    return CerebroChatResponse(
        ok=True,
        reply=reply,
        actions=actions,
        state=cerebro_chat_state(),
        provider="internal",
    )


def get_cerebro_status() -> CerebroStatus:
    ensure_cerebro_schema()
    decisions = list_cerebro_decisions()
    tasks = list_cerebro_tasks()
    blocked_tasks = [task for task in tasks if task.blocked or task.state == CerebroState.blocked]
    pending_decisions = [
        decision
        for decision in decisions
        if decision.state
        in {CerebroState.draft, CerebroState.proposed, CerebroState.waiting_ceo}
    ]
    return CerebroStatus(
        status="cerebro_operational_internal",
        mode="internal_backend_control_center_only",
        role="Chief of Staff / Jefe de Gabinete IA",
        allowed_departments=list(ALLOWED_DESTINATIONS.values()),
        protected_targets=list(PROTECTED_DESTINATIONS.values()),
        decisions=len(decisions),
        tasks=len(tasks),
        blocked_tasks=len(blocked_tasks),
        pending_decisions=len(pending_decisions),
        generated_at=utc_now(),
    )


def build_brief(brief_type: str) -> CerebroDailyBrief:
    ensure_cerebro_schema()
    decisions = list_cerebro_decisions()
    tasks = list_cerebro_tasks()
    blocked = [task for task in tasks if task.blocked or task.state == CerebroState.blocked]
    pending = [
        decision
        for decision in decisions
        if decision.state
        in {CerebroState.draft, CerebroState.proposed, CerebroState.waiting_ceo}
    ]

    if brief_type == "morning":
        headline = "Reunión de mañana con CEREBRO"
        summary = (
            "CEREBRO lee el estado interno, prepara prioridades y escala al CEO "
            "lo que requiere decisión humana."
        )
    elif brief_type == "evening":
        headline = "Reunión de tarde con CEREBRO"
        summary = (
            "CEREBRO resume tareas internas, bloqueos y decisiones que quedan "
            "para el siguiente ciclo."
        )
    else:
        headline = "Resumen ejecutivo CEREBRO"
        summary = (
            "CEREBRO opera dentro del backend/control center, sin apps protegidas "
            "ni runtimes externos."
        )

    return CerebroDailyBrief(
        type=brief_type,
        headline=headline,
        summary=summary,
        decisions=pending[:8],
        tasks=tasks[:8],
        blocked=blocked[:8],
        allowed_departments=list(ALLOWED_DESTINATIONS.values()),
        protected_targets=list(PROTECTED_DESTINATIONS.values()),
        requires_ceo_approval=bool(pending or blocked),
        generated_at=utc_now(),
    )
