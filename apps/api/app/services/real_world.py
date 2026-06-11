from datetime import UTC, datetime
import json
import re

from app.core.database import connect, get_row_value, initialize_database, sql_placeholder
from app.core.safe_data import safe_payload_json
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.real_world import (
    RealWorldActionRequest,
    RealWorldConnection,
    RealWorldConnectionState,
    RealWorldConnectionType,
    RealWorldRiskLevel,
    RealWorldStatus,
)
from app.services.audit import create_audit_event

REAL_WORLD_CONNECTIONS_TABLE = "real_world_connections"
REAL_WORLD_EVENTS_TABLE = "real_world_events"

REAL_WORLD_TABLES = {
    REAL_WORLD_CONNECTIONS_TABLE,
    REAL_WORLD_EVENTS_TABLE,
}

SECRET_VALUE_PATTERN = re.compile(
    r"(password|token|api[_-]?key|client[_-]?secret|secret|clave[_-]?sol|contrase(?:n|ñ)a)\s*[:=]\s*\S+|"
    r"(sk_live_|sk_test_|xoxb-|ghp_[A-Za-z0-9])",
    re.IGNORECASE,
)


class RealWorldError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def actor_name(user: AuthenticatedUser | None) -> str:
    if user is None:
        return "system"
    return user.email or user.name or user.id


def ensure_real_world_schema() -> None:
    initialize_database()
    with connect() as connection:
        for table_name in REAL_WORLD_TABLES:
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


def ensure_table(table_name: str) -> None:
    if table_name not in REAL_WORLD_TABLES:
        raise RealWorldError(500, {"error": "invalid_real_world_table", "table": table_name})


def upsert_payload(table_name: str, item_id: str, payload: dict) -> None:
    ensure_table(table_name)
    ensure_real_world_schema()
    now = utc_now()
    placeholder = sql_placeholder()
    with connect() as connection:
        connection.execute(
            f"""
            INSERT INTO {table_name} (id, payload_json, created_at, updated_at)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            ON CONFLICT(id) DO UPDATE SET
                payload_json = excluded.payload_json,
                updated_at = excluded.updated_at
            """,
            (item_id, json.dumps(payload, ensure_ascii=True), now, now),
        )
        connection.commit()


def fetch_payload(table_name: str, item_id: str) -> dict | None:
    ensure_table(table_name)
    ensure_real_world_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    if row is None:
        return None
    return parse_payload_json(get_row_value(row, "payload_json"))


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_table(table_name)
    ensure_real_world_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            ORDER BY created_at ASC
            """
        ).fetchall()
    payloads: list[dict] = []
    for row in rows:
        payload = parse_payload_json(get_row_value(row, "payload_json"))
        if payload is not None:
            payloads.append(payload)
    return payloads


def parse_payload_json(raw_payload: object) -> dict | None:
    return safe_payload_json(raw_payload)


def reject_secret_like_payload(request: RealWorldActionRequest | None) -> None:
    if request is None:
        return
    for field_name in ("note", "evidence", "reason"):
        value = getattr(request, field_name, None)
        if value and SECRET_VALUE_PATTERN.search(value):
            raise RealWorldError(
                400,
                {
                    "error": "real_world_secret_like_value_rejected",
                    "field": field_name,
                    "reason": "secrets_must_not_be_saved_or_printed",
                },
            )


def audit_real_world_action(
    *,
    actor: AuthenticatedUser | None,
    action: str,
    status: str,
    detail: str,
    metadata: dict[str, object] | None = None,
) -> None:
    create_audit_event(
        AuditEventCreate(
            category=AuditCategory.event,
            severity=AuditSeverity.info,
            source="real_world.connection_readiness",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "actor": actor_name(actor),
                "external_connection_enabled": False,
                "runtime_connected": False,
                "real_publication_enabled": False,
                "paid_campaign_launched": False,
                "payment_connected": False,
                "sunat_enabled": False,
                "secrets_stored": False,
                **(metadata or {}),
            },
        )
    )


def build_connection(
    item_id: str,
    area: str,
    connection: str,
    connection_type: RealWorldConnectionType,
    state: RealWorldConnectionState,
    owner_internal: str,
    recommended_action: str,
    *,
    evidence: str = "missing",
    requires_ceo: bool = False,
    requires_credentials: bool = False,
    requires_money: bool = False,
    risk: RealWorldRiskLevel = RealWorldRiskLevel.medium,
    related_block: str = "S.1",
    can_continue_prepared: bool = True,
    notes: str = "",
) -> RealWorldConnection:
    now = utc_now()
    return RealWorldConnection(
        id=item_id,
        area=area,
        connection=connection,
        connection_type=connection_type,
        state=state,
        evidence=evidence,
        requires_ceo=requires_ceo,
        requires_credentials=requires_credentials,
        requires_money=requires_money,
        risk=risk,
        recommended_action=recommended_action,
        related_block=related_block,
        owner_internal=owner_internal,
        can_continue_prepared=can_continue_prepared,
        notes=notes,
        created_at=now,
        updated_at=now,
    )


def initial_connections() -> list[RealWorldConnection]:
    c = build_connection
    return [
        c("marca_personal_tiktok", "Marca Personal", "TikTok", RealWorldConnectionType.social_account, RealWorldConnectionState.unknown, "MARCA PERSONAL", "Confirmar si existe cuenta oficial antes de publicar.", requires_ceo=True),
        c("marca_personal_instagram", "Marca Personal", "Instagram", RealWorldConnectionType.social_account, RealWorldConnectionState.unknown, "MARCA PERSONAL", "Confirmar cuenta oficial o dejar prepared.", requires_ceo=True),
        c("marca_personal_linkedin", "Marca Personal", "LinkedIn", RealWorldConnectionType.social_account, RealWorldConnectionState.unknown, "MARCA PERSONAL", "Definir cuenta actual o nueva.", requires_ceo=True),
        c("marca_personal_x", "Marca Personal", "X", RealWorldConnectionType.social_account, RealWorldConnectionState.unknown, "MARCA PERSONAL", "Confirmar handle oficial.", requires_ceo=True),
        c("marca_personal_youtube", "Marca Personal", "YouTube", RealWorldConnectionType.social_account, RealWorldConnectionState.unknown, "MARCA PERSONAL", "Confirmar canal oficial o preparar uno nuevo.", requires_ceo=True),
        c("lente_youtube_channels", "LENTE", "YouTube canales", RealWorldConnectionType.publishing_account, RealWorldConnectionState.needs_ceo_definition, "LENTE", "Definir canales y nichos antes de publicacion real.", requires_ceo=True),
        c("lente_tiktok_channels", "LENTE", "TikTok canales", RealWorldConnectionType.publishing_account, RealWorldConnectionState.needs_ceo_definition, "LENTE", "Definir canales oficiales por nicho.", requires_ceo=True),
        c("lente_reels_shorts", "LENTE", "Reels/Shorts", RealWorldConnectionType.content_tool, RealWorldConnectionState.prepared, "LENTE", "Preparar piezas sin publicar real.", risk=RealWorldRiskLevel.low),
        c("lente_podcast_avatar", "LENTE", "podcast/avatar", RealWorldConnectionType.content_tool, RealWorldConnectionState.needs_ceo_definition, "LENTE", "Definir identidad visual y canal.", requires_ceo=True),
        c("lente_animation", "LENTE", "animacion", RealWorldConnectionType.content_tool, RealWorldConnectionState.prepared, "LENTE", "Preparar assets sin cuenta externa.", risk=RealWorldRiskLevel.low),
        c("lente_childrens_channels", "LENTE", "canales infantiles", RealWorldConnectionType.publishing_account, RealWorldConnectionState.needs_ceo_definition, "LENTE", "Requiere definicion y revision de riesgo de contenido infantil.", requires_ceo=True, risk=RealWorldRiskLevel.high),
        c("lente_christian_channels", "LENTE", "canales cristianos", RealWorldConnectionType.publishing_account, RealWorldConnectionState.needs_ceo_definition, "LENTE", "Definir si el nicho aplica antes de crear identidad publica.", requires_ceo=True),
        c("lente_ai_trends_channels", "LENTE", "canales IA/tendencias", RealWorldConnectionType.publishing_account, RealWorldConnectionState.needs_ceo_definition, "LENTE", "Definir lista final de canales.", requires_ceo=True),
        c("publishing_facebook", "Publishing & Growth", "Facebook", RealWorldConnectionType.publishing_account, RealWorldConnectionState.unknown, "MARKETING", "Confirmar cuenta oficial; sin publicacion real por ahora.", requires_ceo=True),
        c("publishing_instagram", "Publishing & Growth", "Instagram", RealWorldConnectionType.publishing_account, RealWorldConnectionState.unknown, "MARKETING", "Mantener publication_status prepared hasta evidencia.", requires_ceo=True),
        c("publishing_tiktok", "Publishing & Growth", "TikTok", RealWorldConnectionType.publishing_account, RealWorldConnectionState.unknown, "MARKETING", "Confirmar cuenta antes de publicar.", requires_ceo=True),
        c("publishing_youtube", "Publishing & Growth", "YouTube", RealWorldConnectionType.publishing_account, RealWorldConnectionState.unknown, "MARKETING", "Confirmar canal o preparar borradores.", requires_ceo=True),
        c("publishing_linkedin", "Publishing & Growth", "LinkedIn", RealWorldConnectionType.publishing_account, RealWorldConnectionState.unknown, "MARKETING", "Confirmar cuenta oficial.", requires_ceo=True),
        c("publishing_x", "Publishing & Growth", "X", RealWorldConnectionType.publishing_account, RealWorldConnectionState.unknown, "MARKETING", "Confirmar cuenta oficial.", requires_ceo=True),
        c("publishing_blog_web", "Publishing & Growth", "Blog/Web", RealWorldConnectionType.publishing_account, RealWorldConnectionState.prepared, "WEB FACTORY", "Preparar contenido y landing sin publicar si dominio no esta confirmado.", risk=RealWorldRiskLevel.low),
        c("publishing_newsletter", "Publishing & Growth", "Newsletter", RealWorldConnectionType.email_tool, RealWorldConnectionState.needs_credentials, "MARKETING", "Definir herramienta y credenciales por canal seguro.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.sensitive),
        c("marketing_meta_ads", "Marketing", "Meta Ads", RealWorldConnectionType.marketing_platform, RealWorldConnectionState.needs_paid_approval, "MARKETING", "Preparar ROI; no lanzar campana pagada sin CEO.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("marketing_google_ads", "Marketing", "Google Ads", RealWorldConnectionType.marketing_platform, RealWorldConnectionState.needs_paid_approval, "MARKETING", "Preparar ROI y presupuesto; no activar.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("marketing_tiktok_ads", "Marketing", "TikTok Ads", RealWorldConnectionType.marketing_platform, RealWorldConnectionState.needs_paid_approval, "MARKETING", "Preparar propuesta pagada con ROI.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("marketing_linkedin_ads", "Marketing", "LinkedIn Ads", RealWorldConnectionType.marketing_platform, RealWorldConnectionState.needs_paid_approval, "MARKETING", "Preparar solo si ROI justifica.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("marketing_email", "Marketing", "email marketing", RealWorldConnectionType.email_tool, RealWorldConnectionState.needs_credentials, "MARKETING", "Elegir herramienta y vault antes de conectar.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.sensitive),
        c("marketing_crm", "Marketing", "CRM", RealWorldConnectionType.crm_tool, RealWorldConnectionState.needs_ceo_definition, "MARKETING", "Definir CRM sin crear cuenta externa todavia.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.high),
        c("revenue_payment_gateway", "Revenue OS", "pasarela de pago", RealWorldConnectionType.payment_provider, RealWorldConnectionState.needs_paid_approval, "REVENUE OS", "Definir proveedor, credenciales y aprobacion antes de cobrar.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("revenue_invoicing", "Revenue OS", "facturacion", RealWorldConnectionType.tax_regulatory_source, RealWorldConnectionState.needs_legal_review, "DCFT", "Revisar legal/tributario antes de automatizar.", requires_ceo=True, risk=RealWorldRiskLevel.sensitive),
        c("revenue_tracking", "Revenue OS", "tracking de ingresos", RealWorldConnectionType.analytics_account, RealWorldConnectionState.prepared, "REVENUE OS", "Preparar tablero sin inventar ventas.", risk=RealWorldRiskLevel.low),
        c("revenue_roi", "Revenue OS", "ROI", RealWorldConnectionType.analytics_account, RealWorldConnectionState.prepared, "REVENUE OS", "Calcular hipotesis con evidencia faltante marcada.", risk=RealWorldRiskLevel.low),
        c("revenue_conversion_metrics", "Revenue OS", "metricas de conversion", RealWorldConnectionType.analytics_account, RealWorldConnectionState.unknown, "MARKETING", "No inventar conversion; esperar herramienta o evidencia.", risk=RealWorldRiskLevel.medium),
        c("ecommerce_store", "E-commerce", "tienda propia", RealWorldConnectionType.ecommerce_platform, RealWorldConnectionState.needs_ceo_definition, "E-COMMERCE", "Definir plataforma/nombre antes de crear tienda.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.high),
        c("ecommerce_marketplace", "E-commerce", "marketplace", RealWorldConnectionType.marketplace, RealWorldConnectionState.needs_account_creation, "E-COMMERCE", "Crear cuenta externa requiere CEO.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.sensitive),
        c("ecommerce_payments", "E-commerce", "pagos", RealWorldConnectionType.payment_provider, RealWorldConnectionState.needs_paid_approval, "E-COMMERCE", "No conectar pagos ni cobrar sin aprobacion.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("ecommerce_inventory", "E-commerce", "inventario", RealWorldConnectionType.ecommerce_platform, RealWorldConnectionState.unknown, "E-COMMERCE", "No comprar inventario; documentar fuentes.", requires_money=True, risk=RealWorldRiskLevel.high),
        c("ecommerce_logistics", "E-commerce", "logistica", RealWorldConnectionType.ecommerce_platform, RealWorldConnectionState.unknown, "E-COMMERCE", "Preparar mapa logistico sin contratar.", requires_money=True, risk=RealWorldRiskLevel.high),
        c("ecommerce_analytics", "E-commerce", "analitica", RealWorldConnectionType.analytics_account, RealWorldConnectionState.prepared, "E-COMMERCE", "Preparar metricas sin inventar datos.", risk=RealWorldRiskLevel.low),
        c("amazon_seller", "SNIFF AMAZON / CHIEF AMAZON", "Amazon Seller", RealWorldConnectionType.marketplace, RealWorldConnectionState.needs_account_creation, "SNIFF AMAZON", "Cuenta Amazon requiere CEO y credenciales.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.sensitive),
        c("amazon_product_research", "SNIFF AMAZON / CHIEF AMAZON", "Amazon Product Research", RealWorldConnectionType.external_api, RealWorldConnectionState.prepared, "SNIFF AMAZON", "Preparar criterios; no pagar herramienta externa.", risk=RealWorldRiskLevel.medium),
        c("amazon_buy_box_tracking", "SNIFF AMAZON / CHIEF AMAZON", "Buy Box tracking", RealWorldConnectionType.external_api, RealWorldConnectionState.unknown, "SNIFF AMAZON", "Confirmar herramienta y costos antes de conectar.", requires_ceo=True, requires_money=True, risk=RealWorldRiskLevel.high),
        c("amazon_scraping_monitoring", "SNIFF AMAZON / CHIEF AMAZON", "scraping/monitoring permitido", RealWorldConnectionType.external_api, RealWorldConnectionState.needs_legal_review, "SNIFF AMAZON", "Revisar terminos antes de automatizar.", requires_ceo=True, risk=RealWorldRiskLevel.high),
        c("amazon_external_tools", "SNIFF AMAZON / CHIEF AMAZON", "herramientas externas", RealWorldConnectionType.external_api, RealWorldConnectionState.needs_paid_approval, "SNIFF AMAZON", "No activar herramientas con costo sin CEO.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("dcft_tax_sources", "DCFT", "fuentes tributarias", RealWorldConnectionType.tax_regulatory_source, RealWorldConnectionState.needs_legal_review, "DCFT", "Validar fuente oficial sin SUNAT real desde ecosystem.", requires_ceo=True, risk=RealWorldRiskLevel.sensitive),
        c("dcft_accounting_sources", "DCFT", "fuentes contables", RealWorldConnectionType.tax_regulatory_source, RealWorldConnectionState.needs_legal_review, "DCFT", "Revisar fuentes antes de claims.", requires_ceo=True, risk=RealWorldRiskLevel.high),
        c("dcft_normative_updates", "DCFT", "actualizacion normativa", RealWorldConnectionType.tax_regulatory_source, RealWorldConnectionState.needs_legal_review, "DCFT", "No afirmar actualizacion legal sin fuente.", requires_ceo=True, risk=RealWorldRiskLevel.sensitive),
        c("dcft_landing", "DCFT", "landing", RealWorldConnectionType.publishing_account, RealWorldConnectionState.prepared, "WEB FACTORY", "Preparar landing sin publicar ni vender.", risk=RealWorldRiskLevel.low),
        c("dcft_pricing", "DCFT", "pricing", RealWorldConnectionType.analytics_account, RealWorldConnectionState.needs_ceo_definition, "MARKETING", "CEO/Marketing deben confirmar precio antes de vender.", requires_ceo=True),
        c("dcft_support", "DCFT", "soporte", RealWorldConnectionType.crm_tool, RealWorldConnectionState.needs_ceo_definition, "DCFT", "Definir soporte y canales sin credenciales.", requires_ceo=True),
        c("dcft_distribution", "DCFT", "distribucion", RealWorldConnectionType.marketplace, RealWorldConnectionState.needs_ceo_definition, "MARKETING", "Definir canal comercial sin publicar real.", requires_ceo=True),
        c("sentinela_security_sources", "SENTINELA", "fuentes de ciberseguridad", RealWorldConnectionType.security_feed, RealWorldConnectionState.needs_legal_review, "SENTINELA", "Validar fuentes y permisos antes de conectar.", requires_ceo=True, risk=RealWorldRiskLevel.sensitive),
        c("sentinela_threat_feeds", "SENTINELA", "threat feeds", RealWorldConnectionType.security_feed, RealWorldConnectionState.needs_credentials, "SENTINELA", "No conectar feed real ni guardar credenciales.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.sensitive),
        c("sentinela_landing", "SENTINELA", "landing", RealWorldConnectionType.publishing_account, RealWorldConnectionState.prepared, "WEB FACTORY", "Preparar landing sin claims de seguridad no validados.", risk=RealWorldRiskLevel.low),
        c("sentinela_pricing", "SENTINELA", "pricing", RealWorldConnectionType.analytics_account, RealWorldConnectionState.needs_ceo_definition, "MARKETING", "Definir precio con Marketing; no meta propia.", requires_ceo=True),
        c("sentinela_support", "SENTINELA", "soporte", RealWorldConnectionType.crm_tool, RealWorldConnectionState.needs_ceo_definition, "SENTINELA", "Definir soporte sin abrir cuentas externas.", requires_ceo=True),
        c("sentinela_distribution", "SENTINELA", "distribucion", RealWorldConnectionType.marketplace, RealWorldConnectionState.needs_ceo_definition, "MARKETING", "Definir canal comercial sin publicacion real.", requires_ceo=True),
        c("web_factory_domains", "Web Factory", "dominios", RealWorldConnectionType.cloud_provider, RealWorldConnectionState.needs_paid_approval, "WEB FACTORY", "Compra de dominio requiere CEO.", requires_ceo=True, requires_money=True, risk=RealWorldRiskLevel.high),
        c("web_factory_hosting", "Web Factory", "hosting", RealWorldConnectionType.cloud_provider, RealWorldConnectionState.needs_paid_approval, "WEB FACTORY", "Hosting con costo requiere aprobacion.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("web_factory_landing_pages", "Web Factory", "landing pages", RealWorldConnectionType.publishing_account, RealWorldConnectionState.prepared, "WEB FACTORY", "Preparar landing local sin publicar.", risk=RealWorldRiskLevel.low),
        c("web_factory_forms", "Web Factory", "formularios", RealWorldConnectionType.crm_tool, RealWorldConnectionState.needs_credentials, "WEB FACTORY", "Definir destino de datos y credenciales.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.sensitive),
        c("web_factory_analytics", "Web Factory", "analytics", RealWorldConnectionType.analytics_account, RealWorldConnectionState.needs_credentials, "WEB FACTORY", "Preparar medicion sin conectar cuenta real.", requires_ceo=True, requires_credentials=True, risk=RealWorldRiskLevel.high),
        c("apis_internal", "APIs/Skills", "APIs internas", RealWorldConnectionType.external_api, RealWorldConnectionState.prepared, "CREADOR APIs/SKILLS", "Mantener internas sin costo ni secretos.", risk=RealWorldRiskLevel.low),
        c("apis_sellable", "APIs/Skills", "APIs vendibles", RealWorldConnectionType.external_api, RealWorldConnectionState.prepared, "CREADOR APIs/SKILLS", "Preparar documentacion y pricing sin vender real.", risk=RealWorldRiskLevel.medium),
        c("apis_external_tools", "APIs/Skills", "herramientas externas", RealWorldConnectionType.external_api, RealWorldConnectionState.needs_paid_approval, "CREADOR APIs/SKILLS", "API con costo requiere CEO y vault.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("apis_documentation", "APIs/Skills", "documentacion", RealWorldConnectionType.content_tool, RealWorldConnectionState.prepared, "CREADOR APIs/SKILLS", "Documentar sin secretos.", risk=RealWorldRiskLevel.low),
        c("apis_pricing", "APIs/Skills", "pricing", RealWorldConnectionType.analytics_account, RealWorldConnectionState.needs_ceo_definition, "MARKETING", "Definir precios antes de venta.", requires_ceo=True),
        c("app_store_google_play", "App Stores", "Google Play", RealWorldConnectionType.app_store, RealWorldConnectionState.needs_account_creation, "NUBE", "Crear cuenta o publicar app requiere CEO.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
        c("app_store_apple", "App Stores", "Apple App Store", RealWorldConnectionType.app_store, RealWorldConnectionState.needs_account_creation, "NUBE", "Cuenta Apple y publicacion requieren CEO.", requires_ceo=True, requires_credentials=True, requires_money=True, risk=RealWorldRiskLevel.sensitive),
    ]


def seed_real_world_defaults() -> None:
    ensure_real_world_schema()
    if fetch_payloads(REAL_WORLD_CONNECTIONS_TABLE):
        return
    for connection in initial_connections():
        upsert_payload(
            REAL_WORLD_CONNECTIONS_TABLE,
            connection.id,
            connection.model_dump(mode="json"),
        )


def parse_connection(payload: dict) -> RealWorldConnection | None:
    try:
        return RealWorldConnection(**payload)
    except Exception:
        return None


def list_connections() -> list[RealWorldConnection]:
    seed_real_world_defaults()
    connections: list[RealWorldConnection] = []
    for payload in fetch_payloads(REAL_WORLD_CONNECTIONS_TABLE):
        connection = parse_connection(payload)
        if connection is not None:
            connections.append(connection)
    return sorted(connections, key=lambda item: (item.area, item.connection))


def get_connection(connection_id: str) -> RealWorldConnection:
    seed_real_world_defaults()
    payload = fetch_payload(REAL_WORLD_CONNECTIONS_TABLE, connection_id)
    if payload is None:
        raise RealWorldError(404, {"error": "real_world_connection_not_found", "connection_id": connection_id})
    connection = parse_connection(payload)
    if connection is None:
        raise RealWorldError(404, {"error": "real_world_connection_payload_invalid", "connection_id": connection_id})
    return connection


def save_connection(connection: RealWorldConnection) -> RealWorldConnection:
    connection.updated_at = utc_now()
    connection.external_connection_enabled = False
    connection.runtime_connected = False
    connection.real_publication_enabled = False
    connection.paid_campaign_launched = False
    connection.payment_connected = False
    connection.sunat_enabled = False
    connection.secrets_stored = False
    upsert_payload(REAL_WORLD_CONNECTIONS_TABLE, connection.id, connection.model_dump(mode="json"))
    return connection


def connection_needs_approval(connection: RealWorldConnection) -> bool:
    return (
        connection.requires_ceo
        or connection.requires_money
        or connection.requires_credentials
        or connection.state
        in {
            RealWorldConnectionState.needs_ceo_definition,
            RealWorldConnectionState.needs_paid_approval,
            RealWorldConnectionState.needs_account_creation,
            RealWorldConnectionState.needs_legal_review,
            RealWorldConnectionState.needs_credentials,
        }
    )


def mark_connection_prepared(
    connection_id: str,
    request: RealWorldActionRequest,
    actor: AuthenticatedUser,
) -> RealWorldConnection:
    reject_secret_like_payload(request)
    connection = get_connection(connection_id)
    connection.state = RealWorldConnectionState.prepared
    connection.evidence = request.evidence or connection.evidence
    connection.notes = request.note or connection.notes
    connection.can_continue_prepared = True
    connection.requires_ceo = False
    connection.recommended_action = "Continuar en modo prepared; no ejecutar conexion real sin nueva aprobacion."
    connection = save_connection(connection)
    audit_real_world_action(
        actor=actor,
        action="mark_connection_prepared",
        status=connection.state.value,
        detail="Real world connection marked prepared without external execution.",
        metadata={"connection_id": connection.id},
    )
    return connection


def request_ceo_definition(
    connection_id: str,
    request: RealWorldActionRequest,
    actor: AuthenticatedUser,
) -> RealWorldConnection:
    reject_secret_like_payload(request)
    connection = get_connection(connection_id)
    connection.state = RealWorldConnectionState.needs_ceo_definition
    connection.requires_ceo = True
    connection.notes = request.reason or request.note or connection.notes
    connection.recommended_action = "CEO debe definir la cuenta, canal, proveedor o criterio antes de ejecutar."
    connection = save_connection(connection)
    audit_real_world_action(
        actor=actor,
        action="request_ceo_definition",
        status=connection.state.value,
        detail="Real world connection escalated for CEO definition.",
        metadata={"connection_id": connection.id},
    )
    return connection


def request_approval(
    connection_id: str,
    request: RealWorldActionRequest,
    actor: AuthenticatedUser,
) -> RealWorldConnection:
    reject_secret_like_payload(request)
    connection = get_connection(connection_id)
    connection.requires_ceo = True
    connection.state = (
        RealWorldConnectionState.needs_paid_approval
        if connection.requires_money
        else RealWorldConnectionState.needs_ceo_definition
    )
    connection.notes = request.reason or request.note or connection.notes
    connection.recommended_action = "Esperar aprobacion CEO antes de usar dinero, credenciales o accion externa."
    connection = save_connection(connection)
    audit_real_world_action(
        actor=actor,
        action="request_real_world_approval",
        status=connection.state.value,
        detail="Real world connection approval requested without executing external action.",
        metadata={"connection_id": connection.id, "requires_money": connection.requires_money},
    )
    return connection


def list_approval_needed() -> list[RealWorldConnection]:
    return [
        connection
        for connection in list_connections()
        if connection_needs_approval(connection)
    ]


def list_risks() -> list[RealWorldConnection]:
    return [
        connection
        for connection in list_connections()
        if connection.risk in {RealWorldRiskLevel.high, RealWorldRiskLevel.sensitive}
    ]


def get_real_world_status() -> RealWorldStatus:
    connections = list_connections()
    connected = [
        connection
        for connection in connections
        if connection.state in {RealWorldConnectionState.connected_manual, RealWorldConnectionState.connected_api}
    ]
    approval_needed = list_approval_needed()
    risks = list_risks()
    return RealWorldStatus(
        total_connections=len(connections),
        connected=len(connected),
        prepared=len([connection for connection in connections if connection.state == RealWorldConnectionState.prepared]),
        unknown=len([connection for connection in connections if connection.state == RealWorldConnectionState.unknown]),
        needs_ceo=len([connection for connection in connections if connection.requires_ceo]),
        needs_credentials=len([connection for connection in connections if connection.requires_credentials]),
        needs_paid_approval=len(
            [
                connection
                for connection in connections
                if connection.requires_money or connection.state == RealWorldConnectionState.needs_paid_approval
            ]
        ),
        high_risk=len([connection for connection in risks if connection.risk == RealWorldRiskLevel.high]),
        sensitive=len([connection for connection in risks if connection.risk == RealWorldRiskLevel.sensitive]),
        can_continue_prepared=len([connection for connection in connections if connection.can_continue_prepared]),
        approval_needed_count=len(approval_needed),
        next_steps=[
            "Confirmar cuentas oficiales existentes.",
            "Definir cuentas externas nuevas antes de crearlas.",
            "Guardar credenciales solo por canal seguro aprobado.",
            "Preparar ROI antes de cualquier campana pagada.",
            "Mantener conexiones como prepared/unknown si falta evidencia.",
        ],
        connections_snapshot=connections[:12],
        generated_at=utc_now(),
    )
