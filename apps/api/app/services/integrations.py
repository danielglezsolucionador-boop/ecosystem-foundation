from functools import lru_cache
import json
from pathlib import Path

from app.schemas.integrations import IntegrationContract

CONTRACTS_PATH = Path(__file__).resolve().parents[1] / "data" / "integration_contracts.json"


@lru_cache
def list_integration_contracts() -> tuple[IntegrationContract, ...]:
    raw_contracts = json.loads(CONTRACTS_PATH.read_text(encoding="utf-8"))
    return tuple(IntegrationContract(**item) for item in raw_contracts)


def get_integration_contract(contract_id: str) -> IntegrationContract | None:
    normalized_id = contract_id.strip().lower()
    return next(
        (contract for contract in list_integration_contracts() if contract.id == normalized_id),
        None,
    )

