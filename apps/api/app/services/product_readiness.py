from datetime import UTC, datetime
import json
from uuid import uuid4

from app.core.database import connect, initialize_database, sql_placeholder
from app.schemas.audit import AuditCategory, AuditEventCreate, AuditSeverity
from app.schemas.auth import AuthenticatedUser
from app.schemas.product_readiness import (
    ProductReadinessAuditRecord,
    ProductReadinessAuditRequest,
    ProductReadinessEvidenceStatus,
    ProductReadinessForgeStatus,
    ProductReadinessForjaRequest,
    ProductReadinessGap,
    ProductReadinessMarketingItem,
    ProductReadinessMarketingPackage,
    ProductReadinessProduct,
    ProductReadinessStatus,
    ProductReadinessStatusValue,
)
from app.services.audit import create_audit_event

PRODUCT_READINESS_PRODUCTS_TABLE = "product_readiness_products"
PRODUCT_READINESS_GAPS_TABLE = "product_readiness_gaps"
PRODUCT_READINESS_AUDITS_TABLE = "product_readiness_audits"
PRODUCT_READINESS_MARKETING_PACKAGES_TABLE = "product_readiness_marketing_packages"

PRODUCT_READINESS_TABLES = {
    PRODUCT_READINESS_PRODUCTS_TABLE,
    PRODUCT_READINESS_GAPS_TABLE,
    PRODUCT_READINESS_AUDITS_TABLE,
    PRODUCT_READINESS_MARKETING_PACKAGES_TABLE,
}

SUPPORTED_PRODUCTS = {"dcft", "sentinela"}


class ProductReadinessError(Exception):
    def __init__(self, status_code: int, detail: dict[str, object]) -> None:
        self.status_code = status_code
        self.detail = detail
        super().__init__(str(detail))


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def normalize(value: object) -> str:
    return str(value or "").strip().lower().replace(" ", "_").replace("-", "_")


def safe_id(value: str, fallback: str) -> str:
    normalized = "".join(char if char.isalnum() else "_" for char in normalize(value))
    normalized = "_".join(part for part in normalized.split("_") if part)
    return normalized or fallback


def actor_name(user: AuthenticatedUser | None) -> str:
    if user is None:
        return "system"
    return user.email or user.name or user.id


def ensure_product_readiness_schema() -> None:
    initialize_database()
    with connect() as connection:
        for table_name in PRODUCT_READINESS_TABLES:
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
    if table_name not in PRODUCT_READINESS_TABLES:
        raise ProductReadinessError(500, {"error": "invalid_product_readiness_table", "table": table_name})


def upsert_payload(table_name: str, item_id: str, payload: dict) -> None:
    ensure_table(table_name)
    ensure_product_readiness_schema()
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
    ensure_product_readiness_schema()
    placeholder = sql_placeholder()
    with connect() as connection:
        row = connection.execute(
            f"SELECT payload_json FROM {table_name} WHERE id = {placeholder}",
            (item_id,),
        ).fetchone()
    if row is None:
        return None
    return json.loads(row[0])


def fetch_payloads(table_name: str) -> list[dict]:
    ensure_table(table_name)
    ensure_product_readiness_schema()
    with connect() as connection:
        rows = connection.execute(
            f"""
            SELECT payload_json
            FROM {table_name}
            ORDER BY created_at DESC
            """
        ).fetchall()
    return [json.loads(row[0]) for row in rows]


def audit_product_readiness_action(
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
            source="product_readiness.dcft_sentinela",
            action=action,
            status=status,
            detail=detail,
            metadata={
                "actor": actor_name(actor),
                "sales_owner": "MARKETING",
                "external_connection_enabled": False,
                "runtime_connected": False,
                "sunat_enabled": False,
                "paid_campaign_enabled": False,
                **(metadata or {}),
            },
        )
    )


def initial_product(product_id: str) -> ProductReadinessProduct:
    now = utc_now()
    if product_id == "dcft":
        return ProductReadinessProduct(
            id="dcft",
            name="DCFT - Doctor Contable Financiero Tributario",
            description=(
                "Producto contable, financiero y tributario representado en el ecosistema para readiness "
                "comercial; no se toca DCFT real ni SUNAT real."
            ),
            value_proposition=(
                "Requires validation: apoyo contable/financiero/tributario para empresas; claims legales "
                "requieren fuente oficial y auditoria."
            ),
            existing_functionality=[
                "Representado como producto protegido en el ecosistema.",
                "Gobernado como protected_no_touch.",
                "No SUNAT real, no credenciales, no runtime externo desde este frente.",
            ],
            sources_needed=[
                "Fuentes tributarias oficiales vigentes.",
                "Evidencia tecnica del producto real antes de claims.",
                "Validacion legal y contable antes de marketing publico.",
            ],
            risks=[
                "No declarar cumplimiento tributario sin fuente oficial.",
                "No prometer automatizacion SUNAT desde este frente.",
                "No vender como listo si falta evidencia de producto.",
            ],
            security_status=ProductReadinessStatusValue.requires_validation,
            sunat_enabled=False,
            created_at=now,
            updated_at=now,
        )
    if product_id == "sentinela":
        return ProductReadinessProduct(
            id="sentinela",
            name="SENTINELA",
            description=(
                "Sistema/producto de seguridad que debe estar actualizado y preparado para comercializacion "
                "cuando MARKETING lo empuje."
            ),
            value_proposition=(
                "Requires validation: seguridad y proteccion del ecosistema con evidencia tecnica pendiente."
            ),
            existing_functionality=[
                "Representado como producto/sistema de seguridad preparado.",
                "No runtime real ni conexion productiva desde este frente.",
                "Capacidades de seguridad requieren evidencia antes de claims.",
            ],
            sources_needed=[
                "Fuentes de amenazas y riesgos actualizadas.",
                "Evidencia tecnica de capacidades defensivas.",
                "Auditoria de seguridad antes de marketing publico.",
            ],
            risks=[
                "No prometer proteccion total.",
                "No declarar deteccion o respuesta real sin evidencia.",
                "No activar integraciones de seguridad reales desde este frente.",
            ],
            security_status=ProductReadinessStatusValue.requires_validation,
            created_at=now,
            updated_at=now,
        )
    raise ProductReadinessError(404, {"error": "product_readiness_product_not_supported", "product_id": product_id})


def initial_gap(product_id: str, area: str, title: str, description: str, severity: str = "medium") -> ProductReadinessGap:
    now = utc_now()
    return ProductReadinessGap(
        id=f"product_gap_{product_id}_{safe_id(title, 'gap')}",
        product_id=product_id,
        area=area,
        title=title,
        description=description,
        severity=severity,
        created_at=now,
        updated_at=now,
    )


def initial_gaps(product_id: str) -> list[ProductReadinessGap]:
    if product_id == "dcft":
        return [
            initial_gap("dcft", "legal_risk", "Fuentes tributarias oficiales faltantes", "Validar cambios contables/tributarios con fuentes oficiales antes de claims.", "high"),
            initial_gap("dcft", "technical", "Evidencia tecnica del producto real pendiente", "Documentar funcionalidades existentes sin tocar DCFT real.", "high"),
            initial_gap("dcft", "commercial", "Landing y onboarding requieren validacion", "Preparar landing y onboarding sin publicar ni vender automatico.", "medium"),
            initial_gap("dcft", "pricing", "Pricing comercial requiere evidencia", "No declarar precio final desde este frente si falta decision comercial.", "medium"),
            initial_gap("dcft", "app_store", "App Store y Play Store unknown", "No publicar ni crear cuenta de tienda; evaluar requisitos y riesgos.", "medium"),
        ]
    if product_id == "sentinela":
        return [
            initial_gap("sentinela", "security", "Evidencia de capacidades defensivas pendiente", "No prometer deteccion, respuesta o proteccion real sin pruebas.", "high"),
            initial_gap("sentinela", "updates", "Fuentes de amenazas pendientes", "Definir fuentes de amenazas actualizadas antes de claims de seguridad.", "high"),
            initial_gap("sentinela", "commercial", "Landing y onboarding requieren validacion", "Preparar material para MARKETING sin activacion real.", "medium"),
            initial_gap("sentinela", "pricing", "Pricing comercial requiere decision", "No asignar meta propia ni precio final sin evidencia comercial.", "medium"),
            initial_gap("sentinela", "app_store", "App Store y Play Store unknown", "Evaluar readiness de tiendas sin publicar.", "medium"),
        ]
    return []


def seed_product_readiness() -> None:
    ensure_product_readiness_schema()
    for product_id in SUPPORTED_PRODUCTS:
        if fetch_payload(PRODUCT_READINESS_PRODUCTS_TABLE, product_id) is None:
            product = initial_product(product_id)
            upsert_payload(PRODUCT_READINESS_PRODUCTS_TABLE, product.id, product.model_dump(mode="json"))
        existing_gaps = [
            gap for gap in fetch_payloads(PRODUCT_READINESS_GAPS_TABLE)
            if gap.get("product_id") == product_id
        ]
        if not existing_gaps:
            for gap in initial_gaps(product_id):
                upsert_payload(PRODUCT_READINESS_GAPS_TABLE, gap.id, gap.model_dump(mode="json"))


def list_gaps(product_id: str | None = None) -> list[ProductReadinessGap]:
    seed_product_readiness()
    gaps = [ProductReadinessGap(**payload) for payload in fetch_payloads(PRODUCT_READINESS_GAPS_TABLE)]
    if product_id:
        product_id = normalize_product_id(product_id)
        gaps = [gap for gap in gaps if gap.product_id == product_id]
    return sorted(gaps, key=lambda gap: (gap.product_id, gap.area, gap.title))


def normalize_product_id(product_id: str) -> str:
    normalized = normalize(product_id)
    if normalized in {"doctor_contable_financiero_tributario", "doctor_contable", "doctor_cft"}:
        return "dcft"
    if normalized in {"centinela", "sentinel"}:
        return "sentinela"
    if normalized not in SUPPORTED_PRODUCTS:
        raise ProductReadinessError(404, {"error": "product_readiness_product_not_supported", "product_id": product_id})
    return normalized


def get_product(product_id: str) -> ProductReadinessProduct:
    seed_product_readiness()
    normalized = normalize_product_id(product_id)
    payload = fetch_payload(PRODUCT_READINESS_PRODUCTS_TABLE, normalized)
    if payload is None:
        raise ProductReadinessError(404, {"error": "product_readiness_product_not_found", "product_id": normalized})
    product = ProductReadinessProduct(**payload)
    product.gaps = list_gaps(normalized)
    return product


def list_products() -> list[ProductReadinessProduct]:
    return [get_product(product_id) for product_id in sorted(SUPPORTED_PRODUCTS)]


def save_product(product: ProductReadinessProduct) -> ProductReadinessProduct:
    product.updated_at = utc_now()
    upsert_payload(PRODUCT_READINESS_PRODUCTS_TABLE, product.id, product.model_dump(mode="json"))
    product.gaps = list_gaps(product.id)
    return product


def save_gap(gap: ProductReadinessGap) -> ProductReadinessGap:
    gap.updated_at = utc_now()
    upsert_payload(PRODUCT_READINESS_GAPS_TABLE, gap.id, gap.model_dump(mode="json"))
    return gap


def get_gap(gap_id: str) -> ProductReadinessGap:
    seed_product_readiness()
    payload = fetch_payload(PRODUCT_READINESS_GAPS_TABLE, gap_id)
    if payload is None:
        raise ProductReadinessError(404, {"error": "product_readiness_gap_not_found", "gap_id": gap_id})
    return ProductReadinessGap(**payload)


def audit_product_readiness(
    product_id: str,
    request: ProductReadinessAuditRequest,
    actor: AuthenticatedUser,
) -> ProductReadinessProduct:
    product = get_product(product_id)
    evidence_status = (
        ProductReadinessEvidenceStatus.partial
        if request.evidence or request.source
        else ProductReadinessEvidenceStatus.missing
    )
    product.audit_status = ProductReadinessStatusValue.requires_validation
    product.evidence_status = evidence_status
    product.commercial_status = ProductReadinessStatusValue.requires_validation
    product.marketing_package_status = "requires_validation"
    product = save_product(product)
    record = ProductReadinessAuditRecord(
        id=f"product_readiness_audit_{product.id}_{uuid4().hex[:8]}",
        product_id=product.id,
        evidence=request.evidence,
        source=request.source,
        notes=request.notes,
        evidence_status=evidence_status,
        result_status=ProductReadinessStatusValue.requires_validation,
        created_by=actor_name(actor),
        created_at=utc_now(),
    )
    upsert_payload(PRODUCT_READINESS_AUDITS_TABLE, record.id, record.model_dump(mode="json"))
    audit_product_readiness_action(
        actor=actor,
        action=f"audit_{product.id}",
        status="requires_validation",
        detail=f"{product.name} auditado sin declarar producto listo.",
        metadata={"product_id": product.id, "evidence_status": evidence_status.value},
    )
    return product


def send_gap_to_forja(
    gap_id: str,
    request: ProductReadinessForjaRequest,
    actor: AuthenticatedUser,
) -> ProductReadinessGap:
    gap = get_gap(gap_id)
    gap.status = "sent_to_forja"
    gap.forge_status = ProductReadinessForgeStatus.prepared
    gap.technical_status = "pending_execution"
    gap.requires_validation = True
    gap = save_gap(gap)
    audit_product_readiness_action(
        actor=actor,
        action="send_gap_to_forja",
        status="prepared",
        detail="Brecha enviada a FORJA como tarea preparada; no implementada.",
        metadata={
            "gap_id": gap.id,
            "product_id": gap.product_id,
            "instruction": request.instruction,
            "technical_status": gap.technical_status,
        },
    )
    return gap


def build_marketing_item(product: ProductReadinessProduct) -> ProductReadinessMarketingItem:
    gaps = list_gaps(product.id)
    if product.id == "dcft":
        target_audience = ["MYPE", "empresa", "contador", "gerencia financiera"]
        objections = [
            "Requiere fuente legal y tributaria oficial.",
            "No prometer SUNAT real desde ecosystem.",
            "Debe probarse onboarding y soporte antes de venta publica.",
        ]
        arguments = [
            "Producto prioritario para MARKETING si la evidencia tecnica y legal se valida.",
            "Puede comunicar preparacion contable/financiera sin prometer cumplimiento automatico.",
        ]
        pieces = ["landing validada", "guion PLUMA revisado", "demo no sensible", "FAQ legal", "onboarding"]
        pluma = ["post educativo sin claim legal", "FAQ con disclaimers", "guion de demo"]
        lente = ["video demo preparado", "visual de flujo contable sin datos reales"]
    else:
        target_audience = ["empresa", "operaciones", "equipos con riesgo digital", "CEO"]
        objections = [
            "Requiere evidencia de capacidades defensivas.",
            "No prometer proteccion total.",
            "Debe auditarse antes de campaña publica.",
        ]
        arguments = [
            "Sistema/producto de seguridad preparado para comercializacion cuando MARKETING lo empuje.",
            "Debe comunicar proteccion y riesgo solo con evidencia verificable.",
        ]
        pieces = ["landing de seguridad validada", "guion PLUMA", "visual LENTE", "matriz de riesgos", "onboarding"]
        pluma = ["post de concientizacion", "brief de riesgos", "FAQ de seguridad sin claims absolutos"]
        lente = ["visual de tablero de riesgos", "video corto de proteccion preparada"]
    return ProductReadinessMarketingItem(
        product_id=product.id,
        product_name=product.name,
        sales_owner="MARKETING",
        has_own_sales_goal=False,
        value_proposition=product.value_proposition,
        target_audience=target_audience,
        objections=objections,
        arguments=arguments,
        required_pieces=pieces,
        landing_required=True,
        pluma_content=pluma,
        lente_content=lente,
        risks=product.risks,
        gaps=[gap.title for gap in gaps],
        readiness_status="requires_validation",
        claim_status="requires_validation",
    )


def build_marketing_package(actor: AuthenticatedUser | None = None) -> ProductReadinessMarketingPackage:
    products = list_products()
    package = ProductReadinessMarketingPackage(
        id="product_readiness_marketing_package_current",
        items=[build_marketing_item(product) for product in products],
        generated_at=utc_now(),
        generated_by=actor_name(actor),
    )
    return package


def get_marketing_package() -> ProductReadinessMarketingPackage:
    seed_product_readiness()
    payload = fetch_payload(PRODUCT_READINESS_MARKETING_PACKAGES_TABLE, "product_readiness_marketing_package_current")
    if payload is None:
        return build_marketing_package()
    return ProductReadinessMarketingPackage(**payload)


def generate_marketing_package(actor: AuthenticatedUser) -> ProductReadinessMarketingPackage:
    package = build_marketing_package(actor)
    upsert_payload(
        PRODUCT_READINESS_MARKETING_PACKAGES_TABLE,
        package.id,
        package.model_dump(mode="json"),
    )
    audit_product_readiness_action(
        actor=actor,
        action="generate_marketing_package",
        status=package.status,
        detail="Marketing package preparado sin claims legales o de seguridad no validados.",
        metadata={"items": len(package.items)},
    )
    return package


def get_product_readiness_status() -> ProductReadinessStatus:
    products = list_products()
    gaps = list_gaps()
    package = get_marketing_package()
    unknown_items = 0
    requires_validation = 0
    for product in products:
        statuses = [
            product.technical_status,
            product.commercial_status,
            product.legal_risk_status,
            product.app_store_status,
            product.play_store_status,
            product.update_status,
            product.audit_status,
        ]
        unknown_items += sum(1 for status in statuses if status == ProductReadinessStatusValue.unknown)
        requires_validation += sum(1 for status in statuses if status == ProductReadinessStatusValue.requires_validation)
    return ProductReadinessStatus(
        status="product_readiness_prepared_requires_validation",
        products=len(products),
        dcft_status=get_product("dcft").commercial_status.value,
        sentinela_status=get_product("sentinela").commercial_status.value,
        products_with_own_sales_goal=sum(1 for product in products if product.has_own_sales_goal),
        open_gaps=sum(1 for gap in gaps if gap.status in {"open", "sent_to_forja"}),
        gaps_sent_to_forja=sum(1 for gap in gaps if gap.forge_status == ProductReadinessForgeStatus.prepared),
        requires_validation=requires_validation,
        unknown_items=unknown_items,
        marketing_package_status=package.status,
        products_snapshot=products,
        marketing_package=package.model_dump(mode="json"),
        generated_at=utc_now(),
    )
