from fastapi import APIRouter

from app.schemas.platform import PlatformStatus
from app.services.platform import get_platform_status

router = APIRouter(prefix="/api/v1/platform", tags=["platform"])


@router.get("/status", response_model=PlatformStatus)
def read_platform_status() -> PlatformStatus:
    return get_platform_status()

