"""Offline COD replay. Provider event codes are invented test fixtures, not API contracts."""
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from app.api.dropshipping_storefront import Cart, quote


class Provider(StrEnum):
    dropi = "Dropi"
    aliclik = "Aliclik"
    easydrop = "Easydrop"


class Stage(StrEnum):
    confirmed = "confirmed"
    dispatched = "dispatched"
    delivered = "delivered"
    rejected = "rejected"
    returned = "returned"
    cancelled = "cancelled"


# Synthetic codes, intentionally prefixed DEMO. No provider is contacted.
CODES = {p: {f"DEMO_{p.value.upper()}_{s.value.upper()}": s for s in Stage}
         for p in Provider}
TRANSITIONS = {
    "received": {Stage.confirmed, Stage.cancelled},
    "confirmed": {Stage.dispatched, Stage.cancelled},
    "dispatched": {Stage.delivered, Stage.rejected},
    "delivered": {Stage.returned},
}
Cents = Annotated[int, Field(strict=True, ge=0, le=100000000)]


class MockEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: str = Field(pattern=r"^DEMO-[0-9]{1,6}$")
    code: str = Field(min_length=1, max_length=64)


class PipelineScenario(BaseModel):
    model_config = ConfigDict(extra="forbid")
    provider: Provider
    cart: Cart
    events: list[MockEvent] = Field(default_factory=list, max_length=30)
    product_cost_cents: Cents
    logistics_cost_cents: Cents
    advertising_cost_cents: Cents
    provider_fee_cents: Cents
    observed_remittance_cents: Cents


def simulate_pipeline(scenario: PipelineScenario) -> dict:
    order = quote(scenario.cart)
    state = "received"
    seen = {}
    history = [state]
    duplicates = 0
    for event in scenario.events:
        if event.event_id in seen:
            if seen[event.event_id] != event.code:
                raise ValueError("Event ID conflict")
            duplicates += 1
            continue
        stage = CODES[scenario.provider].get(event.code)
        if stage is None or stage not in TRANSITIONS.get(state, set()):
            raise ValueError("Unknown code or invalid transition")
        seen[event.event_id] = event.code
        state = stage.value
        history.append(state)
    # COD only: a returned order assumes a complete refund. All costs are
    # user-entered incurred costs, including nonrecoverable failed-order costs.
    closed = state in {"delivered", "rejected", "returned", "cancelled"}
    gross = order["total_cents"] if state == "delivered" else 0
    expected = max(0, gross - scenario.provider_fee_cents) if closed else None
    observed = scenario.observed_remittance_cents
    costs = (scenario.product_cost_cents + scenario.logistics_cost_cents
             + scenario.advertising_cost_cents + scenario.provider_fee_cents)
    return {"mode": "simulation", "provider": scenario.provider.value,
            "state": state, "history": history, "duplicates_ignored": duplicates,
            "gross_cod_cents": gross if closed else None,
            "expected_remittance_cents": expected,
            "observed_remittance_cents": observed,
            "remittance_difference_cents": observed - expected if closed else None,
            "reconciliation": ("pending" if not closed else "matched" if observed == expected else "review"),
            "gross_cash_contribution_cents": gross - costs if closed else None,
            "taxes_included_in_contribution": False,
            "live_enabled": False, "supplier_contacted": False,
            "payment_processed": False, "real_order_created": False,
            "deduplication_scope": "single_replay_only"}


def pipeline_contract() -> dict:
    return {"mode": "simulation", "live_enabled": False,
            "providers": [{"name": p.value, "codes": {s.value: k for k, s in CODES[p].items()},
                           "real_contract_verified": False} for p in Provider],
            "evidence_required": ["supplier SKU and available stock", "tax-valid cost",
                                  "delivery and return terms", "approved physical sample",
                                  "live integration authentication", "owner approval"],
            "persistent_idempotency": False, "external_webhooks_enabled": False}
