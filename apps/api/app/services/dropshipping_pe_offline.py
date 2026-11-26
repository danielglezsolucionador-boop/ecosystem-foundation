"""Offline unit economics and launch gates for Peru dropshipping.

No network, payments, credentials, or supplier orders are used here.
All amounts are PEN, net of recoverable input VAT when applicable.
"""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

D = Decimal
CENT = D("0.01")


def money(value: Decimal) -> Decimal:
    return value.quantize(CENT, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class UnitEconomics:
    price: Decimal
    supplier_cost: Decimal
    delivered_shipping: Decimal
    failed_shipping: Decimal
    advertising_per_order: Decimal
    delivery_rate: Decimal
    payment_rate: Decimal
    reserve_per_delivery: Decimal
    vat_rate: Decimal = D("0.18")

    def __post_init__(self) -> None:
        for value in vars(self).values():
            if not isinstance(value, Decimal) or not value.is_finite() or value < 0:
                raise ValueError("Use finite nonnegative Decimal inputs")
        if not D("0") < self.delivery_rate <= D("1"):
            raise ValueError("Delivery rate must be greater than zero and at most one")
        if self.payment_rate > 1 or self.vat_rate > 1:
            raise ValueError("Invalid rate")

    def contribution_per_delivery(self) -> Decimal:
        """Expected contribution, allocating failed orders and ads to deliveries."""
        q = self.delivery_rate
        return money(
            self.price / (1 + self.vat_rate)
            - self.supplier_cost - self.delivered_shipping
            - self.failed_shipping * (1 - q) / q
            - self.advertising_per_order / q
            - self.price * self.payment_rate - self.reserve_per_delivery
        )


@dataclass(frozen=True)
class LaunchEvidence:
    supplier_stock_verified: bool = False
    supplier_cost_verified: bool = False
    shipping_and_returns_verified: bool = False
    sample_approved: bool = False
    store_test_passed: bool = False
    checkout_test_passed: bool = False
    legal_review_passed: bool = False
    owner_approved: bool = False

    def blockers(self) -> tuple[str, ...]:
        return tuple(name for name, value in vars(self).items() if value is not True)

    def ready_for_live(self, contribution: Decimal, target: Decimal = D("15")) -> bool:
        return (not self.blockers() and contribution.is_finite()
                and target.is_finite() and target > 0 and contribution >= target)
