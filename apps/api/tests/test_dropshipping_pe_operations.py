from decimal import Decimal as D

import pytest

from app.services.dropshipping_pe_operations import Event, operation_status, simulate_order


def test_delivery_and_return():
    result = simulate_order([Event.confirm, Event.dispatch, Event.deliver,
                             Event.request_return, Event.resolve_return])
    assert result["state"] == "return_resolved"
    assert result["history"] == ["received", "confirmed", "dispatched", "delivered",
                                 "return_requested", "return_resolved"]
    assert result["mode"] == "simulation"
    assert not result["real_order_created"]
    assert not result["payment_processed"]


def test_rejected_and_cancelled():
    assert simulate_order([Event.confirm, Event.dispatch, Event.reject])["state"] == "rejected"
    assert simulate_order([Event.cancel])["state"] == "cancelled"


@pytest.mark.parametrize("events", [[Event.dispatch], [Event.deliver], [Event.cancel, Event.confirm],
                                    [Event.confirm, Event.confirm]])
def test_invalid_transitions(events):
    with pytest.raises(ValueError):
        simulate_order(events)


def test_status_never_claims_live():
    result = operation_status()
    assert not result["live_enabled"]
    assert result["real_revenue_pen"] is None
    assert len(result["launch_blockers"]) == 8
    assert all(p["connection"] == "not_connected" for p in result["providers"])
