from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.workday import (
    WorkdayAlert,
    WorkdayAlertEvaluateRequest,
    WorkdayCheckpoint,
    WorkdayPhase,
    WorkdayPriorityChange,
    WorkdayPriorityChangeCreate,
    WorkdayReport,
    WorkdaySession,
    WorkdayStartRequest,
    WorkdayStatus,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.workday import (
    WorkdayError,
    create_priority_change,
    evaluate_alert,
    generate_evening,
    generate_midday,
    generate_morning,
    get_checkpoint,
    get_workday_report,
    get_workday_status,
    list_alerts,
    list_priority_changes,
    start_workday,
)

router = APIRouter(
    prefix="/api/v1/workday",
    tags=["workday"],
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


def require_workday_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "workday_role_not_authorized", "role": user.role.value},
        )


def require_workday_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "workday_write_role_not_authorized", "role": user.role.value},
        )


def raise_workday_error(error: WorkdayError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=WorkdayStatus)
def read_workday_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayStatus:
    require_workday_read(current_user)
    return get_workday_status()


@router.post("/start", response_model=WorkdaySession, status_code=status.HTTP_201_CREATED)
def start_autonomous_workday(
    request: WorkdayStartRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdaySession:
    require_workday_write(current_user)
    return start_workday(request or WorkdayStartRequest(), current_user)


@router.get("/morning", response_model=WorkdayCheckpoint)
def read_workday_morning(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayCheckpoint:
    require_workday_read(current_user)
    return get_checkpoint(WorkdayPhase.morning, current_user)


@router.post("/morning/generate", response_model=WorkdayCheckpoint)
def generate_workday_morning(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayCheckpoint:
    require_workday_write(current_user)
    return generate_morning(current_user)


@router.get("/midday", response_model=WorkdayCheckpoint)
def read_workday_midday(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayCheckpoint:
    require_workday_read(current_user)
    return get_checkpoint(WorkdayPhase.midday, current_user)


@router.post("/midday/generate", response_model=WorkdayCheckpoint)
def generate_workday_midday(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayCheckpoint:
    require_workday_write(current_user)
    return generate_midday(current_user)


@router.get("/evening", response_model=WorkdayCheckpoint)
def read_workday_evening(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayCheckpoint:
    require_workday_read(current_user)
    return get_checkpoint(WorkdayPhase.evening, current_user)


@router.post("/evening/generate", response_model=WorkdayCheckpoint)
def generate_workday_evening(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayCheckpoint:
    require_workday_write(current_user)
    return generate_evening(current_user)


@router.get("/alerts", response_model=list[WorkdayAlert])
def read_workday_alerts(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[WorkdayAlert]:
    require_workday_read(current_user)
    return list_alerts()


@router.post("/alerts/evaluate", response_model=WorkdayAlert)
def evaluate_workday_alert(
    request: WorkdayAlertEvaluateRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayAlert:
    require_workday_write(current_user)
    return evaluate_alert(request, current_user)


@router.get("/priority-changes", response_model=list[WorkdayPriorityChange])
def read_workday_priority_changes(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[WorkdayPriorityChange]:
    require_workday_read(current_user)
    return list_priority_changes()


@router.post(
    "/priority-changes",
    response_model=WorkdayPriorityChange,
    status_code=status.HTTP_201_CREATED,
)
def write_workday_priority_change(
    request: WorkdayPriorityChangeCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayPriorityChange:
    require_workday_write(current_user)
    return create_priority_change(request, current_user)


@router.get("/report", response_model=WorkdayReport)
def read_workday_report(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> WorkdayReport:
    require_workday_read(current_user)
    return get_workday_report()
