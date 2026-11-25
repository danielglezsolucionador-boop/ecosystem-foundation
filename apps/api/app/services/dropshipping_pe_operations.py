"""Stateless offline operations for dropshipping Peru; never dispatches orders."""
from enum import StrEnum

from app.services.dropshipping_pe_offline import LaunchEvidence


class Event(StrEnum):
    confirm = "confirm"
    cancel = "cancel"
    dispatch = "dispatch"
    deliver = "deliver"
    reject = "reject"
    request_return = "request_return"
    resolve_return = "resolve_return"


TRANSITIONS = {
    ("received", Event.confirm): "confirmed",
    ("received", Event.cancel): "cancelled",
    ("confirmed", Event.cancel): "cancelled",
    ("confirmed", Event.dispatch): "dispatched",
    ("dispatched", Event.deliver): "delivered",
    ("dispatched", Event.reject): "rejected",
    ("delivered", Event.request_return): "return_requested",
    ("return_requested", Event.resolve_return): "return_resolved",
}


def simulate_order(events: list[Event]) -> dict:
    state = "received"
    history = [state]
    for event in events:
        next_state = TRANSITIONS.get((state, event))
        if next_state is None:
            raise ValueError(f"Invalid transition: {state} -> {event}")
        state = next_state
        history.append(state)
    return {
        "mode": "simulation", "state": state, "history": history,
        "real_order_created": False, "payment_processed": False,
        "supplier_contacted": False,
    }


def operation_status() -> dict:
    return {
        "unit": "dropshipping-pe-001", "mode": "simulation",
        "currency": "PEN", "live_enabled": False, "real_sales_confirmed": False,
        "store_published": False, "real_revenue_pen": None,
        "launch_blockers": list(LaunchEvidence().blockers()),
        "providers": [
            {"name": name, "connection": "not_connected", "stock_verified": False}
            for name in ("Aliclik", "Dropi", "Easydrop")
        ],
        "capabilities": ["financial_scenario", "order_lifecycle_simulation"],
    }
