from fastapi import APIRouter

from app.schemas.control_center import ControlCenterOverview
from app.services.control_center import get_control_center_overview

router = APIRouter(prefix="/api/v1/control-center", tags=["control-center"])


@router.get("/overview", response_model=ControlCenterOverview)
def get_overview() -> ControlCenterOverview:
    return get_control_center_overview()

