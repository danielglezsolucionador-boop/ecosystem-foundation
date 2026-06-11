from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.real_world import RealWorldActionRequest, RealWorldConnection, RealWorldStatus
from app.services.auth import get_current_user, require_control_center_user
from app.services.real_world import (
    RealWorldError,
    get_connection,
    get_real_world_status,
    list_approval_needed,
    list_connections,
    list_risks,
    mark_connection_prepared,
    request_approval,
    request_ceo_definition,
)

router = APIRouter(
    prefix="/api/v1/real-world",
    tags=["real-world"],
    dependencies=[Depends(require_control_center_user)],
)

READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}
WRITE_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
}


def require_real_world_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "real_world_role_not_authorized", "role": user.role.value},
        )


def require_real_world_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "real_world_write_role_not_authorized", "role": user.role.value},
        )


def raise_real_world_error(error: RealWorldError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=RealWorldStatus)
def read_real_world_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldStatus:
    require_real_world_read(current_user)
    return get_real_world_status()


@router.get("/connections", response_model=list[RealWorldConnection])
def read_real_world_connections(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RealWorldConnection]:
    require_real_world_read(current_user)
    return list_connections()


@router.get("/connections/{connection_id}", response_model=RealWorldConnection)
def read_real_world_connection(
    connection_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldConnection:
    require_real_world_read(current_user)
    try:
        return get_connection(connection_id)
    except RealWorldError as error:
        raise_real_world_error(error)


@router.post("/connections/{connection_id}/mark-prepared", response_model=RealWorldConnection)
def mark_real_world_connection_prepared(
    connection_id: str,
    request: RealWorldActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldConnection:
    require_real_world_write(current_user)
    try:
        return mark_connection_prepared(connection_id, request or RealWorldActionRequest(), current_user)
    except RealWorldError as error:
        raise_real_world_error(error)


@router.post("/connections/{connection_id}/request-ceo-definition", response_model=RealWorldConnection)
def request_real_world_connection_ceo_definition(
    connection_id: str,
    request: RealWorldActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldConnection:
    require_real_world_write(current_user)
    try:
        return request_ceo_definition(connection_id, request or RealWorldActionRequest(), current_user)
    except RealWorldError as error:
        raise_real_world_error(error)


@router.post("/connections/{connection_id}/request-approval", response_model=RealWorldConnection)
def request_real_world_connection_approval(
    connection_id: str,
    request: RealWorldActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldConnection:
    require_real_world_write(current_user)
    try:
        return request_approval(connection_id, request or RealWorldActionRequest(), current_user)
    except RealWorldError as error:
        raise_real_world_error(error)


@router.get("/approval-needed", response_model=list[RealWorldConnection])
def read_real_world_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RealWorldConnection]:
    require_real_world_read(current_user)
    return list_approval_needed()


@router.get("/risks", response_model=list[RealWorldConnection])
def read_real_world_risks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RealWorldConnection]:
    require_real_world_read(current_user)
    return list_risks()
