from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.cerebro import (
    CerebroDailyBrief,
    CerebroDecision,
    CerebroDecisionCreate,
    CerebroStatus,
    CerebroTask,
    CerebroTaskCreate,
    CerebroTaskStateUpdate,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.cerebro import (
    CerebroError,
    build_brief,
    create_cerebro_decision,
    create_cerebro_task,
    get_cerebro_status,
    list_cerebro_decisions,
    list_cerebro_tasks,
    update_cerebro_task_state,
)

router = APIRouter(
    prefix="/api/v1/cerebro",
    tags=["cerebro"],
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


def require_cerebro_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "cerebro_role_not_authorized", "role": user.role.value},
        )


def require_cerebro_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "cerebro_role_not_authorized", "role": user.role.value},
        )


def raise_cerebro_error(error: CerebroError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


@router.get("/status", response_model=CerebroStatus)
def read_cerebro_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroStatus:
    require_cerebro_read(current_user)
    return get_cerebro_status()


@router.get("/brief/morning", response_model=CerebroDailyBrief)
def read_morning_brief(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroDailyBrief:
    require_cerebro_read(current_user)
    return build_brief("morning")


@router.get("/brief/evening", response_model=CerebroDailyBrief)
def read_evening_brief(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroDailyBrief:
    require_cerebro_read(current_user)
    return build_brief("evening")


@router.get("/decisions", response_model=list[CerebroDecision])
def read_cerebro_decisions(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CerebroDecision]:
    require_cerebro_read(current_user)
    return list_cerebro_decisions()


@router.post(
    "/decisions",
    response_model=CerebroDecision,
    status_code=status.HTTP_201_CREATED,
)
def write_cerebro_decision(
    request: CerebroDecisionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroDecision:
    require_cerebro_write(current_user)
    return create_cerebro_decision(request, current_user)


@router.get("/tasks", response_model=list[CerebroTask])
def read_cerebro_tasks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CerebroTask]:
    require_cerebro_read(current_user)
    return list_cerebro_tasks()


@router.post(
    "/tasks",
    response_model=CerebroTask,
    status_code=status.HTTP_201_CREATED,
)
def write_cerebro_task(
    request: CerebroTaskCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroTask:
    require_cerebro_write(current_user)
    return create_cerebro_task(request, current_user)


@router.post("/tasks/{task_id}/state", response_model=CerebroTask)
def update_task_state(
    task_id: str,
    request: CerebroTaskStateUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroTask:
    require_cerebro_write(current_user)
    try:
        return update_cerebro_task_state(task_id, request, current_user)
    except CerebroError as error:
        raise_cerebro_error(error)
