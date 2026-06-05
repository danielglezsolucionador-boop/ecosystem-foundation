from fastapi import APIRouter, HTTPException

from app.schemas.integration_apps import IntegrationAppDiscovery, IntegrationAppProfile
from app.schemas.integrations import IntegrationContract
from app.services.integration_apps import (
    discover_integration_app,
    get_integration_app_profile,
    list_integration_app_profiles,
)
from app.services.integrations import (
    get_integration_contract,
    list_integration_contracts,
)

router = APIRouter(prefix="/api/v1/integrations", tags=["integrations"])


@router.get("/contracts", response_model=list[IntegrationContract])
def read_integration_contracts() -> list[IntegrationContract]:
    return list(list_integration_contracts())


@router.get("/apps", response_model=list[IntegrationAppProfile])
def read_integration_app_profiles() -> list[IntegrationAppProfile]:
    return list(list_integration_app_profiles())


@router.get("/apps/{app_id}/discovery", response_model=IntegrationAppDiscovery)
def read_integration_app_discovery(app_id: str) -> IntegrationAppDiscovery:
    discovery = discover_integration_app(app_id)

    if discovery is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "integration_app_not_found",
                "app_id": app_id,
            },
        )

    return discovery


@router.get("/apps/{app_id}", response_model=IntegrationAppProfile)
def read_integration_app_profile(app_id: str) -> IntegrationAppProfile:
    profile = get_integration_app_profile(app_id)

    if profile is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "integration_app_not_found",
                "app_id": app_id,
            },
        )

    return profile


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
