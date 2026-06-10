from datetime import UTC, datetime
import json
import re
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.core.safe_data import safe_payload
from app.schemas.arsenal import (
    ArsenalAuditStatus,
    ArsenalCatalogItem,
    ArsenalCatalogItemCreate,
    ArsenalCatalogItemEvaluateRequest,
    ArsenalCatalogItemStatus,
    ArsenalCategory,
    ArsenalPermissionRule,
    ArsenalReadiness,
    ArsenalRisk,
    ArsenalRiskCreate,
    ArsenalStatus,
)
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.cerebro import CerebroTaskCreate
from app.schemas.revenue import RevenueOpportunityCreate
from app.services.audit import create_audit_event
from app.services.cerebro import create_cerebro_task
from app.services.revenue import create_opportunity

ARSENAL_CATALOG_TABLE = "arsenal_catalog_items"
ARSENAL_RISKS_TABLE = "arsenal_risks"

SECRET_VALUE_PATTERN = re.compile(r"sk-[A-Za-z0-9_-]{8,}")
SECRET_KEYS = {
    "api_key",
    "apikey",
    "secret",
    "secret_value",
    "client_secret",
    "token",
    "password",
    "credential",
    "credentials",
    "private_key",
}
ALLOWED_SECRET_FLAG_KEYS = {"requires_secret", "secrets_stored"}

CATEGORIES = [
    ("apis_internas", "APIs internas", "Capacidades API para uso interno del ecosistema."),
    ("apis_vendibles", "APIs vendibles", "APIs que podrian convertirse en producto tecnico vendible."),
    ("skills_internas", "Skills internas", "Skills para productividad y operacion interna."),
    ("skills_vendibles", "Skills vendibles", "Skills empaquetables para venta futura."),
    ("modelos_ia", "Modelos IA", "Modelos, evaluaciones y configuraciones de IA."),
    ("conectores", "Conectores", "Puentes preparados hacia sistemas o servicios, sin conexion real."),
    ("automatizaciones", "Automatizaciones", "Flujos internos repetibles sin runtime externo."),
    ("prompts_sistemas", "Prompts/sistemas", "Prompts, instrucciones y sistemas reutilizables."),
    ("herramientas_contenido", "Herramientas de contenido", "Soporte a PLUMA y LENTE."),
    ("herramientas_marketing", "Herramientas de marketing", "Soporte a demanda, leads y embudos."),
    ("herramientas_ecommerce", "Herramientas de ecommerce", "Soporte a e-commerce y Sniff Amazon."),
    ("herramientas_ciberseguridad", "Herramientas de ciberseguridad", "Capacidades defensivas para SENTINELA futura."),
    ("herramientas_contables_tributarias", "Herramientas contables/tributarias", "Capacidades preparadas para DCFT, sin SUNAT real."),
    ("herramientas_cloud", "Herramientas cloud", "Capacidades de control cloud para NUBE."),
    ("herramientas_investigacion", "Herramientas de investigacion", "Buscador de tendencias e investigacion."),
    ("experimentos", "Experimentos", "Ideas y pruebas preparadas sin runtime."),
]


class ArsenalError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def actor_name(user: AuthenticatedUser) -> str:
    return user.email or user.name or user.id


def ensure_arsenal_schema() -> None:
    initialize_database()
    with connect() as connection:
        for table_name in [ARSENAL_CATALOG_TABLE, ARSENAL_RISKS_TABLE]:
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


def insert_payload(table_name: str, item_id: str, payload: str) -> None:
    ensure_arsenal_schema()
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
    ensure_arsenal_schema()
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
    ensure_arsenal_schema()
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
    ensure_arsenal_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    return safe_payload(row) if row else None


def audit_arsenal_action(
    *,
    actor: AuthenticatedUser | None,
    action: str,
    status: str,
    detail: str,
    severity: AuditSeverity = AuditSeverity.info,
    metadata: dict[str, object] | None = None,
) -> str:
    event = create_audit_event(
        AuditEventCreate(
            category=AuditCategory.data_change,
            severity=severity,
            source="arsenal.blueprint",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "actor": actor_name(actor) if actor else "system",
                "external_connection_enabled": False,
                "runtime_connected": False,
                "payment_connected": False,
                "secrets_stored": False,
                **(metadata or {}),
            },
        )
    )
    return event.id


def contains_secret_payload(value: object, path: str = "payload") -> str | None:
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized_key = normalize(key)
            if normalized_key in SECRET_KEYS and normalized_key not in ALLOWED_SECRET_FLAG_KEYS:
                return f"{path}.{key}"
            nested_finding = contains_secret_payload(nested, f"{path}.{key}")
            if nested_finding:
                return nested_finding
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            nested_finding = contains_secret_payload(nested, f"{path}[{index}]")
            if nested_finding:
                return nested_finding
    elif isinstance(value, str) and SECRET_VALUE_PATTERN.search(value):
        return path
    return None


def assert_no_secret_payload(payload: dict) -> None:
    finding = contains_secret_payload(payload)
    if finding:
        raise ArsenalError(
            400,
            {
                "error": "arsenal_secret_payload_rejected",
                "field": finding,
                "reason": "ARSENAL stores metadata only; do not send API keys, tokens, passwords or secrets.",
            },
        )


def permission_rules() -> list[ArsenalPermissionRule]:
    return [
        ArsenalPermissionRule(
            action="view",
            allowed_roles=["ceo", "admin", "operator", "auditor"],
            notes="Lectura interna protegida del blueprint.",
        ),
        ArsenalPermissionRule(
            action="add_catalog_item",
            allowed_roles=["ceo", "admin", "operator"],
            notes="CEREBRO y operacion pueden registrar metadata, nunca secretos.",
        ),
        ArsenalPermissionRule(
            action="evaluate",
            allowed_roles=["ceo", "admin", "operator", "auditor"],
            notes="Evaluacion local preparada sin conectar APIs externas.",
        ),
        ArsenalPermissionRule(
            action="approve_cost_or_secret",
            allowed_roles=["ceo", "admin"],
            requires_ceo_approval=True,
            notes="Costo, credenciales o cuentas externas requieren CEO.",
        ),
        ArsenalPermissionRule(
            action="send_to_forja",
            allowed_roles=["ceo", "admin", "operator"],
            notes="FORJA recibe tarea preparada, no runtime externo.",
        ),
        ArsenalPermissionRule(
            action="mark_sellable",
            allowed_roles=["ceo", "admin", "operator"],
            requires_auditoria=True,
            notes="Vendible requiere revision de AUDITORIA antes de venta real.",
        ),
    ]


def list_catalog_items() -> list[ArsenalCatalogItem]:
    ensure_arsenal_schema()
    items: list[ArsenalCatalogItem] = []
    for payload in fetch_payloads(ARSENAL_CATALOG_TABLE):
        try:
            items.append(ArsenalCatalogItem(**payload))
        except Exception:
            continue
    return items


def get_catalog_item(item_id: str) -> ArsenalCatalogItem:
    payload = fetch_payload(ARSENAL_CATALOG_TABLE, item_id)
    if payload is None:
        raise ArsenalError(404, {"error": "arsenal_catalog_item_not_found", "item_id": item_id})
    return ArsenalCatalogItem(**payload)


def list_categories() -> list[ArsenalCategory]:
    items = list_catalog_items()
    rows: list[ArsenalCategory] = []
    for category_id, name, description in CATEGORIES:
        related = [
            item
            for item in items
            if normalize(item.category) == category_id or normalize(item.category) == normalize(name)
        ]
        rows.append(
            ArsenalCategory(
                id=category_id,
                name=name,
                description=description,
                status="prepared" if related else "empty/prepared",
                items=len(related),
                sellable_items=len([item for item in related if item.is_sellable]),
            )
        )
    return rows


def status_for_item(request: ArsenalCatalogItemCreate) -> ArsenalCatalogItemStatus:
    if request.status is not None:
        return request.status
    if request.cost_usd > 0 or request.requires_secret:
        return ArsenalCatalogItemStatus.needs_ceo_approval
    if request.is_sellable:
        return ArsenalCatalogItemStatus.needs_audit
    return ArsenalCatalogItemStatus.prepared


def audit_status_for_item(request: ArsenalCatalogItemCreate) -> ArsenalAuditStatus:
    if request.is_sellable:
        return ArsenalAuditStatus.requires_auditoria
    return ArsenalAuditStatus.pending if request.requires_external_api else ArsenalAuditStatus.not_required


def create_catalog_item(
    request: ArsenalCatalogItemCreate,
    actor: AuthenticatedUser,
) -> ArsenalCatalogItem:
    assert_no_secret_payload(request.model_dump(mode="json"))
    now = utc_now()
    requires_ceo = request.cost_usd > 0 or request.requires_secret
    item = ArsenalCatalogItem(
        id=f"arsenal_item_{uuid4()}",
        name=request.name,
        item_type=request.item_type,
        category=request.category,
        internal_use=request.internal_use,
        sellable_use=request.sellable_use,
        is_sellable=request.is_sellable,
        cost_usd=request.cost_usd,
        requires_secret=request.requires_secret,
        requires_external_api=request.requires_external_api,
        requires_ceo_approval=requires_ceo,
        requires_auditoria=request.is_sellable,
        status=status_for_item(request),
        risk=request.risk,
        monetization=request.monetization,
        owner=request.owner,
        audit_status=audit_status_for_item(request),
        metadata=request.metadata,
        created_at=now,
        updated_at=now,
    )
    insert_payload(ARSENAL_CATALOG_TABLE, item.id, item.model_dump_json())
    audit_arsenal_action(
        actor=actor,
        action="create_catalog_item",
        status=item.status.value,
        detail="ARSENAL registered metadata for a capability without storing secrets.",
        metadata={
            "item_id": item.id,
            "category": item.category,
            "requires_ceo_approval": item.requires_ceo_approval,
            "requires_auditoria": item.requires_auditoria,
        },
    )
    return item


def evaluate_catalog_item(
    item_id: str,
    request: ArsenalCatalogItemEvaluateRequest,
    actor: AuthenticatedUser,
) -> ArsenalCatalogItem:
    assert_no_secret_payload(request.model_dump(mode="json"))
    item = get_catalog_item(item_id)
    item.risk = request.risk or item.risk
    item.monetization = request.monetization or item.monetization
    item.audit_status = request.audit_status or item.audit_status
    item.technical_status = request.technical_status or "blueprint_evaluated"
    if item.audit_status == ArsenalAuditStatus.requires_auditoria:
        item.requires_auditoria = True
    if item.cost_usd > 0 or item.requires_secret:
        item.requires_ceo_approval = True
        item.status = ArsenalCatalogItemStatus.needs_ceo_approval
    elif item.requires_auditoria:
        item.status = ArsenalCatalogItemStatus.needs_audit
    else:
        item.status = ArsenalCatalogItemStatus.evaluated

    if request.evaluate_revenue_os or (item.is_sellable and request.expected_revenue_usd is not None):
        revenue = create_opportunity(
            RevenueOpportunityCreate(
                title=f"ARSENAL: {item.name}",
                origin="ARSENAL",
                department="CREADOR DE APIS Y SKILLS",
                related_product=item.name,
                action_type="organic" if item.cost_usd == 0 else "paid_api",
                investment_usd=item.cost_usd,
                expected_revenue_usd=request.expected_revenue_usd,
                probability_percent=request.probability_percent,
                risk=item.risk,
                payback_time="not_estimated",
                ecommerce_separate=False,
                recommendation=item.monetization,
            ),
            actor,
        )
        item.revenue_opportunity_id = revenue.id

    if request.send_to_forja:
        task = create_cerebro_task(
            CerebroTaskCreate(
                title=f"Preparar capacidad ARSENAL: {item.name}",
                description=f"FORJA recibe blueprint preparado para {item.name}; sin runtime externo.",
                destination="forja",
                priority="p1" if item.is_sellable else "p2",
                reason="Tarea preparada desde ARSENAL blueprint.",
                requires_ceo_approval=item.requires_ceo_approval,
            ),
            actor,
        )
        item.forja_task_id = task.id

    item.updated_at = utc_now()
    update_payload(ARSENAL_CATALOG_TABLE, item.id, item.model_dump_json())
    audit_arsenal_action(
        actor=actor,
        action="evaluate_catalog_item",
        status=item.status.value,
        detail="ARSENAL evaluated a capability blueprint without external connection.",
        metadata={
            "item_id": item.id,
            "revenue_opportunity_id": item.revenue_opportunity_id,
            "forja_task_id": item.forja_task_id,
        },
    )
    return item


def send_catalog_item_to_forja(item_id: str, actor: AuthenticatedUser) -> dict[str, object]:
    item = get_catalog_item(item_id)
    task = create_cerebro_task(
        CerebroTaskCreate(
            title=f"Preparar capacidad ARSENAL: {item.name}",
            description=f"FORJA recibe blueprint preparado para {item.name}; sin runtime externo.",
            destination="forja",
            priority="p1" if item.is_sellable else "p2",
            reason="Tarea preparada desde ARSENAL blueprint.",
            requires_ceo_approval=item.requires_ceo_approval,
        ),
        actor,
    )
    item.forja_task_id = task.id
    item.updated_at = utc_now()
    update_payload(ARSENAL_CATALOG_TABLE, item.id, item.model_dump_json())
    audit_arsenal_action(
        actor=actor,
        action="send_catalog_item_to_forja",
        status="prepared",
        detail="ARSENAL sent a prepared task to FORJA without touching external FORJA runtime.",
        metadata={"item_id": item.id, "task_id": task.id},
    )
    return {
        "status": "forja_task_prepared",
        "item_id": item.id,
        "task_id": task.id,
        "destination": task.destination,
        "runtime_connected": False,
        "external_connection_enabled": False,
    }


def list_risks() -> list[ArsenalRisk]:
    ensure_arsenal_schema()
    return [
        ArsenalRisk(**payload)
        for payload in fetch_payloads(ARSENAL_RISKS_TABLE)
    ]


def create_risk(request: ArsenalRiskCreate, actor: AuthenticatedUser) -> ArsenalRisk:
    assert_no_secret_payload(request.model_dump(mode="json"))
    now = utc_now()
    risk = ArsenalRisk(
        id=f"arsenal_risk_{uuid4()}",
        title=request.title,
        category=request.category,
        severity=request.severity,
        detail=request.detail,
        mitigation=request.mitigation,
        related_item_id=request.related_item_id,
        created_at=now,
        updated_at=now,
    )
    insert_payload(ARSENAL_RISKS_TABLE, risk.id, risk.model_dump_json())
    audit_arsenal_action(
        actor=actor,
        action="create_risk",
        status=risk.status,
        detail="ARSENAL registered a blueprint risk.",
        severity=AuditSeverity.medium if risk.severity in {"high", "critical"} else AuditSeverity.info,
        metadata={"risk_id": risk.id, "category": risk.category},
    )
    return risk


def get_readiness() -> ArsenalReadiness:
    items = list_catalog_items()
    risks = list_risks()
    blockers: list[str] = []
    next_steps = [
        "Completar catalogo inicial sin secretos.",
        "Auditar items vendibles antes de vender.",
        "Pedir CEO si hay costo, credenciales o cuenta externa.",
        "Conectar Revenue OS solo como evaluacion de monetizacion.",
    ]
    cost_or_secret = [item for item in items if item.requires_ceo_approval]
    sellable = [item for item in items if item.is_sellable]
    if not items:
        blockers.append("catalog_empty")
    if any(risk.severity in {"high", "critical"} and risk.status == "open" for risk in risks):
        blockers.append("high_risk_open")
    if cost_or_secret:
        blockers.append("ceo_approval_required_for_cost_or_secret")
    if any(item.audit_status == ArsenalAuditStatus.requires_auditoria for item in sellable):
        blockers.append("auditoria_required_for_sellable_items")
    score = 60
    if items:
        score += 15
    if sellable:
        score += 10
    if risks:
        score += 5
    score -= min(len(blockers) * 8, 35)
    score = max(0, min(100, score))
    return ArsenalReadiness(
        status="blueprint_ready_for_review" if items else "blueprint_empty_prepared",
        score=score,
        ready_for_build=bool(items) and not blockers,
        blockers=blockers,
        next_steps=next_steps,
        categories_total=len(CATEGORIES),
        catalog_items=len(items),
        sellable_items=len(sellable),
        items_requiring_ceo_approval=len(cost_or_secret),
        risks_open=len([risk for risk in risks if risk.status == "open"]),
    )


def get_status() -> ArsenalStatus:
    categories = list_categories()
    items = list_catalog_items()
    risks = list_risks()
    readiness = get_readiness()
    return ArsenalStatus(
        status="arsenal_blueprint_governed_prepared",
        mode="metadata_only_no_external_runtime",
        purpose="Almacen estrategico de APIs, skills, modelos, conectores y capacidades.",
        categories=len(categories),
        catalog_items=len(items),
        sellable_items=len([item for item in items if item.is_sellable]),
        items_requiring_ceo_approval=len([item for item in items if item.requires_ceo_approval]),
        risks_open=len([risk for risk in risks if risk.status == "open"]),
        permissions=permission_rules(),
        readiness=readiness,
        generated_at=utc_now(),
    )
