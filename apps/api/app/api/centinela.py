from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.centinela import CentinelaStatus
from app.services.auth import get_current_user, require_control_center_user
from app.services.centinela import get_centinela_status

router = APIRouter(
    prefix="/api/v1/centinela",
    tags=["centinela"],
    dependencies=[Depends(require_control_center_user)],
)

READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}


def require_centinela_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "centinela_role_not_authorized", "role": user.role.value},
        )


@router.get("/status", response_model=CentinelaStatus)
def read_centinela_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CentinelaStatus:
    require_centinela_read(current_user)
    return get_centinela_status()
