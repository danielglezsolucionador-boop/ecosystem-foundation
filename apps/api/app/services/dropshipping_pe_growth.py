"""Offline marketing plans and closed-cohort campaign evaluation."""
from decimal import Decimal, ROUND_HALF_UP
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

PRODUCT_ANGLES = {
    "PE-013": ("automóvil", "Revisa los puntos de contacto de la puerta", "Comprueba medidas y compatibilidad", "Muestra la instalación solo con una muestra aprobada"),
    "PE-019": ("hogar", "Observa el espacio bajo la puerta", "Mide la separación antes de elegir", "Demuestra el ajuste con una muestra aprobada"),
    "PE-023": ("cocina", "Revisa cómo organizas tus utensilios", "Comprueba dimensiones y materiales", "Muestra el uso real solo tras verificar la muestra"),
}


def creative_plan(candidate: str, platform: str) -> dict:
    if candidate not in PRODUCT_ANGLES or platform not in {"facebook", "instagram", "tiktok"}:
        raise ValueError("Unknown candidate or platform")
    niche, problem, comparison, demo = PRODUCT_ANGLES[candidate]
    scripts = []
    for angle, hook in [("problem", problem), ("comparison", comparison), ("demonstration", demo)]:
        scripts.append({"angle": angle, "duration_seconds": 25, "shots": [
            {"seconds": "0-4", "text": hook},
            {"seconds": "4-12", "text": "Grabar la situación real sin exagerar resultados."},
            {"seconds": "12-20", "text": "Mostrar características verificadas de la muestra; pendiente de aprobación."},
            {"seconds": "20-25", "text": "Consulta características y disponibilidad antes de comprar."}],
            "format": "9:16", "approved_for_publication": False})
    return {"candidate": candidate, "platform": platform, "niche": niche, "scripts": scripts,
            "handoff": {"MARKETING": "review strategy", "PLUMA": "review copy", "LENTE": "produce after sample approval"},
            "mode": "draft", "published": False, "llm_called": False, "live_enabled": False}


class CreativeChecklist(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    sample_verified: bool = False
    claims_verified: bool = False
    price_verified: bool = False
    media_rights_verified: bool = False
    policy_reviewed: bool = False
    clear_hook: bool = False
    clear_cta: bool = False
    mobile_readable: bool = False


def evaluate_creative(check: CreativeChecklist) -> dict:
    values = check.model_dump()
    blockers = [key for key in ("sample_verified", "claims_verified", "price_verified", "media_rights_verified", "policy_reviewed") if not values[key]]
    return {"score": sum(values.values()), "max_score": len(values), "blockers": blockers,
            "review_ready": not blockers and all(values.values()), "approved_for_publication": False,
            "mode": "simulation", "live_enabled": False}


Cents = Annotated[int, Field(strict=True, ge=0, le=100000000)]
Count = Annotated[int, Field(strict=True, ge=0, le=1000000)]


class CampaignScenario(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    spend_cents: Cents
    budget_cap_cents: Annotated[int, Field(strict=True, gt=0, le=100000000)]
    orders: Count
    delivered_paid: Count
    failed_or_refunded: Count
    pending: Count
    net_sales_ex_vat_cents: Cents
    non_ad_costs_cents: Cents
    target_contribution_per_delivery_cents: Cents = 1500
    min_deliveries: Annotated[int, Field(strict=True, ge=1, le=1000000)] = 10

    @model_validator(mode="after")
    def consistent(self):
        if self.delivered_paid + self.failed_or_refunded + self.pending != self.orders:
            raise ValueError("Order counts must reconcile")
        if not self.delivered_paid and self.net_sales_ex_vat_cents:
            raise ValueError("Net sales require delivered and paid orders")
        return self


def ratio(n, d):
    return str((Decimal(n) / Decimal(d)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)) if d else None


def evaluate_campaign(s: CampaignScenario) -> dict:
    contribution = s.net_sales_ex_vat_cents - s.non_ad_costs_cents - s.spend_cents
    if s.spend_cents >= s.budget_cap_cents:
        decision = "pause_budget_cap"
    elif s.pending:
        decision = "wait_for_settlement"
    elif s.delivered_paid < s.min_deliveries:
        decision = "insufficient_sample"
    elif contribution < 0:
        decision = "pause_loss"
    elif contribution < s.target_contribution_per_delivery_cents * s.delivered_paid:
        decision = "revise_campaign"
    else:
        decision = "review_scaling_with_ceo"
    return {"mode": "simulation", "decision": decision, "live_enabled": False,
            "spend_executed": False, "campaign_changed": False, "ceo_approval_required": True,
            "contribution_cents": contribution, "cohort_closed": s.pending == 0,
            "cpa_order_pen": ratio(s.spend_cents, s.orders * 100),
            "cpa_delivered_pen": ratio(s.spend_cents, s.delivered_paid * 100),
            "net_sales_roas": ratio(s.net_sales_ex_vat_cents, s.spend_cents),
            "contribution_per_delivery_pen": ratio(contribution, s.delivered_paid * 100) if not s.pending else None,
            "delivery_rate_pct": ratio(s.delivered_paid * 100, s.orders) if not s.pending else None,
            "budget_remaining_cents": max(0, s.budget_cap_cents - s.spend_cents)}
