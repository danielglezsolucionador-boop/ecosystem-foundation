from dataclasses import replace
from decimal import Decimal as D

import pytest

from app.services.dropshipping_pe_catalog import MockQuote, Provider, catalog, compare
from app.services.dropshipping_pe_offline import UnitEconomics


def economics():
    return UnitEconomics(D("89"), D("20"), D("15"), D("10"), D("12"),
                         D("0.8"), D("0.05"), D("4"))


def test_catalog_has_unique_unverified_candidates():
    rows = catalog()
    assert len(rows) == len({r["id"] for r in rows}) == 30
    assert sum(r["stage"] == "quote_candidate" for r in rows) == 3
    assert all(r["stock"] is None and r["supplier_cost_pen"] is None
               and not r["approved_for_sale"] for r in rows)


def test_ranking_accounts_for_delivery_failure():
    a = MockQuote(Provider.aliclik, economics())
    b = MockQuote(Provider.dropi, replace(economics(), supplier_cost=D("17"), delivery_rate=D("0.5")))
    result = compare("PE-019", [b, a])
    rows = result["ranked_hypothetical_quotes"]
    assert rows[0]["provider"] == "Aliclik"
    assert rows[0]["contribution_per_delivery_pen"] == "14.47"
    assert not rows[0]["meets_provisional_target"]
    assert result["recommended_supplier"] is None and not result["live_enabled"]
    assert all(not r["cost_verified"] and not r["approved_for_sale"] for r in rows)


@pytest.mark.parametrize("candidate,quotes", [("unknown", [MockQuote(Provider.dropi, economics())]),
                                             ("PE-019", []),
                                             ("PE-019", [MockQuote(Provider.dropi, economics())]*2)])
def test_invalid_comparison(candidate, quotes):
    with pytest.raises(ValueError):
        compare(candidate, quotes)


def test_inconsistent_sale_price_rejected():
    with pytest.raises(ValueError):
        compare("PE-019", [MockQuote(Provider.dropi, economics()),
                           MockQuote(Provider.aliclik, replace(economics(), price=D("99")))])
