"""Provider onboarding contract and economic guardrails. No network or secret access."""
from decimal import Decimal
from enum import StrEnum
from typing import Annotated
from pydantic import BaseModel, ConfigDict, Field

from app.services.dropshipping_pe_offline import UnitEconomics, money

D = Decimal


class ProviderName(StrEnum):
    dropi = "Dropi"
    aliclik = "Aliclik"
    easydrop = "Easydrop"
    direct = "Proveedor local directo"


# Explicitly human-reviewed requirements, not a verified supplier integration.
REQUIREMENTS = {
    "identity_and_contract": "Identidad legal, factura, condiciones comerciales",
    "sku_stock_and_price": "SKU exacto, stock fechado, costo y vigencia",
    "sample_and_packaging": "Muestra física, calidad, empaque y medidas",
    "dispatch_and_coverage": "Frecuencia de despacho, cobertura, transportista y plazo",
    "returns_and_warranty": "Rechazos, garantía, devolución y costos asociados",
    "cod_and_settlement": "Modalidades, comisiones y calendario de liquidación",
    "media_rights_and_claims": "Permisos de imágenes, videos y características verificadas",
    "authentication_and_scopes": "Contrato de autenticación, permisos mínimos y rotación",
    "event_contract": "Contrato de eventos, autenticación, duplicados y estados",
    "sandbox_and_reconciliation": "Ensayo de integración y conciliación comprobable",
}


class SupplierChecklist(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: ProviderName
    declared: dict[str, Annotated[bool, Field(strict=True)]] = Field(default_factory=dict, max_length=10)


def assess_supplier(payload: SupplierChecklist) -> dict:
    unknown = set(payload.declared) - REQUIREMENTS.keys()
    if unknown:
        raise ValueError("Unknown requirement")
    missing = [key for key in REQUIREMENTS if payload.declared.get(key) is not True]
    return {"mode": "simulation", "provider": payload.provider.value,
            "declared_count": len(REQUIREMENTS)-len(missing), "required_count": len(REQUIREMENTS),
            "missing": missing, "declarations_complete": not missing,
            "evidence_verified": False, "provider_contacted": False,
            "credentials_received": False, "approved_for_sale": False, "live_enabled": False}


def integration_contract() -> dict:
    return {"mode": "planning", "live_enabled": False,
            "requirements": REQUIREMENTS,
            "providers": [{"name": p.value, "contract_verified": False,
                           "connected": False, "credentials_configured": None} for p in ProviderName],
            "market": {"country": "PE", "currency": "PEN", "payment_candidates": ["COD", "prepaid"]},
            "future_market": {"country": "US", "currency": "USD", "enabled": False,
                              "payment_candidates": ["prepaid"], "separate_legal_and_cost_review": True},
            "credential_policy": {"store_in_repository": False, "browser_access": False,
                                  "accept_credentials_in_api": False,
                                  "production_secret_manager_verified": False},
            "persistence": {"current": "local_sqlite_demo", "production": "postgresql_proposed",
                            "production_migration_applied": False},
            "external_webhooks_enabled": False, "real_adapter_implemented": False}


Amount = Annotated[Decimal, Field(ge=0, le=1000000, max_digits=10, decimal_places=2)]
Rate = Annotated[Decimal, Field(ge=0, le=1, max_digits=5, decimal_places=4)]


class OfferScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    price: Annotated[Decimal, Field(gt=0, le=1000000, max_digits=10, decimal_places=2)]
    supplier_cost: Amount
    delivered_shipping: Amount
    failed_shipping: Amount
    advertising_per_order: Amount
    delivery_rate: Annotated[Decimal, Field(gt=0, le=1, max_digits=5, decimal_places=4)]
    payment_rate: Rate
    reserve_per_delivery: Amount
    vat_rate: Rate = D("0.18")
    target_per_delivery: Amount = D("15")
    target_margin_rate: Rate = D("0.15")


def offer_scenario(payload: OfferScenario) -> dict:
    data = payload.model_dump(exclude={"target_per_delivery","target_margin_rate"})
    economics = UnitEconomics(**data)
    q = economics.delivery_rate
    net = economics.price / (1 + economics.vat_rate)
    nonad = (economics.supplier_cost + economics.delivered_shipping
             + economics.failed_shipping * (1-q)/q
             + economics.price * economics.payment_rate + economics.reserve_per_delivery)
    target = max(payload.target_per_delivery, net * payload.target_margin_rate)
    cap = (net - nonad - target) * q
    contribution = net - nonad - economics.advertising_per_order/q
    # Conservative cap rounded down so the displayed budget cannot exceed it.
    from decimal import ROUND_FLOOR
    cap_display = max(D("0"), cap).quantize(D("0.01"), rounding=ROUND_FLOOR)
    return {"mode": "simulation", "currency": "PEN", "live_enabled": False,
            "contribution_per_delivery": str(money(contribution)),
            "contribution_margin_pct": str(money(contribution/net*100)),
            "target_per_delivery": str(money(target)),
            "max_ad_spend_per_received_order": str(cap_display),
            "target_possible_before_ads": cap >= 0,
            "meets_both_targets": contribution >= target,
            "repeat_purchase_credit_assumed": False,
            "budget_approved": False, "fixed_costs_and_income_tax_included": False}
