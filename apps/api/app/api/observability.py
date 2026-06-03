from fastapi import APIRouter

from app.schemas.observability import ObservabilityStatus
from app.services.observability import get_observability_status

router = APIRouter(prefix="/api/v1/observability", tags=["observability"])


@router.get("/status", response_model=ObservabilityStatus)
def read_observability_status() -> ObservabilityStatus:
    return get_observability_status()

