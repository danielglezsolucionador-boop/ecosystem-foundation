from datetime import UTC, datetime
import json
import re
from uuid import uuid4

from app.core.database import connect, get_row_value, initialize_database, sql_placeholder
from app.core.safe_data import safe_payload_json
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.real_world_execution import (
    RealWorldExecutionActionRequest,
    RealWorldExecutionPriority,
    RealWorldExecutionQueueCreate,
    RealWorldExecutionQueueItem,
    RealWorldExecutionRisk,
    RealWorldExecutionState,
    RealWorldExecutionStatus,
)
from app.services.audit import create_audit_event

REAL_WORLD_EXECUTION_QUEUE_TABLE = "real_world_execution_queue"
REAL_WORLD_EXECUTION_EVENTS_TABLE = "real_world_execution_events"
REAL_WORLD_EXECUTION_TABLES = {
    REAL_WORLD_EXECUTION_QUEUE_TABLE,
    REAL_WORLD_EXECUTION_EVENTS_TABLE,
}

SECRET_VALUE_PATTERN = re.compile(
    r"(password|token|api[_-]?key|client[_-]?secret|secret|clave[_-]?sol|contrase(?:n|a))\s*[:=]\s*\S+|"
    r"(sk_live_|sk_test_|xoxb-|ghp_[A-Za-z0-9])",
    re.IGNORECASE,
)


class RealWorldExecutionError(Exception):
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


def ensure_execution_schema() -> None:
    initialize_database()
    with connect() as connection:
        for table_name in REAL_WORLD_EXECUTION_TABLES:
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
    if table_name not in REAL_WORLD_EXECUTION_TABLES:
        raise RealWorldExecutionError(500, {"error": "invalid_real_world_execution_table", "table": table_name})


def upsert_payload(table_name: str, item_id: str, payload: dict) -> None:
    ensure_table(table_name)
    ensure_execution_schema()
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
    ensure_execution_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    if row is None:
        return None
    return safe_payload_json(get_row_value(row, "payload_json"))


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_table(table_name)
    ensure_execution_schema()
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
        payload = safe_payload_json(get_row_value(row, "payload_json"))
        if payload is not None:
            payloads.append(payload)
    return payloads


def reject_secret_like_payload(values: dict[str, object] | RealWorldExecutionActionRequest | None) -> None:
    if values is None:
        return
    payload = values.model_dump() if hasattr(values, "model_dump") else values
    for field_name, value in payload.items():
        if value and SECRET_VALUE_PATTERN.search(str(value)):
            raise RealWorldExecutionError(
                400,
                {
                    "error": "real_world_execution_secret_like_value_rejected",
                    "field": field_name,
                    "reason": "secrets_must_not_be_saved_or_printed",
                },
            )


def audit_execution_action(
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
            source="real_world.execution_queue",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "actor": actor_name(actor),
                "external_execution_enabled": False,
                "payment_executed": False,
                "publication_executed": False,
                "account_created": False,
                "credentials_stored": False,
                **(metadata or {}),
            },
        )
    )


def normalize_state_for_safety(create: RealWorldExecutionQueueCreate) -> RealWorldExecutionState:
    if create.state in {
        RealWorldExecutionState.executed_manual_confirmed,
        RealWorldExecutionState.executed_api_confirmed,
    }:
        return RealWorldExecutionState.blocked
    if create.state == RealWorldExecutionState.blocked:
        return RealWorldExecutionState.blocked
    if create.requires_money:
        return RealWorldExecutionState.waiting_paid_approval
    if create.requires_credentials:
        return RealWorldExecutionState.waiting_credentials
    if create.requires_external_account:
        return RealWorldExecutionState.waiting_account_creation
    if create.requires_legal_review:
        return RealWorldExecutionState.waiting_legal_review
    if create.requires_ceo:
        return RealWorldExecutionState.waiting_ceo
    return create.state


def state_needs_ceo(state: RealWorldExecutionState) -> bool:
    return state in {
        RealWorldExecutionState.waiting_ceo,
        RealWorldExecutionState.waiting_credentials,
        RealWorldExecutionState.waiting_paid_approval,
        RealWorldExecutionState.waiting_account_creation,
        RealWorldExecutionState.waiting_legal_review,
        RealWorldExecutionState.blocked,
    }


def build_item(
    item_id: str,
    action: str,
    area: str,
    owner: str,
    priority: RealWorldExecutionPriority,
    state: RealWorldExecutionState,
    *,
    requires_ceo: bool = False,
    requires_money: bool = False,
    requires_credentials: bool = False,
    requires_external_account: bool = False,
    requires_legal_review: bool = False,
    risk: RealWorldExecutionRisk = RealWorldExecutionRisk.medium,
    economic_impact: str = "unknown",
    dependency: str = "none",
    evidence: str = "missing",
    next_action: str = "Preparar internamente; no ejecutar accion real.",
    target_date: str = "TBD",
    related_mission_id: str | None = None,
    revenue_link: str | None = None,
    workday_link: str | None = None,
) -> RealWorldExecutionQueueItem:
    now = utc_now()
    create = RealWorldExecutionQueueCreate(
        action=action,
        area=area,
        owner=owner,
        priority=priority,
        state=state,
        requires_ceo=requires_ceo,
        requires_money=requires_money,
        requires_credentials=requires_credentials,
        requires_external_account=requires_external_account,
        requires_legal_review=requires_legal_review,
        risk=risk,
        economic_impact=economic_impact,
        dependency=dependency,
        evidence=evidence,
        next_action=next_action,
        target_date=target_date,
        related_mission_id=related_mission_id,
        revenue_link=revenue_link,
        workday_link=workday_link,
    )
    safe_state = normalize_state_for_safety(create)
    ceo_required = requires_ceo or requires_money or requires_credentials or requires_external_account or requires_legal_review or state_needs_ceo(safe_state)
    payload = create.model_dump(mode="json")
    payload["state"] = safe_state
    payload["requires_ceo"] = ceo_required
    return RealWorldExecutionQueueItem(
        **payload,
        id=item_id,
        can_execute_internally=safe_state == RealWorldExecutionState.ready_internal and not ceo_required,
        ready_for_manual_execution=safe_state == RealWorldExecutionState.ready_internal and not ceo_required,
        created_at=now,
        updated_at=now,
    )


def initial_queue_items() -> list[RealWorldExecutionQueueItem]:
    p = RealWorldExecutionPriority
    r = RealWorldExecutionRisk
    s = RealWorldExecutionState
    return [
        build_item(
            "s8_marketing_prepare_dcft_landing",
            "Preparar landing comercial DCFT sin publicar",
            "DCFT / Marketing",
            "WEB FACTORY",
            p.high,
            s.ready_internal,
            risk=r.medium,
            economic_impact="apoya Revenue Sprint USD 6,000 sin venta real",
            dependency="Product Readiness DCFT/SENTINELA",
            evidence="internal_docs",
            next_action="WEB FACTORY prepara borrador local; MARKETING revisa propuesta.",
            target_date="S+7",
            revenue_link="global_6000_usd",
            workday_link="content_preparation",
        ),
        build_item(
            "s8_amazon_seller_account_decision",
            "Definir si se creara cuenta Amazon Seller",
            "SNIFF AMAZON / CHIEF AMAZON",
            "CEREBRO",
            p.high,
            s.waiting_account_creation,
            requires_external_account=True,
            requires_credentials=True,
            risk=r.sensitive,
            economic_impact="relacionado con meta E-COMMERCE USD 10,000",
            dependency="CEO decision",
            evidence="missing",
            next_action="CEO define cuenta; no crear ni conectar Amazon Seller desde el sistema.",
            target_date="CEO",
            revenue_link="ecommerce_10000_usd",
        ),
        build_item(
            "s8_ecommerce_payment_provider_decision",
            "Definir pasarela de pago e-commerce",
            "E-Commerce",
            "REVENUE OS",
            p.high,
            s.waiting_paid_approval,
            requires_money=True,
            requires_credentials=True,
            risk=r.sensitive,
            economic_impact="habilitador futuro de USD 10,000 e-commerce",
            dependency="proveedor y ROI aprobados",
            evidence="missing",
            next_action="Preparar comparativo; no conectar pasarela ni cobrar.",
            target_date="CEO",
            revenue_link="ecommerce_10000_usd",
        ),
        build_item(
            "s8_marketing_paid_campaign_roi",
            "Preparar solicitud de campana pagada con ROI",
            "MARKETING",
            "MARKETING",
            p.medium,
            s.waiting_paid_approval,
            requires_money=True,
            requires_credentials=True,
            risk=r.sensitive,
            economic_impact="posible acelerador de demanda si ROI es positivo",
            dependency="Revenue Sprint 30 dias",
            evidence="missing",
            next_action="Crear ROI y presupuesto; campana pagada queda bloqueada hasta CEO.",
            target_date="S+14",
            revenue_link="global_6000_usd",
            workday_link="revenue_sprint",
        ),
        build_item(
            "s8_social_accounts_confirmation",
            "Confirmar cuentas oficiales de Marca Personal",
            "Social Identity Map",
            "MARCA PERSONAL",
            p.medium,
            s.waiting_ceo,
            requires_ceo=True,
            risk=r.high,
            economic_impact="protege identidad publica antes de publicar",
            dependency="Social Identity Map",
            evidence="missing",
            next_action="CEO confirma cuentas existentes o define cuentas nuevas.",
            target_date="CEO",
        ),
        build_item(
            "s8_pluma_content_batch",
            "Preparar lote de contenido organico para DCFT/SENTINELA",
            "PLUMA / Publishing",
            "PLUMA",
            p.medium,
            s.ready_internal,
            risk=r.low,
            economic_impact="apoya demanda organica sin publicar real",
            dependency="Publishing & Growth Engine",
            evidence="internal_docs",
            next_action="PLUMA redacta borradores; publicacion real queda fuera de S.8.",
            target_date="S+5",
            workday_link="content_preparation",
        ),
        build_item(
            "s8_analytics_manual_dashboard",
            "Preparar tablero manual de metricas sin inventar datos",
            "Analytics",
            "AUDITORIA",
            p.medium,
            s.prepared,
            risk=r.low,
            economic_impact="mejora decision sin conectar analytics real",
            dependency="Analytics Readiness",
            evidence="missing",
            next_action="Definir columnas y evidencia requerida; no conectar API externa.",
            target_date="S+10",
        ),
        build_item(
            "s8_sunat_policy_review",
            "Revisar politica antes de cualquier fuente SUNAT desde ecosistema",
            "DCFT / Legal",
            "AUDITORIA",
            p.high,
            s.waiting_legal_review,
            requires_ceo=True,
            requires_legal_review=True,
            risk=r.sensitive,
            economic_impact="protege DCFT y evita SUNAT real no autorizado",
            dependency="CEO / legal review",
            evidence="missing",
            next_action="Mantener SUNAT real apagado; revisar solo documentacion autorizada.",
            target_date="CEO",
        ),
        build_item(
            "s8_web_factory_domain_purchase",
            "Evaluar compra de dominio para landing comercial",
            "WEB FACTORY",
            "WEB FACTORY",
            p.low,
            s.waiting_paid_approval,
            requires_money=True,
            requires_external_account=True,
            risk=r.high,
            economic_impact="posible activo comercial si CEO aprueba costo",
            dependency="nombre comercial definido",
            evidence="missing",
            next_action="Preparar opciones; no comprar dominio.",
            target_date="CEO",
        ),
        build_item(
            "s8_block_external_api_without_vault",
            "Bloquear API externa sin vault y aprobacion",
            "APIs/Skills",
            "CEREBRO",
            p.critical,
            s.blocked,
            requires_ceo=True,
            requires_credentials=True,
            risk=r.sensitive,
            economic_impact="evita costo, secreto o runtime no autorizado",
            dependency="vault y aprobacion CEO",
            evidence="policy",
            next_action="Mantener bloqueada hasta tener aprobacion, vault y alcance.",
            target_date="blocked",
        ),
    ]


def seed_execution_defaults() -> None:
    ensure_execution_schema()
    if fetch_payloads(REAL_WORLD_EXECUTION_QUEUE_TABLE):
        return
    for item in initial_queue_items():
        upsert_payload(REAL_WORLD_EXECUTION_QUEUE_TABLE, item.id, item.model_dump(mode="json"))


def parse_item(payload: dict) -> RealWorldExecutionQueueItem | None:
    try:
        return RealWorldExecutionQueueItem(**payload)
    except Exception:
        return None


def list_execution_queue() -> list[RealWorldExecutionQueueItem]:
    seed_execution_defaults()
    items: list[RealWorldExecutionQueueItem] = []
    for payload in fetch_payloads(REAL_WORLD_EXECUTION_QUEUE_TABLE):
        item = parse_item(payload)
        if item is not None:
            items.append(force_safe_flags(item))
    priority_rank = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    return sorted(items, key=lambda item: (priority_rank.get(item.priority.value, 9), item.area, item.action))


def get_queue_item(item_id: str) -> RealWorldExecutionQueueItem:
    seed_execution_defaults()
    payload = fetch_payload(REAL_WORLD_EXECUTION_QUEUE_TABLE, item_id)
    if payload is None:
        raise RealWorldExecutionError(404, {"error": "real_world_execution_item_not_found", "item_id": item_id})
    item = parse_item(payload)
    if item is None:
        raise RealWorldExecutionError(404, {"error": "real_world_execution_item_payload_invalid", "item_id": item_id})
    return force_safe_flags(item)


def force_safe_flags(item: RealWorldExecutionQueueItem) -> RealWorldExecutionQueueItem:
    item.external_execution_enabled = False
    item.payment_executed = False
    item.publication_executed = False
    item.account_created = False
    item.credentials_stored = False
    item.api_execution_confirmed = False
    item.manual_execution_confirmed = False
    item.can_execute_internally = item.state == RealWorldExecutionState.ready_internal and not item.requires_ceo
    item.ready_for_manual_execution = item.can_execute_internally
    if item.requires_money or item.requires_credentials or item.requires_external_account or item.requires_legal_review:
        item.requires_ceo = True
    return item


def save_item(item: RealWorldExecutionQueueItem) -> RealWorldExecutionQueueItem:
    item.updated_at = utc_now()
    item = force_safe_flags(item)
    upsert_payload(REAL_WORLD_EXECUTION_QUEUE_TABLE, item.id, item.model_dump(mode="json"))
    return item


def create_queue_item(
    request: RealWorldExecutionQueueCreate,
    actor: AuthenticatedUser,
) -> RealWorldExecutionQueueItem:
    reject_secret_like_payload(request.model_dump(mode="json"))
    item_id = f"s8_{uuid4().hex[:12]}"
    item = build_item(
        item_id,
        request.action,
        request.area,
        request.owner,
        request.priority,
        request.state,
        requires_ceo=request.requires_ceo,
        requires_money=request.requires_money,
        requires_credentials=request.requires_credentials,
        requires_external_account=request.requires_external_account,
        requires_legal_review=request.requires_legal_review,
        risk=request.risk,
        economic_impact=request.economic_impact,
        dependency=request.dependency,
        evidence=request.evidence,
        next_action=request.next_action,
        target_date=request.target_date,
        related_mission_id=request.related_mission_id,
        revenue_link=request.revenue_link,
        workday_link=request.workday_link,
    )
    item = save_item(item)
    audit_execution_action(
        actor=actor,
        action="create_real_world_execution_item",
        status=item.state.value,
        detail="Real world execution queue item created without external execution.",
        metadata={"item_id": item.id, "requires_ceo": item.requires_ceo},
    )
    return item


def mark_prepared(
    item_id: str,
    request: RealWorldExecutionActionRequest,
    actor: AuthenticatedUser,
) -> RealWorldExecutionQueueItem:
    reject_secret_like_payload(request)
    item = get_queue_item(item_id)
    if item.requires_money or item.requires_credentials or item.requires_external_account or item.requires_legal_review:
        item.state = (
            RealWorldExecutionState.waiting_paid_approval
            if item.requires_money
            else RealWorldExecutionState.waiting_credentials
            if item.requires_credentials
            else RealWorldExecutionState.waiting_account_creation
            if item.requires_external_account
            else RealWorldExecutionState.waiting_legal_review
        )
        item.requires_ceo = True
        item.next_action = "No se puede marcar ejecutable: requiere CEO, dinero, credenciales, cuenta externa o revision legal."
    else:
        item.state = RealWorldExecutionState.ready_internal
        item.evidence = request.evidence or item.evidence
        item.next_action = request.note or "Lista para trabajo interno manual; no ejecutar accion externa."
    item = save_item(item)
    audit_execution_action(
        actor=actor,
        action="mark_real_world_execution_prepared",
        status=item.state.value,
        detail="Queue item moved safely without external execution.",
        metadata={"item_id": item.id},
    )
    return item


def request_approval(
    item_id: str,
    request: RealWorldExecutionActionRequest,
    actor: AuthenticatedUser,
) -> RealWorldExecutionQueueItem:
    reject_secret_like_payload(request)
    item = get_queue_item(item_id)
    item.requires_ceo = True
    item.state = (
        RealWorldExecutionState.waiting_paid_approval
        if item.requires_money
        else RealWorldExecutionState.waiting_credentials
        if item.requires_credentials
        else RealWorldExecutionState.waiting_account_creation
        if item.requires_external_account
        else RealWorldExecutionState.waiting_legal_review
        if item.requires_legal_review
        else RealWorldExecutionState.waiting_ceo
    )
    item.next_action = request.reason or request.note or "Esperar decision CEO antes de ejecutar."
    item = save_item(item)
    audit_execution_action(
        actor=actor,
        action="request_real_world_execution_approval",
        status=item.state.value,
        detail="Queue item approval requested without external execution.",
        metadata={"item_id": item.id, "requires_money": item.requires_money},
    )
    return item


def block_item(
    item_id: str,
    request: RealWorldExecutionActionRequest,
    actor: AuthenticatedUser,
) -> RealWorldExecutionQueueItem:
    reject_secret_like_payload(request)
    item = get_queue_item(item_id)
    item.state = RealWorldExecutionState.blocked
    item.requires_ceo = True
    item.next_action = request.reason or request.note or "Bloqueado hasta nueva decision CEO."
    item = save_item(item)
    audit_execution_action(
        actor=actor,
        action="block_real_world_execution_item",
        status=item.state.value,
        detail="Queue item blocked without external execution.",
        metadata={"item_id": item.id},
    )
    return item


def item_needs_approval(item: RealWorldExecutionQueueItem) -> bool:
    return (
        item.requires_ceo
        or item.requires_money
        or item.requires_credentials
        or item.requires_external_account
        or item.requires_legal_review
        or state_needs_ceo(item.state)
    )


def list_approval_needed() -> list[RealWorldExecutionQueueItem]:
    return [item for item in list_execution_queue() if item_needs_approval(item)]


def get_execution_status() -> RealWorldExecutionStatus:
    items = list_execution_queue()
    approvals = list_approval_needed()
    return RealWorldExecutionStatus(
        total_items=len(items),
        prepared=len([item for item in items if item.state == RealWorldExecutionState.prepared]),
        ready_internal=len([item for item in items if item.state == RealWorldExecutionState.ready_internal]),
        waiting_ceo=len([item for item in items if item.state == RealWorldExecutionState.waiting_ceo]),
        waiting_credentials=len([item for item in items if item.state == RealWorldExecutionState.waiting_credentials]),
        waiting_paid_approval=len([item for item in items if item.state == RealWorldExecutionState.waiting_paid_approval]),
        waiting_account_creation=len([item for item in items if item.state == RealWorldExecutionState.waiting_account_creation]),
        waiting_legal_review=len([item for item in items if item.state == RealWorldExecutionState.waiting_legal_review]),
        blocked=len([item for item in items if item.state == RealWorldExecutionState.blocked]),
        approval_needed=len(approvals),
        money_needed=len([item for item in items if item.requires_money]),
        credentials_needed=len([item for item in items if item.requires_credentials]),
        high_risk=len([item for item in items if item.risk == RealWorldExecutionRisk.high]),
        sensitive=len([item for item in items if item.risk == RealWorldExecutionRisk.sensitive]),
        manual_ready=len([item for item in items if item.ready_for_manual_execution]),
        next_steps=[
            "CEREBRO prioriza acciones internas sin ejecutar acciones reales.",
            "CEO decide cuentas externas, dinero, credenciales y revision legal.",
            "Revenue y Workday pueden leer la cola como backlog preparado.",
            "AUDITORIA bloquea items con riesgo o evidencia faltante.",
        ],
        queue_snapshot=items[:12],
        generated_at=utc_now(),
    )
