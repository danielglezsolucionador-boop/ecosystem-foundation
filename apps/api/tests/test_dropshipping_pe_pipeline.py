import pytest
from pydantic import ValidationError

from app.services.dropshipping_pe_pipeline import PipelineScenario, pipeline_contract, simulate_pipeline


def scenario(provider="Dropi", states=("confirmed", "dispatched", "delivered"), **overrides):
    payload = dict(provider=provider,
                   cart={"lines": [{"product_id": "PE-019", "pack": 1, "quantity": 1}], "region": "lima"},
                   events=[{"event_id": f"DEMO-{i}", "code": f"DEMO_{provider.upper()}_{s.upper()}"}
                           for i, s in enumerate(states, 1)],
                   product_cost_cents=2000, logistics_cost_cents=1500,
                   advertising_cost_cents=1200, provider_fee_cents=500,
                   observed_remittance_cents=9600)
    return PipelineScenario.model_validate({**payload, **overrides})


@pytest.mark.parametrize("provider", ["Dropi", "Aliclik", "Easydrop"])
def test_delivered_reconciliation(provider):
    result = simulate_pipeline(scenario(provider))
    assert result["gross_cod_cents"] == 10100
    assert result["expected_remittance_cents"] == 9600
    assert result["gross_cash_contribution_cents"] == 4900
    assert result["reconciliation"] == "matched"
    assert not result["real_order_created"] and not result["supplier_contacted"]


def test_reconciliation_difference():
    result = simulate_pipeline(scenario(observed_remittance_cents=9000))
    assert result["remittance_difference_cents"] == -600
    assert result["reconciliation"] == "review"


@pytest.mark.parametrize("states", [("confirmed", "dispatched", "rejected"),
                                    ("confirmed", "dispatched", "delivered", "returned"),
                                    ("cancelled",)])
def test_closed_no_cod_revenue(states):
    result = simulate_pipeline(scenario(states=states, observed_remittance_cents=0))
    assert result["expected_remittance_cents"] == 0
    assert result["gross_cash_contribution_cents"] == -5200


def test_pending_not_reconciled():
    result = simulate_pipeline(scenario(states=("confirmed",)))
    assert result["reconciliation"] == "pending"
    assert result["gross_cash_contribution_cents"] is None


def test_identical_replayed_event_is_ignored():
    s = scenario()
    s.events.insert(1, s.events[0])
    result = simulate_pipeline(s)
    assert result["duplicates_ignored"] == 1
    assert result["history"] == ["received", "confirmed", "dispatched", "delivered"]


def test_conflicting_duplicate_rejected():
    s = scenario()
    s.events[1].event_id = s.events[0].event_id
    with pytest.raises(ValueError, match="conflict"):
        simulate_pipeline(s)


@pytest.mark.parametrize("states", [("delivered",), ("confirmed", "returned"), ("confirmed", "confirmed")])
def test_invalid_transitions(states):
    with pytest.raises(ValueError):
        simulate_pipeline(scenario(states=states))


def test_other_provider_code_rejected():
    s = scenario()
    s.events[0].code = "DEMO_ALICLIK_CONFIRMED"
    with pytest.raises(ValueError):
        simulate_pipeline(s)


@pytest.mark.parametrize("overrides", [{"live": True}, {"phone": "123"},
                                        {"product_cost_cents": -1}, {"provider_fee_cents": True}])
def test_forbidden_inputs(overrides):
    with pytest.raises(ValidationError):
        scenario(**overrides)


def test_contract_is_mock_only():
    result = pipeline_contract()
    assert not result["live_enabled"] and not result["persistent_idempotency"]
    assert all(not p["real_contract_verified"] for p in result["providers"])
