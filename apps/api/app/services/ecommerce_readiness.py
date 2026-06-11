from datetime import UTC, datetime

from app.schemas.ecommerce_readiness import (
    AmazonReadinessStatus,
    CommerceOpportunity,
    CommerceReadinessState,
    CommerceRiskLevel,
    EcommerceReadinessStatus,
)

ECOMMERCE_MONTHLY_GOAL_USD = 10000
GLOBAL_MONTHLY_GOAL_USD = 6000


def utc_now() -> str:
    return datetime.now(UTC).isoformat().replace("+00:00", "Z")


def opportunity(
    item_id: str,
    business_line: str,
    platform: str,
    product_category: str,
    state: CommerceReadinessState,
    next_action: str,
    *,
    evidence: str = "missing",
    investment_needed: str = "unknown",
    margin_estimated: str = "unknown_not_estimated",
    requires_ceo: bool = False,
    requires_external_account: bool = False,
    requires_credentials: bool = False,
    requires_supplier: bool = False,
    requires_payment_provider: bool = False,
    requires_inventory: bool = False,
    requires_paid_tool: bool = False,
    risk: CommerceRiskLevel = CommerceRiskLevel.medium,
) -> CommerceOpportunity:
    now = utc_now()
    return CommerceOpportunity(
        id=item_id,
        business_line=business_line,
        platform=platform,
        product_category=product_category,
        state=state,
        evidence=evidence,
        investment_needed=investment_needed,
        margin_estimated=margin_estimated,
        requires_ceo=requires_ceo,
        requires_external_account=requires_external_account,
        requires_credentials=requires_credentials,
        requires_supplier=requires_supplier,
        requires_payment_provider=requires_payment_provider,
        requires_inventory=requires_inventory,
        requires_paid_tool=requires_paid_tool,
        risk=risk,
        next_action=next_action,
        can_continue_prepared=True,
        target_goal_usd=ECOMMERCE_MONTHLY_GOAL_USD,
        separated_from_global_goal=True,
        real_sales_confirmed=False,
        real_margin_confirmed=False,
        payment_connected=False,
        amazon_seller_connected=False,
        store_created=False,
        inventory_purchased=False,
        prohibited_scraping_enabled=False,
        external_connection_enabled=False,
        credentials_stored=False,
        created_at=now,
        updated_at=now,
    )


def ecommerce_opportunities() -> list[CommerceOpportunity]:
    o = opportunity
    return [
        o("ecommerce_storefront_model", "E-Commerce", "Tienda propia", "catalogo por definir", CommerceReadinessState.prepared, "Preparar arquitectura de tienda sin crear tienda real.", evidence="internal_docs", risk=CommerceRiskLevel.low),
        o("ecommerce_payment_provider", "E-Commerce", "Tienda propia", "pagos", CommerceReadinessState.needs_payment_provider, "Definir proveedor y aprobacion CEO antes de conectar pagos.", requires_ceo=True, requires_credentials=True, requires_payment_provider=True, risk=CommerceRiskLevel.sensitive),
        o("ecommerce_supplier_map", "E-Commerce", "Proveedor", "proveedores", CommerceReadinessState.needs_supplier, "Hacer research de proveedores sin comprar inventario.", requires_ceo=True, requires_supplier=True, requires_inventory=True, investment_needed="unknown_requires_ceo", risk=CommerceRiskLevel.high),
        o("ecommerce_logistics_map", "E-Commerce", "Logistica", "envios", CommerceReadinessState.needs_market_research, "Preparar matriz logistica sin contratar servicios.", evidence="missing", risk=CommerceRiskLevel.medium),
        o("ecommerce_marketplace_option", "E-Commerce", "Marketplace", "marketplace", CommerceReadinessState.needs_account_creation, "Crear cuenta marketplace solo con aprobacion CEO.", requires_ceo=True, requires_external_account=True, requires_credentials=True, risk=CommerceRiskLevel.sensitive),
        o("ecommerce_product_shortlist", "E-Commerce", "Tienda propia", "productos candidatos", CommerceReadinessState.needs_market_research, "Investigar demanda y margen; no declarar productos ganadores.", evidence="missing", margin_estimated="unknown_not_estimated", risk=CommerceRiskLevel.high),
        o("ecommerce_content_engine", "E-Commerce", "Publishing", "contenido organico", CommerceReadinessState.prepared, "MARKETING/PLUMA/LENTE pueden preparar contenido sin publicar real.", evidence="internal_docs", risk=CommerceRiskLevel.low),
        o("ecommerce_analytics_manual", "E-Commerce", "Analytics manual", "metricas", CommerceReadinessState.prepared, "Preparar tablero manual; ventas reales permanecen en 0 hasta evidencia.", evidence="internal_docs", risk=CommerceRiskLevel.low),
    ]


def amazon_opportunities() -> list[CommerceOpportunity]:
    o = opportunity
    return [
        o("amazon_seller_account", "SNIFF AMAZON / CHIEF AMAZON", "Amazon Seller", "cuenta seller", CommerceReadinessState.needs_account_creation, "Amazon Seller requiere CEO, credenciales y revision antes de crear o conectar.", requires_ceo=True, requires_external_account=True, requires_credentials=True, risk=CommerceRiskLevel.sensitive),
        o("amazon_product_radar", "SNIFF AMAZON / CHIEF AMAZON", "Radar Amazon", "senales de producto", CommerceReadinessState.prepared, "Preparar criterios de radar sin scraping prohibido ni herramienta paga.", evidence="internal_docs", risk=CommerceRiskLevel.low),
        o("amazon_paid_research_tool", "SNIFF AMAZON / CHIEF AMAZON", "Herramienta externa", "research Amazon", CommerceReadinessState.needs_paid_tool, "Herramienta con costo requiere ROI y CEO antes de usar.", requires_ceo=True, requires_paid_tool=True, requires_credentials=True, investment_needed="unknown_requires_ceo", risk=CommerceRiskLevel.sensitive),
        o("amazon_buy_box_tracking", "SNIFF AMAZON / CHIEF AMAZON", "Amazon", "buy box tracking", CommerceReadinessState.needs_market_research, "Validar fuente permitida; no scraping prohibido.", requires_ceo=True, risk=CommerceRiskLevel.high),
        o("amazon_category_hypotheses", "SNIFF AMAZON / CHIEF AMAZON", "Radar Amazon", "categorias candidatas", CommerceReadinessState.idea, "Formular hipotesis sin declarar producto ganador ni margen.", evidence="missing", margin_estimated="unknown_not_estimated", risk=CommerceRiskLevel.medium),
        o("amazon_content_bridge", "SNIFF AMAZON / CHIEF AMAZON", "Publishing", "contenido organico", CommerceReadinessState.prepared, "Preparar contenido educativo sin afiliados ni venta real.", evidence="internal_docs", risk=CommerceRiskLevel.low),
    ]


def list_ecommerce_opportunities() -> list[CommerceOpportunity]:
    return ecommerce_opportunities()


def list_amazon_opportunities() -> list[CommerceOpportunity]:
    return amazon_opportunities()


def needs_approval(item: CommerceOpportunity) -> bool:
    return (
        item.requires_ceo
        or item.requires_external_account
        or item.requires_credentials
        or item.requires_supplier
        or item.requires_payment_provider
        or item.requires_inventory
        or item.requires_paid_tool
        or item.state
        in {
            CommerceReadinessState.needs_supplier,
            CommerceReadinessState.needs_payment_provider,
            CommerceReadinessState.needs_account_creation,
            CommerceReadinessState.needs_paid_tool,
            CommerceReadinessState.blocked,
        }
    )


def list_ecommerce_approval_needed() -> list[CommerceOpportunity]:
    return [item for item in list_ecommerce_opportunities() if needs_approval(item)]


def list_amazon_risks() -> list[CommerceOpportunity]:
    return [
        item
        for item in list_amazon_opportunities()
        if item.risk in {CommerceRiskLevel.high, CommerceRiskLevel.sensitive}
    ]


def get_ecommerce_readiness_status() -> EcommerceReadinessStatus:
    items = list_ecommerce_opportunities()
    approvals = list_ecommerce_approval_needed()
    return EcommerceReadinessStatus(
        opportunities=len(items),
        prepared=len([item for item in items if item.state == CommerceReadinessState.prepared]),
        unknown=len([item for item in items if item.state == CommerceReadinessState.unknown]),
        needs_market_research=len([item for item in items if item.state == CommerceReadinessState.needs_market_research]),
        needs_supplier=len([item for item in items if item.state == CommerceReadinessState.needs_supplier]),
        needs_payment_provider=len([item for item in items if item.state == CommerceReadinessState.needs_payment_provider]),
        needs_account_creation=len([item for item in items if item.state == CommerceReadinessState.needs_account_creation]),
        approval_needed=len(approvals),
        investment_required=len([item for item in items if item.requires_inventory or item.investment_needed != "unknown"]),
        high_risk=len([item for item in items if item.risk == CommerceRiskLevel.high]),
        actual_revenue_usd=0,
        actual_sales_confirmed=False,
        margin_invented=False,
        payment_connected=False,
        store_created=False,
        inventory_purchased=False,
        external_connection_enabled=False,
        credentials_stored=False,
        next_steps=[
            "Separar meta e-commerce USD 10,000 de la meta global USD 6,000.",
            "Hacer research de mercado antes de elegir productos.",
            "Pedir CEO antes de inventario, proveedor, cuenta externa o pasarela.",
            "No declarar margen, venta ni producto ganador sin evidencia.",
        ],
        opportunities_snapshot=items[:8],
        generated_at=utc_now(),
    )


def get_amazon_readiness_status() -> AmazonReadinessStatus:
    items = list_amazon_opportunities()
    risks = list_amazon_risks()
    approvals = [item for item in items if needs_approval(item)]
    return AmazonReadinessStatus(
        opportunities=len(items),
        prepared=len([item for item in items if item.state == CommerceReadinessState.prepared]),
        unknown=len([item for item in items if item.state == CommerceReadinessState.unknown]),
        needs_market_research=len([item for item in items if item.state == CommerceReadinessState.needs_market_research]),
        needs_paid_tool=len([item for item in items if item.state == CommerceReadinessState.needs_paid_tool]),
        needs_account_creation=len([item for item in items if item.state == CommerceReadinessState.needs_account_creation]),
        risks=len(risks),
        approval_needed=len(approvals),
        amazon_seller_connected=False,
        paid_tool_connected=False,
        prohibited_scraping_enabled=False,
        real_products_declared_winners=False,
        real_sales_confirmed=False,
        real_margin_confirmed=False,
        external_connection_enabled=False,
        credentials_stored=False,
        next_steps=[
            "Usar SNIFF AMAZON / CHIEF AMAZON solo como radar preparado.",
            "No conectar Amazon Seller sin CEO y credenciales seguras.",
            "No usar scraping prohibido ni herramientas pagadas sin ROI.",
            "No declarar productos ganadores sin evidencia verificable.",
        ],
        opportunities_snapshot=items[:8],
        generated_at=utc_now(),
    )
