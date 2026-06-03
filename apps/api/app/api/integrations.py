from fastapi import APIRouter, HTTPException

from app.schemas.integrations import IntegrationContract
from app.services.integrations import (
    get_integration_contract,
    list_integration_contracts,
)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/contracts", response_model=list[IntegrationContract])
def read_integration_contracts() -> list[IntegrationContract]:
    return list(list_integration_contracts())


@router.get("/contracts/{contract_id}", response_model=IntegrationContract)
def read_integration_contract(contract_id: str) -> IntegrationContract:
    contract = get_integration_contract(contract_id)

    if contract is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "contract_not_found",
                "contract_id": contract_id,
            },
        )

    return contract

