from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.missions import (
    MissionDailyReport,
    MissionLoopAssignRequest,
    MissionLoopAuditRequest,
    MissionLoopBlockRequest,
    MissionLoopCompleteRequest,
    MissionLoopCreate,
    MissionLoopDispatchRequest,
    MissionLoopForjaRequest,
    MissionLoopMission,
    MissionLoopPlanRequest,
    MissionLoopUpdateRequest,
    MissionTimeline,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.cerebro import CerebroError
from app.services.missions import (
    active_loop_missions,
    assign_loop_mission,
    block_loop_mission,
    complete_loop_mission,
    create_loop_mission,
    dispatch_loop_mission,
    get_loop_mission,
    get_mission_daily_report,
    list_loop_missions,
    mission_timeline,
    plan_loop_mission,
    request_loop_audit,
    send_loop_to_forja,
    update_loop_mission,
)

router = APIRouter(
    prefix="/api/v1/missions",
    tags=["missions"],
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


def require_mission_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "mission_role_not_authorized", "role": user.role.value},
        )


def require_mission_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "mission_write_role_not_authorized", "role": user.role.value},
        )


def raise_mission_error(error: CerebroError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/active", response_model=list[MissionLoopMission])
def read_active_missions(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[MissionLoopMission]:
    require_mission_read(current_user)
    return active_loop_missions()


@router.get("/reports/daily", response_model=MissionDailyReport)
def read_mission_daily_report(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionDailyReport:
    require_mission_read(current_user)
    return get_mission_daily_report()


@router.get("", response_model=list[MissionLoopMission])
@router.get("/", response_model=list[MissionLoopMission])
def read_missions(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[MissionLoopMission]:
    require_mission_read(current_user)
    return list_loop_missions()


@router.post("", response_model=MissionLoopMission, status_code=status.HTTP_201_CREATED)
@router.post("/", response_model=MissionLoopMission, status_code=status.HTTP_201_CREATED)
def write_mission(
    request: MissionLoopCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    return create_loop_mission(request, current_user)


@router.get("/{mission_id}", response_model=MissionLoopMission)
def read_mission(
    mission_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_read(current_user)
    try:
        return get_loop_mission(mission_id)
    except CerebroError as error:
        raise_mission_error(error)


@router.post("/{mission_id}/plan", response_model=MissionLoopMission)
def plan_mission(
    mission_id: str,
    request: MissionLoopPlanRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    try:
        return plan_loop_mission(mission_id, request or MissionLoopPlanRequest(), current_user)
    except CerebroError as error:
        raise_mission_error(error)


@router.post("/{mission_id}/assign", response_model=MissionLoopMission)
def assign_mission(
    mission_id: str,
    request: MissionLoopAssignRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    try:
        return assign_loop_mission(mission_id, request, current_user)
    except CerebroError as error:
        raise_mission_error(error)


@router.post("/{mission_id}/dispatch", response_model=MissionLoopMission)
def dispatch_mission(
    mission_id: str,
    request: MissionLoopDispatchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    try:
        return dispatch_loop_mission(mission_id, request, current_user)
    except CerebroError as error:
        raise_mission_error(error)


@router.post("/{mission_id}/request-audit", response_model=MissionLoopMission)
def request_mission_audit(
    mission_id: str,
    request: MissionLoopAuditRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    try:
        return request_loop_audit(mission_id, request or MissionLoopAuditRequest(), current_user)
    except CerebroError as error:
        raise_mission_error(error)


@router.post("/{mission_id}/send-to-forja", response_model=MissionLoopMission)
def send_mission_to_forja(
    mission_id: str,
    request: MissionLoopForjaRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    try:
        return send_loop_to_forja(mission_id, request, current_user)
    except CerebroError as error:
        raise_mission_error(error)


@router.post("/{mission_id}/update", response_model=MissionLoopMission)
def update_mission(
    mission_id: str,
    request: MissionLoopUpdateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    try:
        return update_loop_mission(mission_id, request, current_user)
    except CerebroError as error:
        raise_mission_error(error)


@router.post("/{mission_id}/complete", response_model=MissionLoopMission)
def complete_mission(
    mission_id: str,
    request: MissionLoopCompleteRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    try:
        return complete_loop_mission(mission_id, request, current_user)
    except CerebroError as error:
        raise_mission_error(error)


@router.post("/{mission_id}/block", response_model=MissionLoopMission)
def block_mission(
    mission_id: str,
    request: MissionLoopBlockRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionLoopMission:
    require_mission_write(current_user)
    try:
        return block_loop_mission(mission_id, request, current_user)
    except CerebroError as error:
        raise_mission_error(error)


@router.get("/{mission_id}/timeline", response_model=MissionTimeline)
def read_mission_timeline(
    mission_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> MissionTimeline:
    require_mission_read(current_user)
    try:
        return mission_timeline(mission_id)
    except CerebroError as error:
        raise_mission_error(error)
