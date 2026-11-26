"""Offline candidate register and provider comparison; no live integrations."""
from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum

from app.services.dropshipping_pe_offline import UnitEconomics


class Provider(StrEnum):
    aliclik = "Aliclik"
    dropi = "Dropi"
    easydrop = "Easydrop"


# Prior research shortlist; entries are leads, not verified SKUs or offers.
CANDIDATES = (
    "Balanza digital recargable", "Liga ejercitadora Body Trimmer",
    "Libro electrónico educativo", "Soporte magnético", "Convertidor PowerCar 300 W",
    "Convertidor PowerCar 150 W", "Mini cooler portátil", "Wonder Master 22 en 1",
    "Magic BB 10 en 1", "Pack champú y sérum Batana", "Champú y sérum Batana",
    "Sellador automático al vacío", "Protector de silicona para automóvil",
    "Cubretablero de automóvil", "Lentes de luz azul", "Cinturón para mascotas",
    "Rasuradora para patas de mascotas", "Sanitario de pasto para perros",
    "Sello adhesivo inferior para puertas", "Tendedero de cuatro niveles",
    "Luz solar con sensor", "Freidora eléctrica 3,5 litros", "Utensilios de acero inoxidable",
    "Guirnalda solar multicolor", "Hidrolavadora inalámbrica", "Foco LED con ventilador",
    "Tabla de corte de acero inoxidable", "Rodillo quitapelos", "Mini sellador de bolsas",
    "Clips selladores de bolsas",
)
FINALISTS = {13, 19, 23}
HOLD = {5, 6, 10, 11, 15, 16, 22}


def catalog() -> list[dict]:
    return [
        {"id": f"PE-{i:03}", "name": name,
         "stage": "quote_candidate" if i in FINALISTS else "hold" if i in HOLD else "research",
         "evidence": "prior_research_unverified", "supplier_sku": None,
         "stock": None, "supplier_cost_pen": None, "approved_for_sale": False}
        for i, name in enumerate(CANDIDATES, 1)
    ]


@dataclass(frozen=True)
class MockQuote:
    provider: Provider
    economics: UnitEconomics

    def simulate(self) -> dict:
        margin = self.economics.contribution_per_delivery()
        return {"provider": self.provider.value, "mode": "simulation",
                "contribution_per_delivery_pen": str(margin),
                "meets_provisional_target": margin >= Decimal("15"),
                "stock_verified": False, "cost_verified": False,
                "supplier_contacted": False, "approved_for_sale": False}


def compare(candidate_id: str, quotes: list[MockQuote]) -> dict:
    candidate = next((item for item in catalog() if item["id"] == candidate_id), None)
    if candidate is None:
        raise ValueError("Unknown candidate")
    if not 1 <= len(quotes) <= len(Provider):
        raise ValueError("Supply between one and three hypothetical quotes")
    if len({q.provider for q in quotes}) != len(quotes):
        raise ValueError("Duplicate provider")
    common = {(q.economics.price, q.economics.advertising_per_order,
               q.economics.payment_rate, q.economics.reserve_per_delivery,
               q.economics.vat_rate) for q in quotes}
    if len(common) != 1:
        raise ValueError("Use common sale, advertising, commission, reserve and VAT assumptions")
    results = sorted((q.simulate() for q in quotes),
                     key=lambda row: (-Decimal(row["contribution_per_delivery_pen"]), row["provider"]))
    return {"candidate": candidate, "mode": "simulation", "currency": "PEN",
            "ranked_hypothetical_quotes": results, "live_enabled": False,
            "recommended_supplier": None}
