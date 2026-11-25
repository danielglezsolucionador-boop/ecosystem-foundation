"""Public demonstration endpoints: no provider, customer, payment or order writes."""
from enum import StrEnum
from typing import Annotated

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field

router = APIRouter(prefix="/api/v1/dropshipping-demo", tags=["dropshipping-demo"])

PRODUCTS = {
    "PE-013": ("Protector de silicona para automóvil", "Auto", 7900),
    "PE-019": ("Sello inferior para puertas", "Hogar", 8900),
    "PE-023": ("Utensilios de cocina", "Cocina", 9990),
}
DISCOUNTS = {1: 0, 2: 10, 3: 15}


class Region(StrEnum):
    lima = "lima"
    provincia = "provincia"


class Payment(StrEnum):
    cod = "contra_entrega_demo"
    prepaid = "anticipado_demo"


class Line(BaseModel):
    model_config = ConfigDict(extra="forbid")
    product_id: str = Field(pattern=r"^PE-[0-9]{3}$")
    pack: Annotated[int, Field(strict=True, ge=1, le=3)]
    quantity: Annotated[int, Field(strict=True, ge=1, le=10)]


class Cart(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lines: list[Line] = Field(min_length=1, max_length=9)
    region: Region


class Checkout(Cart):
    payment: Payment
    acknowledge_demo: Annotated[bool, Field(strict=True)]


def pack_price(base: int, pack: int) -> int:
    # Integer centimos with round-half-up, never trust browser amounts.
    return (base * pack * (100 - DISCOUNTS[pack]) + 50) // 100


def quote(cart: Cart) -> dict:
    seen = set()
    lines = []
    if sum(line.quantity for line in cart.lines) > 30:
        raise ValueError("Máximo 30 paquetes por simulación")
    for line in cart.lines:
        key = (line.product_id, line.pack)
        if key in seen or line.product_id not in PRODUCTS:
            raise ValueError("Producto desconocido o línea duplicada")
        seen.add(key)
        name, _, base = PRODUCTS[line.product_id]
        unit = pack_price(base, line.pack)
        lines.append({"product_id": line.product_id, "name": name,
                      "pack": line.pack, "quantity": line.quantity,
                      "pack_price_cents": unit, "line_total_cents": unit * line.quantity})
    subtotal = sum(line["line_total_cents"] for line in lines)
    shipping = 1200 if cart.region == Region.lima else 1800
    return {"mode": "simulation", "currency": "PEN", "lines": lines,
            "subtotal_cents": subtotal, "shipping_cents": shipping,
            "total_cents": subtotal + shipping, "live_enabled": False,
            "stock_verified": False, "prices_verified": False}


@router.get("/catalog")
def read_catalog() -> dict:
    return {"mode": "simulation", "brand": "NEXORA / concepto", "currency": "PEN",
            "live_enabled": False, "items": [
                {"id": key, "name": name, "category": category,
                 "packs": [{"units": n, "price_cents": pack_price(base, n),
                            "discount_pct": DISCOUNTS[n]} for n in DISCOUNTS],
                 "approved_for_sale": False, "stock_verified": False}
                for key, (name, category, base) in PRODUCTS.items()]}


@router.post("/quote")
def read_quote(cart: Cart) -> dict:
    try:
        return quote(cart)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.post("/checkout")
def simulate_checkout(cart: Checkout) -> dict:
    if not cart.acknowledge_demo:
        raise HTTPException(status_code=422, detail="Confirma que es una simulación")
    result = read_quote(cart)
    return {**result, "payment": cart.payment.value, "status": "demo_completed",
            "real_order_created": False, "payment_processed": False,
            "supplier_contacted": False, "personal_data_collected": False}
