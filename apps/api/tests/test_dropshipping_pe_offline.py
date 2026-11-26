from decimal import Decimal as D

import pytest

from app.services.dropshipping_pe_offline import LaunchEvidence, UnitEconomics


def scenario(**overrides):
    args = dict(price=D("89"), supplier_cost=D("20"),
                delivered_shipping=D("15"), failed_shipping=D("10"),
                advertising_per_order=D("12"), delivery_rate=D("0.8"),
                payment_rate=D("0.05"), reserve_per_delivery=D("4"))
    args.update(overrides)
    return UnitEconomics(**args)


def test_cost_of_failed_deliveries_is_included():
    assert scenario().contribution_per_delivery() == D("14.47")
    assert scenario(delivery_rate=D("1")).contribution_per_delivery() == D("19.97")


def test_invalid_delivery_rate_fails_closed():
    with pytest.raises(ValueError):
        scenario(delivery_rate=D("0"))


def test_default_launch_is_blocked():
    assert len(LaunchEvidence().blockers()) == 8
    assert not LaunchEvidence().ready_for_live(D("100"))


def test_live_requires_evidence_and_margin():
    evidence = LaunchEvidence(**dict.fromkeys(vars(LaunchEvidence()), True))
    assert not evidence.ready_for_live(D("14.99"))
    assert evidence.ready_for_live(D("15"))
