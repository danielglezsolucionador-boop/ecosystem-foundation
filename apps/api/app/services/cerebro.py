from datetime import UTC, datetime
import hashlib
import hmac
import json
from os import environ
import re
import unicodedata
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
    CerebroConversationDetail,
    CerebroConversationMessage,
    CerebroConversationSummary,
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
    SombraReportClassification,
)
from app.schemas.integration_bus import IntegrationDispatchRequest
from app.services.audit import create_audit_event
from app.services.bunker_vault import (
    archive_sealed_report,
    archive_sombra_event_metadata,
    get_sealed_report_by_original_message_id,
)
from app.services.centinela import analyze_operational_report, get_centinela_status
from app.services.cerebro_llm import generate_reply as generate_cerebro_reply
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
CEREBRO_CONVERSATIONS_TABLE = "cerebro_conversations"
CEREBRO_MESSAGES_TABLE = "cerebro_messages"

PERU_TZ = ZoneInfo("America/Lima")
GLOBAL_MONTHLY_GOAL_USD = 6000.0
ECOMMERCE_MONTHLY_GOAL_USD = 10000.0
CEREBRO_FIXED_OPERATION_INSTRUCTION = (
    "CEREBRO opera como orquestador ejecutivo del ecosistema. Cuando reciba o detecte "
    "inteligencia externa, bug bounty, recompensas, plata, reclamar, reportes, ultimo "
    "escaneo o sistema discreto, debe leer datos reales del inbox interno, no responder "
    "generico, clasificar la informacion y producir salidas accionables para CEO, FORJA, "
    "PLUMA, MARCA PERSONAL, CENTINELA y AUDITORIA."
)

SOMBRA_PRODUCTIVE_CLASSIFICATIONS = {
    "INFORME_BUG_BOUNTY",
    "TAREA_FORJA",
    "BORRADOR_LINKEDIN",
    "ALERTA_CENTINELA",
    "DESCARTADO",
    "PENDIENTE_EVIDENCIA",
}

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
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CEREBRO_CONVERSATIONS_TABLE} (
                id TEXT PRIMARY KEY,
                owner_id TEXT NOT NULL,
                owner TEXT NOT NULL,
                title TEXT NOT NULL,
                context TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{{}}',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {CEREBRO_MESSAGES_TABLE} (
                id TEXT PRIMARY KEY,
                conversation_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                source TEXT NOT NULL,
                metadata_json TEXT NOT NULL DEFAULT '{{}}',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_cerebro_conversations_owner_updated ON {CEREBRO_CONVERSATIONS_TABLE} (owner_id, updated_at)"
        )
        connection.execute(
            f"CREATE INDEX IF NOT EXISTS idx_cerebro_messages_conversation_created ON {CEREBRO_MESSAGES_TABLE} (conversation_id, created_at)"
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
    if message.classification == SombraReportClassification.secreto_militar_ceo:
        return ["bunker"]
    routes = list(dict.fromkeys(str(item) for item in message.audience))
    if "centinela" not in routes:
        routes.append("centinela")
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
        message.safe_for_commercial_use
        and message.type.value in {"briefing", "scan_report", "lead_signal"}
        and not manual_review_required
    )
    commercial_summary = (
        build_commercial_safe_summary(message, top_points)
        if commercial_draft_ready
        else None
    )
    event_metrics = extract_sombra_scan_metrics(
        {
            "type": message.type.value,
            "severity": message.severity.value,
            "title": message.title,
            "summary": message.summary,
            "payload": message.payload,
            "metadata": message.metadata,
            "safe_for_commercial_use": message.safe_for_commercial_use,
        }
    )
    productive_classification = classify_sombra_productive_event(
        {
            "type": message.type.value,
            "severity": message.severity.value,
            "title": message.title,
            "summary": message.summary,
            "payload": message.payload,
            "metadata": message.metadata,
            "routed_to": determine_sombra_routes(message),
            "safe_for_commercial_use": message.safe_for_commercial_use,
        },
        event_metrics,
    )
    return {
        "policy": CEREBRO_CYBER_INTELLIGENCE_POLICY["name"],
        "fixed_operation_instruction": CEREBRO_FIXED_OPERATION_INSTRUCTION,
        "productive_classification": productive_classification,
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
                "classification": message.classification.value,
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
    classification = str(metadata.get("report_classification") or "OPERATIVO_DEFENSIVO")
    return SombraInboxRecentMessage(
        id=get_row_value(row, "id"),
        message_id=get_row_value(row, "message_id"),
        source=get_row_value(row, "source"),
        classification=SombraReportClassification(classification),
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

    if message.classification == SombraReportClassification.secreto_militar_ceo:
        sealed_report = archive_sealed_report(message, raw_body=raw_body)
        return SombraInboxMessageResponse(
            ok=True,
            received=True,
            message_id=message.message_id,
            stored=True,
            classification=message.classification,
            sealed=True,
            bunker_entry_id=sealed_report.id,
            severity=message.severity,
            routed_to=["bunker"],
            executive_summary=None,
            commercial_draft_ready=False,
            manual_review_required=True,
            internal_actions=[
                {
                    "type": "sealed_report_archived",
                    "id": sealed_report.id,
                    "target": "bunker",
                    "vault_path": sealed_report.vault_path,
                    "content_sha256": sealed_report.content_sha256,
                    "content_size_bytes": str(sealed_report.content_size_bytes),
                }
            ],
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
                classification=message.classification,
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
            "report_classification": message.classification.value,
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
        classification=message.classification,
        severity=message.severity,
        ceo_code=protocol["ceo_code"],
        immediate_ceo_attention=bool(protocol["immediate_ceo_attention"]),
        routed_to=routed_to,
        executive_summary=str(protocol["executive_summary"]),
        commercial_draft_ready=bool(protocol["commercial_draft_ready"]),
        manual_review_required=bool(protocol["manual_review_required"]),
        internal_actions=internal_actions,
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


def _row_to_sombra_context(row: object) -> dict[str, object]:
    metadata = _json_load(get_row_value(row, "metadata_json", default="{}"), {})
    payload = _json_load(get_row_value(row, "payload_json", default='""'), "")
    routed_to = _json_load(get_row_value(row, "routed_to_json", default="[]"), [])
    return {
        "message_id": get_row_value(row, "message_id"),
        "source": get_row_value(row, "source"),
        "type": get_row_value(row, "message_type"),
        "severity": get_row_value(row, "severity"),
        "created_at": get_row_value(row, "source_created_at"),
        "received_at": get_row_value(row, "received_at"),
        "title": get_row_value(row, "title"),
        "summary": get_row_value(row, "summary"),
        "routed_to": list(routed_to) if isinstance(routed_to, list) else [],
        "ceo_code": get_row_value(row, "ceo_code", default=None),
        "executive_summary": get_row_value(row, "executive_summary", default=None),
        "payload": payload,
        "metadata": sanitize_metadata(metadata) if isinstance(metadata, dict) else {},
    }


def list_sombra_inbox_context(limit: int = 5) -> list[dict[str, object]]:
    ensure_sombra_inbox_schema()
    safe_limit = max(1, min(int(limit or 5), 20))
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM {CEREBRO_SOMBRA_INBOX_TABLE}
            ORDER BY received_at DESC
            LIMIT {safe_limit}
            """
        ).fetchall()
    return [_row_to_sombra_context(row) for row in rows]


EVENT_TRACE_FIELDS = (
    "message_id",
    "received_at",
    "source",
    "classification",
    "bunker_status",
    "bunker_id",
    "bunker_path_or_key",
    "audit_status",
    "audit_id",
    "centinela_status",
    "centinela_alert_id",
    "centinela_response_summary",
    "forja_status",
    "forja_task_id",
    "arsenal_status",
    "arsenal_artifact_id",
    "linkedin_status",
    "draft_id",
    "decision_ceo",
    "missing_steps",
)


def _empty_event_trace(message_id: str) -> dict[str, object]:
    return {
        "message_id": message_id,
        "received_at": None,
        "source": None,
        "classification": None,
        "bunker_status": "no",
        "bunker_id": None,
        "bunker_path_or_key": None,
        "audit_status": "no",
        "audit_id": None,
        "centinela_status": "no",
        "centinela_alert_id": None,
        "centinela_response_summary": None,
        "forja_status": "no aplica",
        "forja_task_id": None,
        "arsenal_status": "no aplica",
        "arsenal_artifact_id": None,
        "linkedin_status": "no aplica",
        "draft_id": None,
        "decision_ceo": "Verificar message_id en inbox SOMBRA o BUNKER.",
        "missing_steps": ["message_not_found"],
    }


def get_sombra_inbox_row_by_message_id(message_id: str) -> object | None:
    ensure_sombra_inbox_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        return connection.execute(
            f"SELECT * FROM {CEREBRO_SOMBRA_INBOX_TABLE} WHERE message_id = {placeholder}",
            (message_id,),
        ).fetchone()


def _row_metadata(row: object) -> dict[str, object]:
    metadata = _json_load(get_row_value(row, "metadata_json", default="{}"), {})
    return metadata if isinstance(metadata, dict) else {}


def _row_internal_actions(row: object) -> list[dict[str, str]]:
    metadata = _row_metadata(row)
    actions = metadata.get("internal_actions", [])
    if not isinstance(actions, list):
        return []
    normalized: list[dict[str, str]] = []
    for action in actions:
        if isinstance(action, dict):
            normalized.append({str(key): str(value) for key, value in action.items()})
    return normalized


def _append_trace_action(actions: list[dict[str, str]], action: dict[str, str] | None) -> bool:
    if not action:
        return False
    action_type = str(action.get("type") or "")
    action_id = str(action.get("id") or "")
    if any(
        existing.get("type") == action_type
        and (not action_id or existing.get("id") == action_id)
        for existing in actions
    ):
        return False
    actions.append({str(key): str(value) for key, value in action.items()})
    return True


def _find_action(actions: list[dict[str, str]], *action_types: str) -> dict[str, str] | None:
    expected = set(action_types)
    for action in actions:
        action_id = str(action.get("id") or "")
        if action.get("type") in expected and action_id and action_id != "unavailable":
            return action
    return None


def _persist_trace_actions(row: object, actions: list[dict[str, str]]) -> None:
    metadata = _row_metadata(row)
    metadata["internal_actions"] = actions
    placeholder = sql_placeholder()
    with connect() as connection:
        connection.execute(
            f"""
            UPDATE {CEREBRO_SOMBRA_INBOX_TABLE}
            SET metadata_json = {placeholder}, updated_at = {placeholder}
            WHERE message_id = {placeholder}
            """,
            (_json_dump(sanitize_metadata(metadata)), utc_now(), get_row_value(row, "message_id")),
        )
        connection.commit()


def _row_payload_hash(row: object) -> tuple[str, int]:
    payload_json = str(get_row_value(row, "payload_json", default="") or "")
    content = payload_json.encode("utf-8")
    return hashlib.sha256(content).hexdigest(), len(content)


def _filename_from_metadata(metadata: dict[str, object], fallback: str) -> str:
    for key in ("filename", "file_name", "name", "report_file", "report_path", "file_path", "path"):
        value = metadata.get(key)
        if value:
            return str(value)
    return fallback


def _classification_from_row(row: object) -> str:
    metadata = _row_metadata(row)
    classification = str(metadata.get("report_classification") or "OPERATIVO_DEFENSIVO")
    if classification not in {item.value for item in SombraReportClassification}:
        return SombraReportClassification.operativo_defensivo.value
    return classification


def _sombra_message_from_row(row: object) -> SombraInboxMessageCreate:
    audience = _json_load(get_row_value(row, "audience_json", default="[]"), [])
    client_context = _json_load(get_row_value(row, "client_context_json", default="{}"), {})
    payload = _json_load(get_row_value(row, "payload_json", default='""'), "")
    metadata = _row_metadata(row)
    safe_audience = [
        item
        for item in (audience if isinstance(audience, list) else [])
        if item in {"cerebro", "centinela", "bunker", "ceo", "forja", "pluma", "marketing"}
    ]
    return SombraInboxMessageCreate(
        message_id=str(get_row_value(row, "message_id")),
        source="sombra",
        classification=SombraReportClassification(_classification_from_row(row)),
        type=get_row_value(row, "message_type"),
        severity=get_row_value(row, "severity"),
        created_at=str(get_row_value(row, "source_created_at")),
        title=str(get_row_value(row, "title")),
        summary=str(get_row_value(row, "summary")),
        audience=safe_audience or ["cerebro", "centinela", "bunker"],
        client_context=client_context if isinstance(client_context, dict) else {},
        safe_for_commercial_use=row_bool(row, "safe_for_commercial_use"),
        sensitive=row_bool(row, "sensitive", default=True),
        encrypted=row_bool(row, "encrypted", default=True),
        payload=payload if isinstance(payload, (str, dict)) else "",
        metadata=metadata,
    )


def _create_trace_audit_action(trace: dict[str, object]) -> dict[str, str]:
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.runtime,
            severity=AuditSeverity.info,
            source="cerebro.event_trace",
            action="trace_event",
            status="registered",
            detail="CEREBRO registered exact SOMBRA/CEREBRO event traceability without exposing payload.",
            metadata={
                "message_id": trace.get("message_id"),
                "classification": trace.get("classification"),
                "bunker_id": trace.get("bunker_id"),
                "centinela_alert_id": trace.get("centinela_alert_id"),
                "forja_task_id": trace.get("forja_task_id"),
                "arsenal_artifact_id": trace.get("arsenal_artifact_id"),
                "draft_id": trace.get("draft_id"),
                "content_included": False,
                "payload_included": False,
                "external_connection_enabled": False,
                "runtime_connected": False,
            },
        )
    )
    return {"type": "event_trace_audit_registered", "id": event.id, "target": "auditoria"}


def _create_centinela_trace_alert(
    message: SombraInboxMessageCreate,
    centinela_action: dict[str, str] | None,
) -> dict[str, str]:
    actor = service_actor()
    summary = str(
        (centinela_action or {}).get("recommendation")
        or "Alerta defensiva creada para trazabilidad SOMBRA/CEREBRO."
    )
    alert = create_alert(
        CerebroAlertCreate(
            title=cerebro_chat_title(message.title, "CENTINELA: trazabilidad defensiva SOMBRA"),
            summary=summary,
            source="cerebro_event_trace",
            relevance_score=88 if message.severity.value in {"high", "critical"} else 72,
            risk_level=message.severity.value,
            dafo=CerebroDafo(
                opportunities=["Cerrar trazabilidad defensiva por evento SOMBRA/CEREBRO."],
                threats=["Evento operativo sin alerta defensiva verificable previa."],
            ),
        ),
        actor,
    )
    return {
        "type": "centinela_alert_created",
        "id": alert.id,
        "target": "centinela",
        "summary": summary[:300],
    }


def _find_draft_for_message(message_id: str) -> str | None:
    for draft in list_commercial_drafts():
        if draft.source_message_id == message_id:
            return draft.id
    return None


def _event_trace_decision(trace: dict[str, object]) -> str:
    missing_steps = trace.get("missing_steps")
    if isinstance(missing_steps, list) and missing_steps:
        return "CEO revisar missing_steps y ordenar cierre manual de los IDs faltantes."
    return "Evento trazable; revisar IDs y aprobar solo pasos pendientes."


def trace_event(message_id: str) -> dict[str, object]:
    normalized_id = " ".join(str(message_id or "").strip().split())
    trace = _empty_event_trace(normalized_id)
    if not normalized_id:
        return {key: trace[key] for key in EVENT_TRACE_FIELDS}

    row = get_sombra_inbox_row_by_message_id(normalized_id)
    sealed_report = get_sealed_report_by_original_message_id(normalized_id)
    changed = False
    actions: list[dict[str, str]] = []
    missing_steps: list[str] = []

    if row is None:
        if sealed_report is None:
            return {key: trace[key] for key in EVENT_TRACE_FIELDS}
        trace.update(
            {
                "received_at": sealed_report.received_at,
                "source": sealed_report.source,
                "classification": sealed_report.classification,
                "bunker_status": "si",
                "bunker_id": sealed_report.id,
                "bunker_path_or_key": sealed_report.vault_path or sealed_report.id,
                "centinela_status": "no aplica",
                "forja_status": "no aplica",
                "arsenal_status": "no aplica",
                "linkedin_status": "no aplica",
                "missing_steps": [],
            }
        )
        audit_action = _create_trace_audit_action(trace)
        trace["audit_status"] = "si"
        trace["audit_id"] = audit_action["id"]
        trace["decision_ceo"] = _event_trace_decision(trace)
        return {key: trace[key] for key in EVENT_TRACE_FIELDS}

    metadata = _row_metadata(row)
    actions = _row_internal_actions(row)
    classification = _classification_from_row(row)
    trace.update(
        {
            "received_at": get_row_value(row, "received_at"),
            "source": get_row_value(row, "source"),
            "classification": classification,
        }
    )

    if sealed_report is None and str(trace["source"]).lower() == "sombra":
        payload_hash, payload_size = _row_payload_hash(row)
        sealed_report = archive_sombra_event_metadata(
            message_id=normalized_id,
            classification=classification,
            message_type=str(get_row_value(row, "message_type")),
            severity=str(get_row_value(row, "severity")),
            source_created_at=get_row_value(row, "source_created_at", default=None),
            received_at=get_row_value(row, "received_at", default=None),
            filename_or_id_value=_filename_from_metadata(metadata, normalized_id),
            content_hash=payload_hash,
            content_size_bytes=payload_size,
            metadata={
                "origin": "SOMBRA",
                "message_id": normalized_id,
                "source_table": CEREBRO_SOMBRA_INBOX_TABLE,
                "content_included": False,
                "payload_included": False,
                "local_path_is_bunker": False,
            },
        )
        changed |= _append_trace_action(
            actions,
            {
                "type": "bunker_event_metadata_archived",
                "id": sealed_report.id,
                "target": "bunker",
                "vault_path": sealed_report.vault_path,
            },
        )

    if sealed_report is not None:
        trace.update(
            {
                "bunker_status": "si",
                "bunker_id": sealed_report.id,
                "bunker_path_or_key": sealed_report.vault_path or sealed_report.id,
            }
        )
    else:
        missing_steps.append("bunker_id")

    message = _sombra_message_from_row(row)
    centinela_action = _find_action(actions, "centinela_analysis_created")
    if centinela_action is None:
        centinela_action = notify_centinela(message)
        changed |= _append_trace_action(actions, centinela_action)
    centinela_alert = _find_action(actions, "centinela_alert_created", "alert_created")
    if centinela_alert is None:
        centinela_alert = _create_centinela_trace_alert(message, centinela_action)
        changed |= _append_trace_action(actions, centinela_alert)
    if centinela_alert:
        trace["centinela_status"] = "si"
        trace["centinela_alert_id"] = centinela_alert.get("id")
    else:
        missing_steps.append("centinela_alert_id")
    trace["centinela_response_summary"] = (
        (centinela_alert or {}).get("summary")
        or (centinela_action or {}).get("recommendation")
        or (centinela_action or {}).get("impact")
    )

    forja_action = _find_action(actions, "forja_task_created")
    centinela_requires_forja = (centinela_action or {}).get("requires_forja_task") == "true"
    if forja_action is None and centinela_requires_forja:
        created_forja = create_forja_task(message, centinela_action or {}, apply_cyber_intelligence_protocol(message), service_actor())
        if created_forja:
            forja_action = created_forja
            changed |= _append_trace_action(actions, created_forja)
    if forja_action:
        trace["forja_status"] = "si"
        trace["forja_task_id"] = forja_action.get("id")
    elif centinela_requires_forja:
        trace["forja_status"] = "pendiente"
        missing_steps.append("forja_task_id")

    arsenal_action = _find_action(actions, "arsenal_artifact_registered")
    if arsenal_action is None and forja_action is not None:
        created_arsenal = register_arsenal_artifact(message, centinela_action or {}, forja_action, service_actor())
        if created_arsenal and created_arsenal.get("type") == "arsenal_artifact_registered":
            arsenal_action = created_arsenal
            changed |= _append_trace_action(actions, created_arsenal)
    if arsenal_action:
        trace["arsenal_status"] = "si"
        trace["arsenal_artifact_id"] = arsenal_action.get("id")
    else:
        reusable_requested = any(
            (centinela_action or {}).get(key) == "true"
            for key in ("requires_api", "requires_skill", "requires_tool", "requires_defensive_rule")
        )
        trace["arsenal_status"] = "pendiente" if forja_action and reusable_requested else "no aplica"
        if trace["arsenal_status"] == "pendiente":
            missing_steps.append("arsenal_artifact_id")

    draft_action = _find_action(actions, "commercial_draft_created")
    draft_id = draft_action.get("id") if draft_action else _find_draft_for_message(normalized_id)
    if draft_id:
        trace["linkedin_status"] = "si"
        trace["draft_id"] = draft_id
    else:
        trace["linkedin_status"] = "no aplica"

    trace["missing_steps"] = missing_steps
    audit_action = _find_action(actions, "event_trace_audit_registered", "auditoria_flow_registered")
    if audit_action is None:
        audit_action = _create_trace_audit_action(trace)
        changed |= _append_trace_action(actions, audit_action)
    if audit_action:
        trace["audit_status"] = "si"
        trace["audit_id"] = audit_action.get("id")
    else:
        missing_steps.append("audit_id")
        trace["missing_steps"] = missing_steps

    trace["decision_ceo"] = _event_trace_decision(trace)
    if changed:
        _persist_trace_actions(row, actions)
    return {key: trace[key] for key in EVENT_TRACE_FIELDS}


def event_trace_reply(trace: dict[str, object]) -> str:
    return json.dumps(
        {key: trace.get(key) for key in EVENT_TRACE_FIELDS},
        ensure_ascii=False,
        indent=2,
    )


def inspect_event_trace(message_id: str) -> dict[str, object]:
    normalized_id = " ".join(str(message_id or "").strip().split())
    trace = _empty_event_trace(normalized_id)
    if not normalized_id:
        return {key: trace[key] for key in EVENT_TRACE_FIELDS}

    row = get_sombra_inbox_row_by_message_id(normalized_id)
    sealed_report = get_sealed_report_by_original_message_id(normalized_id)
    if sealed_report is not None:
        trace.update(
            {
                "received_at": sealed_report.received_at,
                "source": sealed_report.source,
                "classification": sealed_report.classification,
                "bunker_status": "si",
                "bunker_id": sealed_report.id,
                "bunker_path_or_key": sealed_report.vault_path or sealed_report.id,
            }
        )

    if row is None:
        if sealed_report is not None:
            trace.update(
                {
                    "centinela_status": "no aplica",
                    "forja_status": "no aplica",
                    "arsenal_status": "no aplica",
                    "linkedin_status": "no aplica",
                    "missing_steps": ["inbox_row_not_found"],
                    "decision_ceo": "Evento sellado en BUNKER; revisar permisos CEO antes de abrir contenido.",
                }
            )
        return {key: trace[key] for key in EVENT_TRACE_FIELDS}

    actions = _row_internal_actions(row)
    classification = _classification_from_row(row)
    trace.update(
        {
            "received_at": get_row_value(row, "received_at"),
            "source": get_row_value(row, "source"),
            "classification": classification,
        }
    )

    if sealed_report is None:
        trace["missing_steps"] = ["bunker_id"]
    else:
        trace["missing_steps"] = []

    centinela_alert = _find_action(actions, "centinela_alert_created", "alert_created")
    centinela_analysis = _find_action(actions, "centinela_analysis_created")
    if centinela_alert:
        trace["centinela_status"] = "si"
        trace["centinela_alert_id"] = centinela_alert.get("id")
        trace["centinela_response_summary"] = centinela_alert.get("summary")
    elif centinela_analysis:
        trace["centinela_status"] = "si"
        trace["centinela_response_summary"] = (
            centinela_analysis.get("recommendation")
            or centinela_analysis.get("impact")
        )
        trace["missing_steps"].append("centinela_alert_id")
    else:
        trace["missing_steps"].append("centinela_alert_id")

    forja_action = _find_action(actions, "forja_task_created")
    if forja_action:
        trace["forja_status"] = "si"
        trace["forja_task_id"] = forja_action.get("id")

    arsenal_action = _find_action(actions, "arsenal_artifact_registered")
    if arsenal_action:
        trace["arsenal_status"] = "si"
        trace["arsenal_artifact_id"] = arsenal_action.get("id")

    draft_action = _find_action(actions, "commercial_draft_created")
    draft_id = draft_action.get("id") if draft_action else _find_draft_for_message(normalized_id)
    if draft_id:
        trace["linkedin_status"] = "si"
        trace["draft_id"] = draft_id

    audit_action = _find_action(actions, "event_trace_audit_registered", "auditoria_flow_registered")
    if audit_action:
        trace["audit_status"] = "si"
        trace["audit_id"] = audit_action.get("id")
    else:
        trace["missing_steps"].append("audit_id")

    trace["decision_ceo"] = _event_trace_decision(trace)
    return {key: trace[key] for key in EVENT_TRACE_FIELDS}


def _resource_name(resource: object) -> str:
    if isinstance(resource, dict):
        return str(resource.get("name") or "sin nombre")
    return str(getattr(resource, "name", "sin nombre"))


def event_office_decision_reply(
    trace: dict[str, object],
    sombra_resources: list[object],
) -> str:
    resource_names = {_resource_name(resource) for resource in sombra_resources}
    recommended_resource = (
        "Header/CSP Auditor" if "Header/CSP Auditor" in resource_names else "pendiente en ARSENAL"
    )
    registered_resource = (
        "Sombra Toolbelt" if "Sombra Toolbelt" in resource_names else "pendiente en ARSENAL"
    )
    forja_task_id = trace.get("forja_task_id") or "no existente"
    draft_id = trace.get("draft_id") or "no existente"
    audit_id = trace.get("audit_id") or "no existente"
    bunker_id = trace.get("bunker_id") or "no existente"
    bunker_path = trace.get("bunker_path_or_key") or "no existente"
    centinela_alert_id = trace.get("centinela_alert_id") or "no existente"

    return "\n".join(
        [
            "DECISION EJECUTIVA POR OFICINA: PASS",
            "",
            "EVENTO:",
            f"- message_id: {trace.get('message_id') or 'no encontrado'}",
            f"- source: {trace.get('source') or 'no encontrado'}",
            f"- classification: {trace.get('classification') or 'no encontrado'}",
            f"- bunker_status: {trace.get('bunker_status')}",
            f"- audit_status: {trace.get('audit_status')}",
            f"- centinela_status: {trace.get('centinela_status')}",
            "",
            "ARSENAL:",
            "- aplica: si, como consulta de recursos disponibles",
            f"- recurso recomendado para SOMBRA/CENTINELA: {recommended_resource}",
            f"- recurso registrado: {registered_resource}",
            "- no crear recurso nuevo sin aprobacion CEO",
            "",
            "CENTINELA:",
            "- aplica: si",
            "- accion: seguimiento defensivo",
            f"- usar centinela_alert_id existente: {centinela_alert_id}",
            "- no ejecutar accion externa",
            "",
            "FORJA:",
            "- aplica: solo si CEO aprueba construccion o mejora tecnica",
            "- no crear tarea nueva automaticamente",
            f"- forja_task_id existente/legado: {forja_task_id}",
            "",
            "PLUMA / LINKEDIN:",
            "- aplica: solo borrador educativo si CEO lo aprueba",
            "- no crear borrador nuevo automaticamente",
            f"- draft_id existente/legado: {draft_id}",
            "",
            "AUDITORIA:",
            "- aplica: si",
            f"- usar audit_id existente: {audit_id}",
            "",
            "BUNKER:",
            "- aplica: si",
            f"- usar bunker_id existente: {bunker_id}",
            f"- bunker_path_or_key: {bunker_path}",
            "",
            "DECISION CEO:",
            "- no hay dinero reclamable confirmado",
            "- no hay informe reportable listo sin evidencia",
            "- siguiente paso: validar evidencia y decidir si se autoriza FORJA o PLUMA",
            "",
            "CERO EFECTOS SECUNDARIOS:",
            "- no crear FORJA task nueva",
            "- no crear LinkedIn draft nuevo",
            "- no duplicar ARSENAL resources",
            "- no tocar SOMBRA runtime",
        ]
    )


def _safe_int(value: object) -> int | None:
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, str):
        match = re.search(r"-?\d+", value)
        if match:
            return int(match.group(0))
    return None


def _normalized_metric_text(value: object) -> str:
    text = str(value or "").lower()
    replacements = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ó": "o",
        "ú": "u",
        "ñ": "n",
    }
    for original, replacement in replacements.items():
        text = text.replace(original, replacement)
    text = unicodedata.normalize("NFKD", text)
    text = "".join(character for character in text if not unicodedata.combining(character))
    return text


SOMBRA_SCAN_METRIC_ALIASES = {
    "programs_analyzed": (
        "programs",
        "program_count",
        "programs_count",
        "programs_fetched",
        "programs_analyzed",
        "programas",
        "programas analizados",
    ),
    "local_signal_count": (
        "signals",
        "signal_count",
        "signals_loaded",
        "local_signals",
        "local_signal_count",
        "local_signals_loaded",
        "senales",
        "senales detectadas",
    ),
    "matches": (
        "matches",
        "matches_found",
        "scope_matches",
        "scope_signal_matches",
        "coincidencias",
    ),
    "reportable_opportunities": (
        "reportable",
        "reportable_count",
        "reportable_findings",
        "reportable_opportunities",
        "reportable_opportunity_count",
        "oportunidades reportables",
    ),
    "passive_findings": (
        "passive_findings",
        "passive_scope_findings",
        "hallazgos pasivos",
    ),
    "paid_program_count": (
        "paid_programs",
        "paid_program_count",
        "paid_programs_count",
        "paid_bug_bounty_programs",
        "programas pagados",
        "programas con recompensa",
    ),
}


def _iter_metric_sources(value: object) -> list[dict[str, object]]:
    sources: list[dict[str, object]] = []
    if not isinstance(value, dict):
        return sources
    sources.append(value)
    for key in ("summary", "metrics", "scan_summary", "report", "result", "counts"):
        nested = value.get(key)
        if isinstance(nested, dict):
            sources.extend(_iter_metric_sources(nested))
    return sources


def _metric_from_dict(sources: list[dict[str, object]], aliases: tuple[str, ...]) -> int | None:
    normalized_aliases = {alias.lower() for alias in aliases}
    for source in sources:
        for key, value in source.items():
            if str(key).lower() in normalized_aliases:
                parsed = _safe_int(value)
                if parsed is not None:
                    return parsed
    return None


def _metric_from_text(text: object, aliases: tuple[str, ...]) -> int | None:
    normalized = _normalized_metric_text(text)
    for alias in aliases:
        token = re.escape(_normalized_metric_text(alias))
        patterns = (
            rf"\b{token}\b\s*[:=]\s*(-?\d+)",
            rf"\b{token}\b\s+(-?\d+)",
        )
        for pattern in patterns:
            match = re.search(pattern, normalized)
            if match:
                return int(match.group(1))
    return None


def _first_value_from_sources(sources: list[dict[str, object]], aliases: tuple[str, ...]) -> object | None:
    normalized_aliases = {alias.lower() for alias in aliases}
    for source in sources:
        for key, value in source.items():
            if str(key).lower() in normalized_aliases and value not in (None, "", []):
                return value
    return None


def _compact_metric_item(value: object) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, str):
        clean = " ".join(value.split())
        return clean[:120] if clean else None
    if isinstance(value, dict):
        for key in (
            "name",
            "program",
            "program_name",
            "title",
            "domain",
            "asset",
            "signal",
            "finding",
            "company",
        ):
            if value.get(key):
                return _compact_metric_item(value.get(key))
        return _compact_metric_item(json.dumps(value, ensure_ascii=False, sort_keys=True, default=str))
    return _compact_metric_item(str(value))


def _metric_list_from_sources(
    sources: list[dict[str, object]],
    aliases: tuple[str, ...],
    *,
    limit: int = 6,
) -> list[str]:
    value = _first_value_from_sources(sources, aliases)
    items = value if isinstance(value, list) else []
    result: list[str] = []
    for item in items:
        clean = _compact_metric_item(item)
        if clean and clean not in result:
            result.append(clean)
        if len(result) == limit:
            break
    return result


def _metric_text_from_sources(sources: list[dict[str, object]], aliases: tuple[str, ...]) -> str | None:
    value = _first_value_from_sources(sources, aliases)
    if isinstance(value, (dict, list)):
        return _compact_metric_item(value)
    return _compact_metric_item(value)


def _extract_pdf_path(event: dict[str, object]) -> str | None:
    payload = event.get("payload")
    if isinstance(payload, dict):
        for key in ("pdf", "pdf_path", "report_path", "report_file"):
            value = payload.get(key)
            if value:
                return str(value)
    text = f"{event.get('summary') or ''} {event.get('executive_summary') or ''}"
    match = re.search(r"\bpdf\s*[:=]\s*([^\s]+)", text, flags=re.IGNORECASE)
    if match:
        return match.group(1)
    return None


def extract_sombra_scan_metrics(event: dict[str, object]) -> dict[str, object]:
    payload = event.get("payload")
    metadata = event.get("metadata")
    sources: list[dict[str, object]] = []
    if isinstance(payload, dict):
        sources.extend(_iter_metric_sources(payload))
    if isinstance(metadata, dict):
        sources.extend(_iter_metric_sources(metadata))
    text = " ".join(
        str(event.get(key) or "")
        for key in ("title", "summary", "executive_summary")
    )
    metrics: dict[str, object] = {}
    for metric_name, aliases in SOMBRA_SCAN_METRIC_ALIASES.items():
        parsed = _metric_from_dict(sources, aliases)
        if parsed is None:
            parsed = _metric_from_text(text, aliases)
        if parsed is not None:
            metrics[metric_name] = parsed
    program_names = _metric_list_from_sources(
        sources,
        (
            "program_names",
            "programs",
            "bug_bounty_programs",
            "programs_analyzed_details",
        ),
    )
    if program_names:
        metrics["program_names"] = program_names
        metrics.setdefault("programs_analyzed", len(program_names))
    paid_programs = _metric_list_from_sources(
        sources,
        (
            "paid_program_names",
            "paid_programs",
            "paid_bug_bounty_programs",
            "bounty_programs",
            "reward_programs",
            "programas_pagados",
        ),
    )
    if paid_programs:
        metrics["paid_programs"] = paid_programs
        metrics.setdefault("paid_program_count", len(paid_programs))
    local_signals = _metric_list_from_sources(
        sources,
        (
            "local_signals",
            "signals",
            "signals_loaded",
            "signal_examples",
            "local_signal_examples",
        ),
    )
    if local_signals:
        metrics["local_signals"] = local_signals
        metrics.setdefault("local_signal_count", len(local_signals))
    scope_matches = _metric_list_from_sources(
        sources,
        (
            "scope_signal_matches",
            "matches",
            "matches_found",
            "confirmed_matches",
            "matched_assets",
        ),
    )
    if scope_matches:
        metrics["scope_matches"] = scope_matches
        metrics.setdefault("matches", len(scope_matches))
    reportable_items = _metric_list_from_sources(
        sources,
        (
            "reportable_items",
            "reportable_findings",
            "reportable_opportunities",
            "opportunities",
        ),
    )
    if reportable_items:
        metrics["reportable_items"] = reportable_items
        metrics.setdefault("reportable_opportunities", len(reportable_items))
    next_step = _metric_text_from_sources(
        sources,
        (
            "next_step",
            "recommended_next_step",
            "recommendation",
            "recommended_action",
            "siguiente_paso",
        ),
    )
    if next_step:
        metrics["next_step"] = next_step
    pdf_path = _extract_pdf_path(event)
    if pdf_path:
        metrics["pdf_path"] = pdf_path
    return metrics


def _metric_copy(metrics: dict[str, object], key: str) -> str:
    value = metrics.get(key)
    return str(value) if isinstance(value, int) else "no informado"


def _metric_list_copy(metrics: dict[str, object], key: str, empty: str) -> str:
    value = metrics.get(key)
    if not isinstance(value, list) or not value:
        return empty
    return ", ".join(str(item) for item in value[:6])


def select_sombra_context_event(events: list[dict[str, object]]) -> dict[str, object] | None:
    if not events:
        return None
    meaningful = [
        event
        for event in events
        if str(event.get("type") or "").lower() != "heartbeat"
    ]
    reports = [
        event
        for event in meaningful
        if str(event.get("type") or "").lower() in {"scan_report", "order_result", "briefing", "lead_signal"}
    ]
    if reports:
        return reports[0]
    priority = [
        event
        for event in meaningful
        if str(event.get("severity") or "").lower() in {"critical", "high"}
    ]
    if priority:
        return priority[0]
    if meaningful:
        return meaningful[0]
    return events[0]


def _event_metadata(event: dict[str, object]) -> dict[str, object]:
    metadata = event.get("metadata")
    return metadata if isinstance(metadata, dict) else {}


def _event_protocol(event: dict[str, object]) -> dict[str, object]:
    protocol = _event_metadata(event).get("cyber_intelligence_protocol")
    return protocol if isinstance(protocol, dict) else {}


def _event_bool(event: dict[str, object], key: str) -> bool:
    value = event.get(key)
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on", "si"}
    return bool(value)


def classify_sombra_productive_event(
    event: dict[str, object],
    metrics: dict[str, object] | None = None,
) -> str:
    metrics = metrics or extract_sombra_scan_metrics(event)
    protocol = _event_protocol(event)
    existing = str(protocol.get("productive_classification") or "").strip().upper()
    if existing in SOMBRA_PRODUCTIVE_CLASSIFICATIONS:
        return existing

    metadata = _event_metadata(event)
    text = _normalized_metric_text(
        " ".join(
            [
                str(event.get("type") or ""),
                str(event.get("severity") or ""),
                str(event.get("title") or ""),
                str(event.get("summary") or ""),
                json.dumps(metadata, ensure_ascii=False, default=str),
                json.dumps(event.get("payload") or {}, ensure_ascii=False, default=str),
            ]
        )
    )
    event_type = str(event.get("type") or "").lower()
    severity = str(event.get("severity") or "").lower()
    routes = [str(route).lower() for route in event.get("routed_to", []) if route]
    reportable_count = metrics.get("reportable_opportunities")
    paid_program_count = metrics.get("paid_program_count")
    has_reportable = isinstance(reportable_count, int) and reportable_count > 0
    has_paid_programs = isinstance(paid_program_count, int) and paid_program_count > 0
    manual_review = bool(
        metadata.get("manual_review_required")
        or metadata.get("requires_manual_review")
        or metadata.get("force_manual_review")
        or event.get("manual_review_required")
    )

    if manual_review:
        return "PENDIENTE_EVIDENCIA"
    if has_reportable:
        return "INFORME_BUG_BOUNTY"
    if (
        event_type in {"scan_report", "order_result"}
        and (
            "bug bounty" in text
            or "recompensa" in text
            or "paid" in text
            or has_paid_programs
            or metrics.get("program_names")
        )
    ):
        return "PENDIENTE_EVIDENCIA"
    if event_type == "lead_signal" or _event_bool(event, "safe_for_commercial_use") or any(
        token in text for token in ("linkedin", "pluma", "marca personal", "contenido")
    ):
        return "BORRADOR_LINKEDIN"
    if severity in {"critical", "high"} or event_type == "alert" or any(
        token in text for token in ("riesgo", "amenaza", "intrusion", "credencial", "cve")
    ):
        return "ALERTA_CENTINELA"
    if "forja" in routes or any(
        token in text
        for token in ("forja", "parche", "patch", "api", "skill", "herramienta", "diagnostico", "hardening")
    ):
        return "TAREA_FORJA"
    return "DESCARTADO"


def _metric_value_or_zero(metrics: dict[str, object], key: str) -> int:
    value = metrics.get(key)
    return value if isinstance(value, int) else 0


def _money_claimable_confirmed(event: dict[str, object], metrics: dict[str, object]) -> bool:
    metadata = _event_metadata(event)
    return bool(
        metrics.get("money_claimable_confirmed")
        or metadata.get("money_claimable_confirmed")
        or metadata.get("evidence_confirmed")
    )


def _sombra_output_counts(classification: str, metrics: dict[str, object]) -> dict[str, int]:
    reportable_count = _metric_value_or_zero(metrics, "reportable_opportunities")
    ready_reports = reportable_count if classification == "INFORME_BUG_BOUNTY" else 0
    pending_evidence = 1 if classification == "PENDIENTE_EVIDENCIA" else 0
    discarded = 1 if classification == "DESCARTADO" else 0
    return {
        "ready_reports": ready_reports,
        "pending_evidence": pending_evidence,
        "discarded": discarded,
    }


def build_sombra_production_reply(
    latest: dict[str, object],
    events: list[dict[str, object]],
    metrics: dict[str, object],
    classification: str,
) -> tuple[str, dict[str, object]]:
    programs_line = _metric_list_copy(metrics, "program_names", "no informado")
    paid_programs_line = _metric_list_copy(metrics, "paid_programs", "no informado")
    signals_line = _metric_list_copy(metrics, "local_signals", "no informado")
    matches_line = _metric_list_copy(metrics, "scope_matches", "sin coincidencias confirmadas")
    reportables_line = _metric_list_copy(metrics, "reportable_items", "sin items reportables confirmados")
    next_step = str(
        metrics.get("next_step")
        or "Cruzar las senales con el scope autorizado y confirmar evidencia antes de reclamar."
    )
    confirmed_money = _money_claimable_confirmed(latest, metrics)
    reportable_count = _metric_value_or_zero(metrics, "reportable_opportunities")
    counts = _sombra_output_counts(classification, metrics)
    if confirmed_money:
        money_line = (
            "Dinero reclamable confirmado: si; requiere que Daniel revise y suba manualmente el informe al programa."
        )
    elif reportable_count:
        money_line = (
            "No hay dinero reclamable confirmado todavia: hay oportunidad reportable potencial, "
            "pendiente de evidencia y scope."
        )
    else:
        money_line = "No hay plata reclamable todavia: el ultimo evento no registra oportunidades reportables confirmadas."
    potential_line = (
        f"{reportable_count} oportunidad(es) reportable(s) para revision privada del CEO."
        if reportable_count
        else "pendiente; hay programas pagados detectados, pero falta evidencia reportable."
    )
    forja_line = (
        "Tarea tecnica necesaria: preparar diagnostico/parche defensivo interno sin tocar FORJA externa."
        if classification in {"TAREA_FORJA", "PENDIENTE_EVIDENCIA", "INFORME_BUG_BOUNTY"}
        else "Tareas tecnicas necesarias: ninguna nueva hasta tener evidencia accionable."
    )
    centinela_line = (
        "Alerta defensiva: revisar senales con CENTINELA; nivel de riesgo derivado del evento "
        f"{latest.get('severity') or 'no informado'}."
    )
    linkedin_line = (
        "Borrador publico seguro: educar sobre gestion de riesgo digital; sin empresa vulnerable, "
        "sin endpoint, sin explotacion, sin datos sensibles y sin publicacion automatica."
    )
    ready_line = (
        f"{counts['ready_reports']} informe(s) privado(s) listo(s) para revision del CEO."
        if counts["ready_reports"]
        else "0 informes listos; no se declara bounty reclamable sin evidencia suficiente."
    )
    pending_line = (
        f"{counts['pending_evidence']} informe(s) pendiente(s) por evidencia."
        if counts["pending_evidence"]
        else "0 informes pendientes por evidencia fuera de las validaciones del evento seleccionado."
    )
    audit_context = {
        "productive_classification": classification,
        "ready_reports": counts["ready_reports"],
        "pending_evidence": counts["pending_evidence"],
        "discarded": counts["discarded"],
        "money_claimable_confirmed": confirmed_money,
        "fixed_operation_instruction_active": True,
    }
    reply = (
        "DINERO:\n"
        f"- hay dinero reclamable confirmado? {'si' if confirmed_money else 'no'}.\n"
        f"- programas pagados detectados: {paid_programs_line}.\n"
        f"- programas pagados: {_metric_copy(metrics, 'paid_program_count')}.\n"
        f"- potencial economico: {potential_line}\n"
        f"- {money_line}\n\n"
        "INFORMES:\n"
        f"- clasificacion productiva: {classification}.\n"
        f"- informes listos para revision del CEO: {ready_line}\n"
        f"- informes pendientes por evidencia: {pending_line}\n"
        f"- descartados: {counts['discarded']}.\n"
        f"- evento: {latest.get('title') or 'sin titulo'}; tipo={latest.get('type')}; severidad={latest.get('severity')}; "
        f"message_id={latest.get('message_id')}; recibido={latest.get('received_at')}.\n"
        f"- programas analizados: {_metric_copy(metrics, 'programs_analyzed')}.\n"
        f"- programas detectados: {programs_line}.\n"
        f"- senales detectadas: {_metric_copy(metrics, 'local_signal_count')}.\n"
        f"- senales principales: {signals_line}.\n"
        f"- coincidencias: {_metric_copy(metrics, 'matches')}.\n"
        f"- matches cantidad: {_metric_copy(metrics, 'matches')}.\n"
        f"- matches: {matches_line}.\n"
        f"- oportunidades reportables: {_metric_copy(metrics, 'reportable_opportunities')}.\n"
        f"- items reportables: {reportables_line}.\n\n"
        "FORJA:\n"
        f"- {forja_line}\n"
        "- salida: tarea preparada por CEREBRO si falta construir herramienta, API, skill o parche defensivo.\n\n"
        "LINKEDIN:\n"
        f"- {linkedin_line}\n\n"
        "CENTINELA:\n"
        f"- {centinela_line}\n"
        "- accion recomendada: validar defensivamente y no consultar SOMBRA externo desde la UI.\n\n"
        "AUDITORIA:\n"
        "- evento registrado: si.\n"
        f"- decision tomada: {classification}.\n"
        "- evidencia disponible: payload sensible retenido en inbox interno; salida CEO sanitizada.\n\n"
        "DECISION CEO:\n"
        f"- Daniel debe revisar evidencia y decidir si sube manualmente el informe al programa correspondiente. Siguiente paso: {next_step}.\n"
        f"- Esto sale de {len(events)} evento(s) ya recibido(s); no consulte runtime externo ni expuse payload sensible."
    )
    if metrics.get("pdf_path"):
        reply += f"\n- PDF registrado: {metrics['pdf_path']}."
    return reply, audit_context


def audit_sombra_productive_decision(
    latest: dict[str, object],
    classification_context: dict[str, object],
) -> str | None:
    try:
        severity_value = str(latest.get("severity") or "info").lower()
        if severity_value not in {item.value for item in AuditSeverity}:
            severity_value = "info"
        event = create_audit_event(
            AuditEventCreate(
                category=AuditCategory.integration,
                severity=AuditSeverity(severity_value),
                source="cerebro.production_flow",
                action="sombra_inbox_decision",
                status=str(classification_context.get("productive_classification") or "DESCARTADO"),
                detail="CEREBRO classified SOMBRA inbox and produced sanitized CEO outputs.",
                metadata={
                    "message_id": latest.get("message_id"),
                    "message_type": latest.get("type"),
                    "classification": classification_context.get("productive_classification"),
                    "money_claimable_confirmed": classification_context.get("money_claimable_confirmed"),
                    "ready_reports": classification_context.get("ready_reports"),
                    "pending_evidence": classification_context.get("pending_evidence"),
                    "discarded": classification_context.get("discarded"),
                    "payload_exposed": False,
                    "external_connection_enabled": False,
                    "runtime_connected": False,
                },
            )
        )
        return event.id
    except Exception:
        return None


def build_sombra_context_reply(events: list[dict[str, object]]) -> tuple[str, dict[str, object]]:
    selected = select_sombra_context_event(events)
    context = {
        "used_sombra_context": bool(events),
        "sombra_events_used": len(events),
        "sombra_latest_event_at": selected.get("received_at") if selected else None,
        "sombra_latest_message_id": selected.get("message_id") if selected else None,
    }
    if selected is None:
        return (
            "Daniel, el inbox interno de CEREBRO esta preparado. "
            "Todavia no hay eventos reales de SOMBRA registrados en PostgreSQL para responder con contexto. "
            "No consulte el servidor externo de SOMBRA.",
            context,
        )

    latest = selected
    metrics = extract_sombra_scan_metrics(latest)
    context["sombra_latest_metrics"] = metrics
    reportable = metrics.get("reportable_opportunities")
    reportable_count = reportable if isinstance(reportable, int) else None
    money_claimable = bool(reportable_count and reportable_count > 0)
    money_line = (
        "Dinero reclamable: si, potencialmente; requiere revision manual, evidencia y scope antes de reclamar."
        if money_claimable
        else "No hay plata reclamable todavia: el ultimo evento no registra oportunidades reportables confirmadas."
    )
    if metrics:
        classification = classify_sombra_productive_event(latest, metrics)
        reply, classification_context = build_sombra_production_reply(
            latest,
            events,
            metrics,
            classification,
        )
        context.update(classification_context)
        return reply, context

    summary = latest.get("executive_summary") or latest.get("summary") or "sin resumen disponible"
    classification = classify_sombra_productive_event(latest, metrics)
    context.update(
        {
            "productive_classification": classification,
            "ready_reports": 0,
            "pending_evidence": 1 if classification == "PENDIENTE_EVIDENCIA" else 0,
            "discarded": 1 if classification == "DESCARTADO" else 0,
            "money_claimable_confirmed": False,
            "fixed_operation_instruction_active": True,
        }
    )
    return (
        "DINERO:\n"
        "- hay dinero reclamable confirmado? no.\n"
        "- programas pagados detectados: no informado.\n"
        "- potencial economico: pendiente por evidencia.\n\n"
        "INFORMES:\n"
        f"- clasificacion productiva: {classification}.\n"
        "- informes listos para revision del CEO: 0.\n"
        "- informes pendientes por evidencia: 1.\n"
        "- descartados: 0.\n"
        f"- evento: {latest.get('title') or 'sin titulo'}; message_id={latest.get('message_id')}; recibido={latest.get('received_at')}.\n"
        f"- resumen: {summary}.\n"
        "- no invento conteos ni oportunidades; se requiere que SOMBRA envie metricas explicitas.\n\n"
        "FORJA:\n"
        "- tarea tecnica necesaria: pendiente hasta tener evidencia parseable.\n\n"
        "LINKEDIN:\n"
        "- borrador publico seguro: no generar pieza especifica sin evidencia; sin empresa vulnerable, sin endpoint, sin explotacion, sin datos sensibles.\n\n"
        "CENTINELA:\n"
        "- alerta defensiva: revisar solo si la severidad o evidencia lo justifica.\n\n"
        "AUDITORIA:\n"
        "- evento registrado: si.\n"
        f"- decision tomada: {classification}.\n"
        "- evidencia disponible: insuficiente para informe productivo.\n\n"
        "DECISION CEO:\n"
        "- Daniel debe pedir a SOMBRA metricas explicitas o evidencia antes de reclamar o publicar. No consulte servidor externo de SOMBRA.",
        context,
    )


def _board_join(
    items: list[str],
    fallback: str = "sin datos suficientes todavía",
    limit: int = 3,
) -> str:
    clean: list[str] = []
    for item in items:
        value = " ".join(str(item or "").split())
        if value and value not in clean:
            clean.append(value)
        if len(clean) >= limit:
            break
    return "; ".join(clean) if clean else fallback


def _pending_evidence_count(events: list[dict[str, object]]) -> int:
    return sum(
        1
        for event in events
        if classify_sombra_productive_event(
            event,
            extract_sombra_scan_metrics(event),
        )
        == "PENDIENTE_EVIDENCIA"
    )


def _discarded_count(events: list[dict[str, object]]) -> int:
    return sum(
        1
        for event in events
        if classify_sombra_productive_event(
            event,
            extract_sombra_scan_metrics(event),
        )
        == "DESCARTADO"
    )


def _ready_report_titles(events: list[dict[str, object]]) -> list[str]:
    titles: list[str] = []
    for event in events:
        metrics = extract_sombra_scan_metrics(event)
        if classify_sombra_productive_event(event, metrics) != "INFORME_BUG_BOUNTY":
            continue
        count = _metric_value_or_zero(metrics, "reportable_opportunities")
        title = str(event.get("title") or event.get("message_id") or "informe sin título")
        titles.append(f"{title} ({count} oportunidad(es) reportable(s))")
    return titles


def _paid_programs_from_events(events: list[dict[str, object]]) -> list[str]:
    paid_programs: list[str] = []
    for event in events:
        metrics = extract_sombra_scan_metrics(event)
        value = metrics.get("paid_programs")
        if isinstance(value, list):
            paid_programs.extend(str(item) for item in value[:6])
        elif _metric_value_or_zero(metrics, "paid_program_count") > 0:
            paid_programs.append(
                f"{_metric_value_or_zero(metrics, 'paid_program_count')} "
                "programa(s) pagado(s) detectado(s)"
            )
    return paid_programs


def _money_claimable_from_events(events: list[dict[str, object]]) -> bool:
    return any(
        _money_claimable_confirmed(event, extract_sombra_scan_metrics(event))
        for event in events
    )


def _economic_potential(
    revenue_opportunities: list[CerebroRevenueOpportunity],
    events: list[dict[str, object]],
) -> str:
    expected_revenue = sum(
        float(item.economic_matrix.expected_revenue or 0)
        for item in revenue_opportunities
    )
    reportable = sum(
        _metric_value_or_zero(
            extract_sombra_scan_metrics(event),
            "reportable_opportunities",
        )
        for event in events
    )
    if expected_revenue > 0:
        return (
            f"potencial registrado en oportunidades internas: USD {expected_revenue:.0f}; "
            "sin datos suficientes todavía para reclamar dinero"
        )
    if reportable > 0:
        return (
            f"{reportable} oportunidad(es) reportable(s) potencial(es), "
            "pendiente evidencia y scope"
        )
    return "sin datos suficientes todavía"


def build_operational_board_reply() -> tuple[str, dict[str, object]]:
    revenue_opportunities = safe_call(list_revenue_opportunities, [])
    commercial_drafts = safe_call(list_commercial_drafts, [])
    tasks = safe_call(list_cerebro_tasks, [])
    decisions = safe_call(list_cerebro_decisions, [])
    approval_requests = safe_call(list_approval_requests, [])
    alerts = safe_call(lambda: list_alerts(include_low=True), [])
    sombra_events = safe_call(lambda: list_sombra_inbox_context(limit=20), [])

    try:
        from app.services.audit import list_audit_events, list_auditoria_reviews

        audit_events = safe_call(list_audit_events, [])
        auditoria_reviews = safe_call(lambda: list_auditoria_reviews(limit=100), [])
    except Exception:
        audit_events = []
        auditoria_reviews = []

    confirmed_money = _money_claimable_from_events(sombra_events)
    paid_programs = _paid_programs_from_events(sombra_events)
    ready_reports = _ready_report_titles(sombra_events)
    pending_evidence = _pending_evidence_count(sombra_events)
    discarded = _discarded_count(sombra_events)

    forja_tasks = [
        f"{task.title} ({task.state.value})"
        for task in tasks
        if normalize_destination(task.destination) == "forja"
        and not task.blocked
        and task.state not in {CerebroState.completed, CerebroState.rejected}
    ]
    linkedin_drafts = [
        f"{draft.title} ({draft.status})"
        for draft in commercial_drafts
        if "linkedin"
        in _normalized_metric_text(
            f"{draft.draft_type} {draft.title} {draft.source}"
        )
        or draft.draft_type == "linkedin_post"
    ]
    alert_lines = [
        f"{alert.title} ({alert.risk_level})"
        for alert in alerts
        if alert.interrupt_ceo
        or alert.risk_level in {"medium", "high", "critical"}
    ]
    pending_decisions = [
        f"{decision.title} ({decision.state.value})"
        for decision in decisions
        if decision.state
        in {CerebroState.draft, CerebroState.proposed, CerebroState.waiting_ceo}
        or (
            decision.requires_ceo_approval
            and decision.state
            not in {CerebroState.completed, CerebroState.rejected}
        )
    ] + [
        f"{approval.title} ({approval.status})"
        for approval in approval_requests
        if approval.status in {"pending_ceo", "waiting_ceo", "proposed"}
    ]
    risk_level = (
        "alto"
        if any(alert.risk_level in {"high", "critical"} for alert in alerts)
        else "medio"
        if alert_lines or pending_evidence or forja_tasks
        else "bajo"
    )
    centinela_action = (
        "resolver alertas de riesgo alto antes de afirmar cierre productivo."
        if risk_level == "alto"
        else "revisar evidencia interna antes de reclamar, publicar o ejecutar cambios."
    )
    linkedin_status = (
        "pendiente CEO"
        if linkedin_drafts
        else "pendiente CEO - sin datos suficientes todavía"
    )

    context = {
        "operational_board": True,
        "money_claimable_confirmed": confirmed_money,
        "paid_programs_detected": len(paid_programs),
        "reports_ready": len(ready_reports),
        "reports_pending_evidence": pending_evidence,
        "reports_discarded": discarded,
        "forja_tasks": len(forja_tasks),
        "linkedin_drafts": len(linkedin_drafts),
        "centinela_alerts": len(alert_lines),
        "audit_events": len(audit_events),
        "auditoria_reviews": len(auditoria_reviews),
        "external_connection_enabled": False,
        "runtime_connected": False,
    }

    reply = (
        "DINERO:\n"
        f"- dinero reclamable confirmado: {'sí' if confirmed_money else 'no'}\n"
        f"- potencial económico: {_economic_potential(revenue_opportunities, sombra_events)}\n"
        f"- programas pagados detectados: {_board_join(paid_programs)}\n\n"
        "INFORMES:\n"
        f"- informes listos para revisión CEO: {_board_join(ready_reports)}\n"
        "- informes pendientes por evidencia: "
        f"{pending_evidence if sombra_events else 'sin datos suficientes todavía'}\n"
        f"- descartados: {discarded if sombra_events else 'sin datos suficientes todavía'}\n\n"
        "FORJA:\n"
        f"- tareas técnicas necesarias: {_board_join(forja_tasks, 'sin tarea técnica inmediata')}\n\n"
        "LINKEDIN:\n"
        f"- borradores disponibles: {_board_join(linkedin_drafts)}\n"
        f"- estado: {linkedin_status}\n\n"
        "CENTINELA:\n"
        f"- alertas defensivas: {_board_join(alert_lines)}\n"
        f"- nivel de riesgo: {risk_level}\n"
        f"- acción recomendada: {centinela_action}\n\n"
        "AUDITORÍA:\n"
        f"- eventos registrados: {len(audit_events)} evento(s) centrales; "
        f"{len(auditoria_reviews)} revisión(es) de AUDITORÍA\n"
        f"- decisiones pendientes: {_board_join(pending_decisions)}\n"
        "- evidencia disponible: "
        f"SOMBRA inbox={len(sombra_events)}; borradores={len(commercial_drafts)}; "
        f"tareas={len(tasks)}; oportunidades={len(revenue_opportunities)}\n\n"
        "DECISIÓN CEO:\n"
        "- qué debe aprobar, subir o decidir Daniel ahora: aprobar o rechazar "
        "decisiones pendientes; subir evidencia solo si existe informe listo; "
        "mantener LinkedIn en revisión CEO hasta confirmar datos; no reclamar "
        "dinero sin evidencia suficiente."
    )
    return reply, context


def cerebro_conversation_owner_id(actor: AuthenticatedUser) -> str:
    return str(actor.id or actor.email or actor.name or "unknown")


def _message_count_for_conversation(connection, conversation_id: str) -> int:
    placeholder = sql_placeholder()
    row = connection.execute(
        f"SELECT COUNT(*) AS message_count FROM {CEREBRO_MESSAGES_TABLE} WHERE conversation_id = {placeholder}",
        (conversation_id,),
    ).fetchone()
    return int(get_row_value(row, "message_count", index=0, default=0) or 0)


def _latest_message_for_conversation(connection, conversation_id: str) -> str | None:
    placeholder = sql_placeholder()
    row = connection.execute(
        f"""
        SELECT content
        FROM {CEREBRO_MESSAGES_TABLE}
        WHERE conversation_id = {placeholder}
        ORDER BY created_at DESC
        LIMIT 1
        """,
        (conversation_id,),
    ).fetchone()
    content = get_row_value(row, "content", default=None)
    return str(content) if content else None


def _row_to_conversation_summary(row: object, connection=None) -> CerebroConversationSummary:
    metadata = _json_load(get_row_value(row, "metadata_json", default="{}"), {})
    conversation_id = str(get_row_value(row, "id"))
    message_count = int(get_row_value(row, "message_count", default=-1) or -1)
    latest_message = get_row_value(row, "latest_message", default=None)
    if connection is not None:
        if message_count < 0:
            message_count = _message_count_for_conversation(connection, conversation_id)
        if latest_message is None:
            latest_message = _latest_message_for_conversation(connection, conversation_id)
    if message_count < 0:
        message_count = 0
    return CerebroConversationSummary(
        id=conversation_id,
        owner=str(get_row_value(row, "owner")),
        title=str(get_row_value(row, "title")),
        context=str(get_row_value(row, "context")),
        message_count=message_count,
        latest_message=str(latest_message) if latest_message else None,
        created_at=str(get_row_value(row, "created_at")),
        updated_at=str(get_row_value(row, "updated_at")),
        metadata=metadata if isinstance(metadata, dict) else {},
    )


def _row_to_conversation_message(row: object) -> CerebroConversationMessage:
    metadata = _json_load(get_row_value(row, "metadata_json", default="{}"), {})
    return CerebroConversationMessage(
        id=str(get_row_value(row, "id")),
        conversation_id=str(get_row_value(row, "conversation_id")),
        role=get_row_value(row, "role"),
        content=str(get_row_value(row, "content")),
        source=str(get_row_value(row, "source")),
        metadata=metadata if isinstance(metadata, dict) else {},
        created_at=str(get_row_value(row, "created_at")),
    )


def ensure_cerebro_conversation(
    request: CerebroChatRequest,
    actor: AuthenticatedUser,
    message: str,
) -> CerebroConversationSummary:
    ensure_cerebro_schema()
    placeholder = sql_placeholder()
    owner_id = cerebro_conversation_owner_id(actor)
    with connect() as connection:
        if request.conversation_id:
            row = connection.execute(
                f"SELECT * FROM {CEREBRO_CONVERSATIONS_TABLE} WHERE id = {placeholder}",
                (request.conversation_id,),
            ).fetchone()
            if row is None or get_row_value(row, "owner_id") != owner_id:
                raise CerebroError(
                    status_code=404,
                    detail={"error": "cerebro_conversation_not_found", "conversation_id": request.conversation_id},
                )
            return _row_to_conversation_summary(row, connection)

        now = utc_now()
        conversation_id = f"cerebro-conv-{uuid4()}"
        metadata = sanitize_metadata(
            {
                "created_from": "cerebro_chat",
                "office": request.office,
                "priority": request.priority,
                "app_context": request.app_context,
                "external_connection_enabled": False,
                "runtime_connected": False,
            }
        )
        connection.execute(
            f"""
            INSERT INTO {CEREBRO_CONVERSATIONS_TABLE} (
                id, owner_id, owner, title, context, metadata_json, created_at, updated_at
            )
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                conversation_id,
                owner_id,
                actor_name(actor),
                cerebro_chat_title(message, "Conversacion con CEREBRO"),
                request.context,
                _json_dump(metadata),
                now,
                now,
            ),
        )
        connection.commit()
        row = connection.execute(
            f"SELECT * FROM {CEREBRO_CONVERSATIONS_TABLE} WHERE id = {placeholder}",
            (conversation_id,),
        ).fetchone()
    return _row_to_conversation_summary(row)


def store_cerebro_message(
    conversation_id: str,
    role: str,
    content: str,
    *,
    source: str = "cerebro_chat",
    metadata: dict[str, object] | None = None,
) -> CerebroConversationMessage:
    ensure_cerebro_schema()
    placeholder = sql_placeholder()
    now = utc_now()
    message_id = f"cerebro-msg-{uuid4()}"
    safe_metadata = sanitize_metadata(metadata or {})
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {CEREBRO_MESSAGES_TABLE} (
                id, conversation_id, role, content, source, metadata_json, created_at
            )
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """,
            (
                message_id,
                conversation_id,
                role,
                content,
                source,
                _json_dump(safe_metadata),
                now,
            ),
        )
        connection.execute(
            f"""
            UPDATE {CEREBRO_CONVERSATIONS_TABLE}
            SET updated_at = {placeholder}
            WHERE id = {placeholder}
            """,
            (now, conversation_id),
        )
        connection.commit()
        row = connection.execute(
            f"SELECT * FROM {CEREBRO_MESSAGES_TABLE} WHERE id = {placeholder}",
            (message_id,),
        ).fetchone()
    return _row_to_conversation_message(row)


def list_cerebro_conversations(
    actor: AuthenticatedUser,
    *,
    limit: int = 20,
) -> list[CerebroConversationSummary]:
    ensure_cerebro_schema()
    safe_limit = max(1, min(int(limit or 20), 100))
    placeholder = sql_placeholder()
    owner_id = cerebro_conversation_owner_id(actor)
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT *
            FROM {CEREBRO_CONVERSATIONS_TABLE}
            WHERE owner_id = {placeholder}
            ORDER BY updated_at DESC
            LIMIT {safe_limit}
            """,
            (owner_id,),
        ).fetchall()
        return [_row_to_conversation_summary(row, connection) for row in rows]


def get_cerebro_conversation(
    conversation_id: str,
    actor: AuthenticatedUser,
) -> CerebroConversationDetail:
    ensure_cerebro_schema()
    placeholder = sql_placeholder()
    owner_id = cerebro_conversation_owner_id(actor)
    with connect() as connection:
        row = connection.execute(
            f"SELECT * FROM {CEREBRO_CONVERSATIONS_TABLE} WHERE id = {placeholder}",
            (conversation_id,),
        ).fetchone()
        if row is None or get_row_value(row, "owner_id") != owner_id:
            raise CerebroError(
                status_code=404,
                detail={"error": "cerebro_conversation_not_found", "conversation_id": conversation_id},
            )
        messages = connection.execute(
            f"""
            SELECT *
            FROM {CEREBRO_MESSAGES_TABLE}
            WHERE conversation_id = {placeholder}
            ORDER BY created_at ASC
            """,
            (conversation_id,),
        ).fetchall()
        summary = _row_to_conversation_summary(row, connection)
    return CerebroConversationDetail(
        **summary.model_dump(),
        messages=[_row_to_conversation_message(message) for message in messages],
    )


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


def notify_centinela(message: SombraInboxMessageCreate) -> dict[str, str]:
    analysis = analyze_operational_report(message)
    return {
        "type": "centinela_analysis_created",
        "id": analysis.id,
        "target": "centinela",
        "impact": analysis.impact,
        "affects_ecosystem": str(analysis.affects_ecosystem).lower(),
        "may_affect_clients": str(analysis.may_affect_clients).lower(),
        "requires_update": str(analysis.requires_update).lower(),
        "requires_defensive_rule": str(analysis.requires_defensive_rule).lower(),
        "requires_api": str(analysis.requires_api).lower(),
        "requires_skill": str(analysis.requires_skill).lower(),
        "requires_tool": str(analysis.requires_tool).lower(),
        "requires_forja_task": str(analysis.requires_forja_task).lower(),
        "recommendation": analysis.recommendation,
    }


def create_forja_task(
    message: SombraInboxMessageCreate,
    centinela_action: dict[str, str],
    protocol: dict[str, object],
    actor: AuthenticatedUser,
) -> dict[str, str] | None:
    if centinela_action.get("requires_forja_task") != "true":
        return None
    task = create_cerebro_task(
        CerebroTaskCreate(
            title="FORJA: construir defensa solicitada por CENTINELA",
            description=(
                str(protocol.get("forja_signal") or build_forja_signal(message))
                + " CENTINELA pidio construccion tecnica desde canal operativo."
            ),
            destination="FORJA",
            priority="p0" if message.severity.value == "critical" else "p1",
            reason="Canal OPERATIVO_DEFENSIVO SOMBRA -> CEREBRO -> CENTINELA -> FORJA.",
            requires_ceo_approval=False,
        ),
        actor,
    )
    return {"type": "forja_task_created", "id": task.id, "target": "forja"}


def register_arsenal_artifact(
    message: SombraInboxMessageCreate,
    centinela_action: dict[str, str],
    forja_action: dict[str, str] | None,
    actor: AuthenticatedUser,
) -> dict[str, str] | None:
    reusable = any(
        centinela_action.get(key) == "true"
        for key in ("requires_api", "requires_skill", "requires_tool", "requires_defensive_rule")
    )
    if not reusable:
        return None
    try:
        from app.schemas.arsenal import ArsenalCatalogItemCreate
        from app.services.arsenal import create_catalog_item

        item_type = "regla_reutilizable"
        if centinela_action.get("requires_api") == "true":
            item_type = "api"
        elif centinela_action.get("requires_skill") == "true":
            item_type = "skill"
        elif centinela_action.get("requires_tool") == "true":
            item_type = "herramienta"

        item = create_catalog_item(
            ArsenalCatalogItemCreate(
                name=f"Capacidad defensiva SOMBRA {message.message_id[:32]}",
                item_type=item_type,
                category="herramientas_ciberseguridad",
                internal_use=(
                    "Artefacto preparado desde reporte operativo SOMBRA analizado por CENTINELA. "
                    "Sin secretos, sin payload sensible y sin ejecucion externa."
                ),
                sellable_use="Pendiente de auditoria y aprobacion CEO antes de uso comercial.",
                is_sellable=False,
                requires_secret=False,
                requires_external_api=False,
                risk=message.severity.value,
                monetization="not_estimated",
                owner="CEREBRO/CENTINELA/FORJA",
                metadata={
                    "source": "sombra_operativo_defensivo",
                    "message_id": message.message_id,
                    "forja_task_created": bool(forja_action),
                    "centinela_analysis_id": centinela_action.get("id"),
                    "content_included": False,
                },
            ),
            actor,
        )
        return {"type": "arsenal_artifact_registered", "id": item.id, "target": "arsenal", "item_type": item.item_type}
    except Exception as exc:
        return {"type": "arsenal_artifact_failed", "id": "unavailable", "target": str(exc)[:120]}


def create_editorial_draft(
    message: SombraInboxMessageCreate,
    protocol: dict[str, object],
    actor: AuthenticatedUser,
) -> dict[str, str] | None:
    if not protocol.get("commercial_draft_ready"):
        return None
    draft = create_cerebro_commercial_draft(
        CerebroCommercialDraftCreate(
            source="sombra_operativo_defensivo",
            source_message_id=message.message_id,
            title=message.title,
            summary=str(protocol.get("commercial_summary") or message.summary),
            client_context=message.client_context,
            safe_for_commercial_use=True,
        ),
        actor,
    )
    return {"type": "commercial_draft_created", "id": draft.id, "target": "pluma_marca_personal"}


def audit_report_flow(
    message: SombraInboxMessageCreate,
    actions: list[dict[str, str]],
    actor: AuthenticatedUser,
) -> dict[str, str]:
    action_map = {action.get("type", ""): action.get("id", "") for action in actions}
    event_id = audit_cerebro_action(
        action="sombra_operational_report_flow",
        actor=actor,
        status="routed",
        detail=(
            "CEREBRO routed an OPERATIVO_DEFENSIVO SOMBRA report through CENTINELA, "
            "FORJA/ARSENAL/PLUMA when required, and AUDITORIA metadata."
        ),
        state=CerebroState.delegated,
        destination="centinela_forja_arsenal_pluma_auditoria",
        reason=f"message_id={message.message_id}",
        requires_ceo_approval=False,
        blocked=False,
    )
    return {
        "type": "auditoria_flow_registered",
        "id": event_id,
        "target": "auditoria",
        "reported": "received,cerebro_decision,centinela_analysis,forja_task,arsenal_artifact,pluma_draft,final_state",
        "forja_task_id": action_map.get("forja_task_created", ""),
        "arsenal_artifact_id": action_map.get("arsenal_artifact_registered", ""),
        "draft_id": action_map.get("commercial_draft_created", ""),
    }


def route_operational_report(
    message: SombraInboxMessageCreate,
    routed_to: list[str],
    protocol: dict[str, object] | None = None,
) -> list[dict[str, str]]:
    protocol = protocol or apply_cyber_intelligence_protocol(message)
    actor = service_actor()
    actions: list[dict[str, str]] = []
    centinela_action = notify_centinela(message)
    actions.append(centinela_action)

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

    try:
        forja_action = create_forja_task(message, centinela_action, protocol, actor)
        if forja_action:
            actions.append(forja_action)
    except Exception as exc:
        actions.append({"type": "forja_task_failed", "id": "unavailable", "target": str(exc)[:120]})
        forja_action = None

    arsenal_action = register_arsenal_artifact(message, centinela_action, forja_action, actor)
    if arsenal_action:
        actions.append(arsenal_action)

    if message.type.value == "lead_signal":
        try:
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
        except Exception as exc:
            actions.append({"type": "lead_signal_route_failed", "id": "unavailable", "target": str(exc)[:120]})

    try:
        draft_action = create_editorial_draft(message, protocol, actor)
        if draft_action:
            actions.append(draft_action)
    except Exception as exc:
        actions.append({"type": "commercial_draft_failed", "id": "unavailable", "target": str(exc)[:120]})

    actions.append(audit_report_flow(message, actions, actor))
    return actions


def route_sombra_message(
    message: SombraInboxMessageCreate,
    routed_to: list[str],
    protocol: dict[str, object] | None = None,
) -> list[dict[str, str]]:
    return route_operational_report(message, routed_to, protocol)


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


SOMBRA_CHAT_STRONG_TRIGGERS = (
    "revisa inteligencia",
    "revisa inteligencia externa",
    "alertas externas",
    "alertas de sombra",
    "mensajes de sombra",
    "inteligencia entrante",
    "inteligencia externa",
    "resume briefing",
    "briefing",
    "ultimo reporte",
    "ultimo escaneo",
    "reporte",
    "reportes",
    "bug bounty",
    "recompensa",
    "oportunidades",
    "plata",
    "reclamar",
    "que encontro",
    "reporte de sombra",
    "hay plata",
    "oportunidad reportable",
    "sistema discreto",
)

SOMBRA_CHAT_NAME_ONLY_OPTOUTS = (
    "sin tocar sombra",
    "no tocar sombra",
    "no consulte sombra",
    "no consultar sombra",
)

ARSENAL_CHAT_TRIGGERS = (
    "recursos sombra",
    "herramientas sombra",
    "lista herramientas sombra",
    "recursos centinela",
    "herramientas centinela",
    "apis disponibles",
    "skills disponibles",
)

OPERATIONAL_BOARD_SECTIONS = (
    "dinero",
    "informes",
    "forja",
    "linkedin",
    "centinela",
    "auditoria",
    "decision ceo",
)

EVENT_OFFICE_DECISION_TRIGGERS = (
    "decision ejecutiva por oficina",
    "que aplica por oficina",
    "aplica arsenal",
    "aplica centinela",
    "aplica sentinela",
    "aplica forja",
    "aplica pluma",
)


def message_requests_sombra_inbox(message: str) -> bool:
    if any(token in message for token in SOMBRA_CHAT_STRONG_TRIGGERS):
        return True
    return "sombra" in message and not any(
        token in message for token in SOMBRA_CHAT_NAME_ONLY_OPTOUTS
    )


def message_requests_arsenal_resources(message: str) -> bool:
    normalized = _normalized_metric_text(message)
    return "arsenal" in normalized or any(
        token in normalized for token in ARSENAL_CHAT_TRIGGERS
    )


def arsenal_office_from_message(message: str) -> str:
    normalized = _normalized_metric_text(message)
    office_aliases = (
        ("sombra", "SOMBRA"),
        ("centinela", "CENTINELA"),
        ("sentinela", "CENTINELA"),
        ("forja", "FORJA"),
        ("pluma", "PLUMA"),
        ("marca personal", "MARCA_PERSONAL"),
        ("auditoria", "AUDITORIA"),
        ("nube", "NUBE"),
        ("ceo", "CEO"),
    )
    for token, office in office_aliases:
        if token in normalized:
            return office
    return "CEREBRO"


def arsenal_resources_for_chat(
    office: str,
    actor: AuthenticatedUser,
) -> list[object]:
    # Deferred import is intentional. app.services.arsenal imports task helpers
    # from this module, so importing it at module load time would be circular.
    from app.services.arsenal import list_resources_for_office

    return list(list_resources_for_office(office, actor=actor))


def arsenal_resources_reply(
    office: str,
    resources: list[object],
) -> str:
    def resource_value(resource: object, key: str, default: object = None) -> object:
        if isinstance(resource, dict):
            return resource.get(key, default)
        return getattr(resource, key, default)

    lines = [
        "ARSENAL: PASS",
        f"oficina consultada: {office}",
        f"recursos visibles: {len(resources)}",
    ]
    for resource in resources:
        name = resource_value(resource, "name", "sin nombre")
        resource_type = resource_value(resource, "type", "sin tipo")
        status = resource_value(resource, "status", "sin estado")
        readiness = resource_value(resource, "readiness", "sin readiness")
        type_value = getattr(resource_type, "value", resource_type)
        status_value = getattr(status, "value", status)
        lines.append(
            f"- {name} | type={type_value} | status={status_value} | "
            f"readiness={readiness} | secrets_stored=false"
        )
    lines.extend(
        [
            "secrets_stored=false",
            "sin acciones externas",
            "sin crear tareas",
            "sin crear borradores",
        ]
    )
    return "\n".join(lines)


def message_requests_operational_board(message: str) -> bool:
    section_matches = sum(
        1 for section in OPERATIONAL_BOARD_SECTIONS if section in message
    )
    asks_for_state = any(
        token in message
        for token in (
            "estado",
            "estatus",
            "tablero",
            "diagnostico",
            "situacion",
            "dame",
            "muestra",
            "resume",
            "resumen",
            "como estamos",
        )
    )
    asks_for_productive_state = any(
        token in message
        for token in (
            "estado productivo",
            "estado operativo",
            "estado real",
            "tablero operativo",
            "flujo operativo",
            "productivo real",
        )
    )
    board_topics = (
        "inteligencia externa",
        "bug bounty",
        "reportes",
        "informes",
        "dinero",
        "sombra",
        "ecosistema",
        "flujo operativo",
    )
    creates_content = any(
        token in message
        for token in (
            "genera post",
            "generar post",
            "redacta",
            "escribe",
            "publica",
            "programa",
            "borrador linkedin",
        )
    )
    if creates_content and not asks_for_state and section_matches < 2:
        return False
    return (
        asks_for_productive_state
        or section_matches >= 3
        or (asks_for_state and any(topic in message for topic in board_topics))
    )


def extract_trace_event_message_id(message: str) -> str | None:
    text = " ".join(str(message or "").strip().split())
    if not text:
        return None
    patterns = (
        r"(?:trace event|trace_event|estado del evento|estatus del evento|con el evento|evento|message_id|mensaje)\s*[:=#-]?\s*([A-Za-z0-9][A-Za-z0-9_.:-]{8,180})",
        r"\b([A-Za-z0-9][A-Za-z0-9_.:-]*20[0-9]{6}T[0-9]{6}Z[A-Za-z0-9_.:-]*)\b",
    )
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" \t\r\n,;.()[]{}<>\"'")
            if len(candidate) >= 8 and candidate.lower() not in {"trazabilidad", "responde"}:
                return candidate
    normalized = _normalized_metric_text(text)
    if not any(token in normalized for token in ("trazabilidad", "trace event", "estado del evento")):
        return None
    for token in re.findall(r"[A-Za-z0-9][A-Za-z0-9_.:-]{8,180}", text):
        candidate = token.strip(" \t\r\n,;.()[]{}<>\"'")
        if any(character.isdigit() for character in candidate) and any(
            separator in candidate for separator in ("-", "_", ":")
        ):
            return candidate
    return None


def message_requests_event_trace(message: str) -> bool:
    normalized = _normalized_metric_text(message)
    asks_for_trace = any(
        token in normalized
        for token in (
            "trazabilidad",
            "trace event",
            "estado del evento",
            "estatus del evento",
            "responde solo trazabilidad",
        )
    )
    return asks_for_trace and extract_trace_event_message_id(message) is not None


def message_id_is_bug_bounty_event(message_id: str | None) -> bool:
    return str(message_id or "").lower().startswith("bug-bounty-hunter-")


def message_requests_event_office_decision(message: str) -> bool:
    normalized = _normalized_metric_text(message)
    message_id = extract_trace_event_message_id(message)
    if not message_id_is_bug_bounty_event(message_id):
        return False
    return any(token in normalized for token in EVENT_OFFICE_DECISION_TRIGGERS)


def cerebro_chat_intent(request: CerebroChatRequest) -> str:
    message = _normalized_metric_text(request.message)
    if message_requests_event_trace(request.message):
        return "event_trace"
    if message_requests_event_office_decision(request.message):
        return "event_office_decision"
    if message_requests_arsenal_resources(message):
        return "arsenal_resources"
    if request.action == "operational_board":
        return "operational_board"
    if request.action != "auto":
        if request.action == "event_trace":
            return "event_trace"
        if request.action == "event_office_decision":
            return "event_office_decision"
        if message_requests_sombra_inbox(message):
            return "sombra_inbox"
        return request.action
    if message_requests_operational_board(message):
        return "operational_board"
    if message_requests_sombra_inbox(message):
        return "sombra_inbox"
    office = normalize_destination(request.office)
    if office == "centinela":
        return "centinela"
    if office == "forja":
        return "forja"
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
    conversation = ensure_cerebro_conversation(request, actor, message)
    user_message = store_cerebro_message(
        conversation.id,
        "user",
        message,
        metadata={
            "intent_detected": intent,
            "request_context": request.context,
            "office": request.office,
            "priority": request.priority,
            "app_context": request.app_context,
            "external_connection_enabled": False,
            "runtime_connected": False,
        },
    )
    actions: list[CerebroChatAction] = []
    used_context: dict[str, object] = {
        "intent_detected": intent,
        "used_sombra_context": False,
        "sombra_events_used": 0,
        "external_connection_enabled": False,
        "runtime_connected": False,
    }

    if intent == "event_trace":
        traced_message_id = extract_trace_event_message_id(message) or ""
        trace = trace_event(traced_message_id)
        reply = event_trace_reply(trace)
        used_context.update(
            {
                "event_trace_message_id": traced_message_id,
                "event_trace": trace,
                "used_sombra_context": bool(trace.get("source")),
            }
        )
        actions.append(
            CerebroChatAction(
                type="event_trace",
                status="prepared",
                id=traced_message_id or str(trace.get("message_id") or "event-trace"),
                label="Trazabilidad exacta de evento",
                detail="CEREBRO devolvio solo trazabilidad por message_id; no creo borrador ni tarea desde el prompt CEO.",
            )
        )
    elif intent == "event_office_decision":
        traced_message_id = extract_trace_event_message_id(message) or ""
        trace = inspect_event_trace(traced_message_id)
        sombra_resources = arsenal_resources_for_chat("SOMBRA", actor)
        reply = event_office_decision_reply(trace, sombra_resources)
        used_context.update(
            {
                "event_trace_message_id": traced_message_id,
                "event_trace": trace,
                "used_sombra_context": bool(trace.get("source")),
                "arsenal_office": "SOMBRA",
                "arsenal_resource_count": len(sombra_resources),
                "forja_tasks_created": 0,
                "linkedin_drafts_created": 0,
                "arsenal_resources_created": 0,
                "sombra_runtime_touched": False,
            }
        )
        actions.append(
            CerebroChatAction(
                type="event_office_decision",
                status="prepared",
                id=traced_message_id or str(trace.get("message_id") or "event-office-decision"),
                label="Decision ejecutiva por oficina",
                detail=(
                    "CEREBRO devolvio aplicacion por ARSENAL/CENTINELA/FORJA/PLUMA/"
                    "BUNKER/AUDITORIA usando IDs existentes; sin tarea, borrador, recurso nuevo "
                    "ni runtime SOMBRA."
                ),
            )
        )
    elif intent == "arsenal_resources":
        office = arsenal_office_from_message(message)
        resources = arsenal_resources_for_chat(office, actor)
        reply = arsenal_resources_reply(office, resources)
        used_context.update(
            {
                "arsenal_office": office,
                "arsenal_resource_count": len(resources),
                "arsenal_secrets_stored": False,
                "arsenal_external_actions": False,
                "arsenal_tasks_created": 0,
                "arsenal_drafts_created": 0,
            }
        )
        actions.append(
            CerebroChatAction(
                type="arsenal_resources",
                status="prepared",
                id=f"arsenal-resources-{office.lower()}",
                label=f"Recursos ARSENAL para {office}",
                detail=(
                    "Consulta interna de inventario autorizado; sin acciones externas, "
                    "sin tareas FORJA y sin borradores LinkedIn."
                ),
            )
        )
    elif intent == "operational_board":
        reply, board_context = build_operational_board_reply()
        used_context.update(board_context)
        actions.append(
            CerebroChatAction(
                type="operational_board",
                status="prepared",
                id="cerebro-operational-board",
                label="Tablero operativo CEREBRO",
                detail=(
                    "CEREBRO devolvió DINERO / INFORMES / FORJA / LINKEDIN / "
                    "CENTINELA / AUDITORÍA / DECISIÓN CEO desde datos internos."
                ),
            )
        )
    elif intent == "mission":
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
        sombra_events = list_sombra_inbox_context(limit=5)
        reply, sombra_context = build_sombra_context_reply(sombra_events)
        used_context.update(sombra_context)
        if sombra_events:
            selected_message_id = str(sombra_context.get("sombra_latest_message_id") or "")
            latest = next(
                (
                    event
                    for event in sombra_events
                    if str(event.get("message_id") or "") == selected_message_id
                ),
                sombra_events[0],
            )
            audit_event_id = audit_sombra_productive_decision(latest, sombra_context)
            if audit_event_id:
                used_context["audit_event_id"] = audit_event_id
            metrics = extract_sombra_scan_metrics(latest)
            metrics_detail = (
                "programas={programs} senales={signals} coincidencias={matches} reportables={reportable}".format(
                    programs=metrics.get("programs_analyzed", "no informado"),
                    signals=metrics.get("local_signal_count", "no informado"),
                    matches=metrics.get("matches", "no informado"),
                    reportable=metrics.get("reportable_opportunities", "no informado"),
                )
                if metrics
                else "Evento real recibido, sin metricas parseables."
            )
            actions.append(
                CerebroChatAction(
                    type="sombra_inbox_reviewed",
                    status="prepared",
                    id=str(latest.get("message_id") or "sombra-inbox-event"),
                    label=str(latest.get("title") or "Inbox SOMBRA de CEREBRO"),
                    detail=f"{len(sombra_events)} eventos reales revisados; {metrics_detail} Payload sensible no expuesto.",
                )
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

    state = cerebro_chat_state()
    provider = "internal"
    if intent not in {
        "sombra_inbox",
        "arsenal_resources",
        "operational_board",
        "event_trace",
        "event_office_decision",
    }:
        llm_reply = generate_cerebro_reply(
            message=message,
            intent=intent,
            actions=[action.model_dump() for action in actions],
            state=state.model_dump(),
        )
        if llm_reply:
            reply = llm_reply
            provider = "anthropic"

    assistant_message = store_cerebro_message(
        conversation.id,
        "assistant",
        reply,
        metadata={
            **used_context,
            "provider": provider,
            "actions": [action.model_dump() for action in actions],
            "state": state.model_dump(),
        },
    )

    return CerebroChatResponse(
        ok=True,
        conversation_id=conversation.id,
        message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        reply=reply,
        response=reply,
        actions=actions,
        state=state,
        provider=provider,
        used_context=used_context,
        created_at=assistant_message.created_at,
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
