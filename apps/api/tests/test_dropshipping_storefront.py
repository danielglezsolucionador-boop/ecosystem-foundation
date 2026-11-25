from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

from app.api.dropshipping_storefront import router

app = FastAPI()
app.include_router(router)
client = TestClient(app)
PREFIX = "/api/v1/dropshipping-demo"
LINE = {"product_id": "PE-019", "pack": 2, "quantity": 1}
CART = {"lines": [LINE], "region": "lima"}


def test_catalog_is_demo_only():
    data = client.get(PREFIX + "/catalog").json()
    assert len(data["items"]) == 3 and data["live_enabled"] is False
    assert all(not p["approved_for_sale"] and not p["stock_verified"] for p in data["items"])
    assert data["items"][1]["packs"][1]["price_cents"] == 16020


def test_quote_calculates_pack_and_shipping_server_side():
    data = client.post(PREFIX + "/quote", json=CART).json()
    assert data["subtotal_cents"] == 16020
    assert data["shipping_cents"] == 1200 and data["total_cents"] == 17220
    assert client.post(PREFIX + "/quote", json={**CART, "region": "provincia"}).json()["total_cents"] == 17820


@pytest.mark.parametrize("cart", [
    {**CART, "total_cents": 1}, {**CART, "lines": []},
    {**CART, "lines": [LINE, LINE]}, {**CART, "region": "invalid"},
    {**CART, "lines": [{**LINE, "quantity": -1}]},
    {**CART, "lines": [{**LINE, "quantity": True}]},
    {**CART, "lines": [{**LINE, "pack": 4}]},
    {**CART, "lines": [{**LINE, "product_id": "PE-999"}]},
    {**CART, "lines": [{**LINE, "price": 1}]},
    {**CART, "lines": [{**LINE, "pack": n, "quantity": 10} for n in (1, 2, 3)] +
                     [{"product_id": "PE-013", "pack": 1, "quantity": 1}]},
])
def test_invalid_carts_rejected(cart):
    assert client.post(PREFIX + "/quote", json=cart).status_code == 422


@pytest.mark.parametrize("payment", ["contra_entrega_demo", "anticipado_demo"])
def test_checkout_never_creates_real_side_effects(payment):
    result = client.post(PREFIX + "/checkout", json={**CART, "payment": payment,
                         "acknowledge_demo": True})
    assert result.status_code == 200
    data = result.json()
    assert data["status"] == "demo_completed" and data["total_cents"] == 17220
    assert all(data[key] is False for key in ("real_order_created", "payment_processed",
               "supplier_contacted", "personal_data_collected", "live_enabled"))


@pytest.mark.parametrize("patch", [{"acknowledge_demo": False}, {"acknowledge_demo": "true"},
                                   {"payment": "card"}, {"phone": "123"}, {"live": True}])
def test_checkout_rejects_live_or_personal_data(patch):
    data = {**CART, "payment": "contra_entrega_demo", "acknowledge_demo": True, **patch}
    assert client.post(PREFIX + "/checkout", json=data).status_code == 422
