from fastapi import APIRouter, HTTPException

from app.schemas.app_registry import EcosystemApp
from app.services.app_registry import get_registered_app, list_registered_apps

router = APIRouter(prefix="/api/v1", tags=["app-registry"])


@router.get("/apps", response_model=list[EcosystemApp])
def get_apps() -> list[EcosystemApp]:
    return list(list_registered_apps())


@router.get("/apps/{app_id}", response_model=EcosystemApp)
def get_app(app_id: str) -> EcosystemApp:
    app = get_registered_app(app_id)

    if app is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "app_not_found",
                "app_id": app_id,
            },
        )

    return app
