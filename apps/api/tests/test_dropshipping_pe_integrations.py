import pytest
from pydantic import ValidationError
from app.services.dropshipping_pe_integrations import (
    integration_contract, assess_supplier, SupplierChecklist, REQUIREMENTS, OfferScenario, offer_scenario,
)


def test_contract_keeps_markets_separate_and_disabled():
    c = integration_contract()
    assert c["market"]["currency"] == "PEN"
    assert c["future_market"]["currency"] == "USD" and not c["future_market"]["enabled"]
    assert not c["real_adapter_implemented"] and not c["live_enabled"]
    assert all(not p["connected"] for p in c["providers"])


def test_empty_and_complete_checklist_not_authorization():
    p = SupplierChecklist(provider="Dropi")
    assert len(assess_supplier(p)["missing"]) == 10
    p = SupplierChecklist(provider="Proveedor local directo", declared=dict.fromkeys(REQUIREMENTS, True))
    r = assess_supplier(p)
    assert r["declarations_complete"] and not r["evidence_verified"] and not r["approved_for_sale"]


def test_reject_unknown_fields_and_secrets():
    with pytest.raises(ValidationError):
        SupplierChecklist(provider="Dropi", api_key="not-accepted")
    with pytest.raises(ValidationError):
        SupplierChecklist(provider="Dropi", declared={"identity_and_contract":"true"})
    with pytest.raises(ValueError):
        assess_supplier(SupplierChecklist(provider="Dropi", declared={"invented":True}))


def offer(**patch):
    return OfferScenario(**{**dict(price="89",supplier_cost="20",delivered_shipping="15",
        failed_shipping="10",advertising_per_order="12",delivery_rate=".8",
        payment_rate=".05",reserve_per_delivery="4"),**patch})


def test_offer_respects_both_targets_and_delivery_rate():
    r = offer_scenario(offer())
    assert r["contribution_per_delivery"] == "14.47"
    assert r["max_ad_spend_per_received_order"] == "11.57"
    assert not r["meets_both_targets"] and not r["budget_approved"]
    assert not r["repeat_purchase_credit_assumed"]


def test_impossible_before_ads():
    r = offer_scenario(offer(supplier_cost="100", advertising_per_order="0"))
    assert not r["target_possible_before_ads"] and r["max_ad_spend_per_received_order"] == "0.00"


def test_higher_margin_target_limits_acquisition():
    a = offer_scenario(offer(target_margin_rate=".15"))
    b = offer_scenario(offer(target_margin_rate=".30"))
    from decimal import Decimal
    assert Decimal(b["max_ad_spend_per_received_order"]) < Decimal(a["max_ad_spend_per_received_order"])


def test_reject_bad_rate():
    with pytest.raises(ValidationError): offer(delivery_rate="0")
