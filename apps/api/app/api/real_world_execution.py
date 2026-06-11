from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.real_world_execution import (
    RealWorldExecutionActionRequest,
    RealWorldExecutionQueueCreate,
    RealWorldExecutionQueueItem,
    RealWorldExecutionStatus,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.real_world_execution import (
    RealWorldExecutionError,
    block_item,
    create_queue_item,
    get_execution_status,
    list_approval_needed,
    list_execution_queue,
    mark_prepared,
    request_approval,
)

router = APIRouter(
    prefix="/api/v1/real-world-execution",
    tags=["real-world-execution"],
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


def require_execution_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "real_world_execution_role_not_authorized", "role": user.role.value},
        )


def require_execution_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "real_world_execution_write_role_not_authorized", "role": user.role.value},
        )


def raise_execution_error(error: RealWorldExecutionError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=RealWorldExecutionStatus)
def read_real_world_execution_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldExecutionStatus:
    require_execution_read(current_user)
    return get_execution_status()


@router.get("/queue", response_model=list[RealWorldExecutionQueueItem])
def read_real_world_execution_queue(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RealWorldExecutionQueueItem]:
    require_execution_read(current_user)
    return list_execution_queue()


@router.get("/approval-needed", response_model=list[RealWorldExecutionQueueItem])
def read_real_world_execution_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RealWorldExecutionQueueItem]:
    require_execution_read(current_user)
    return list_approval_needed()


@router.post("/queue", response_model=RealWorldExecutionQueueItem)
def create_real_world_execution_queue_item(
    request: RealWorldExecutionQueueCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldExecutionQueueItem:
    require_execution_write(current_user)
    try:
        return create_queue_item(request, current_user)
    except RealWorldExecutionError as error:
        raise_execution_error(error)


@router.post("/queue/{item_id}/mark-prepared", response_model=RealWorldExecutionQueueItem)
def mark_real_world_execution_prepared(
    item_id: str,
    request: RealWorldExecutionActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldExecutionQueueItem:
    require_execution_write(current_user)
    try:
        return mark_prepared(item_id, request or RealWorldExecutionActionRequest(), current_user)
    except RealWorldExecutionError as error:
        raise_execution_error(error)


@router.post("/queue/{item_id}/request-approval", response_model=RealWorldExecutionQueueItem)
def request_real_world_execution_approval(
    item_id: str,
    request: RealWorldExecutionActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldExecutionQueueItem:
    require_execution_write(current_user)
    try:
        return request_approval(item_id, request or RealWorldExecutionActionRequest(), current_user)
    except RealWorldExecutionError as error:
        raise_execution_error(error)


@router.post("/queue/{item_id}/block", response_model=RealWorldExecutionQueueItem)
def block_real_world_execution_queue_item(
    item_id: str,
    request: RealWorldExecutionActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RealWorldExecutionQueueItem:
    require_execution_write(current_user)
    try:
        return block_item(item_id, request or RealWorldExecutionActionRequest(), current_user)
    except RealWorldExecutionError as error:
        raise_execution_error(error)
