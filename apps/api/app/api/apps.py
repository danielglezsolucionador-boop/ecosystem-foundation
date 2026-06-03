from fastapi import APIRouter

from app.schemas.app_registry import EcosystemApp
from app.services.app_registry import list_registered_apps

router = APIRouter(prefix="/api/v1", tags=["app-registry"])


@router.get("/apps", response_model=list[EcosystemApp])
def get_apps() -> list[EcosystemApp]:
    return list(list_registered_apps())

