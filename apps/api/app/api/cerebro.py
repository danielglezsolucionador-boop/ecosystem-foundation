from fastapi import APIRouter, Depends, Header, HTTPException, Request, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.cerebro import (
    CerebroAlert,
    CerebroAlertCreate,
    CerebroApprovalActionRequest,
    CerebroApprovalRequest,
    CerebroApprovalRequestCreate,
    CerebroChatRequest,
    CerebroChatResponse,
    CerebroCheckpoint,
    CerebroChiefOfStaffStatus,
    CerebroCompanyGoal,
    CerebroCompanyGoalCreate,
    CerebroDailyBrief,
    CerebroDecision,
    CerebroDecisionCreate,
    CerebroDepartmentGoal,
    CerebroDepartmentGoalCreate,
    CerebroMission,
    CerebroMissionCreate,
    CerebroMissionDispatchRequest,
    CerebroMissionUpdateCreate,
    CerebroRevenueOpportunity,
    CerebroRevenueOpportunityCreate,
    CerebroStatus,
    CerebroTask,
    CerebroTaskCreate,
    CerebroTaskStateUpdate,
    SombraInboxMessageCreate,
    SombraInboxMessageResponse,
    SombraInboxRecentMessage,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.cerebro import (
    CerebroError,
    add_mission_update,
    build_brief,
    build_checkpoint,
    create_alert,
    create_approval_request,
    create_cerebro_decision,
    create_cerebro_task,
    create_company_goal,
    create_department_goal,
    create_mission,
    create_revenue_opportunity,
    dispatch_mission,
    get_cerebro_status,
    get_chief_of_staff_status,
    get_mission,
    list_sombra_inbox_messages,
    list_alerts,
    list_approval_requests,
    list_cerebro_decisions,
    list_cerebro_tasks,
    list_company_goals,
    list_department_goals,
    list_missions,
    list_revenue_opportunities,
    receive_sombra_inbox_message,
    run_cerebro_chat,
    update_approval_request_status,
    update_cerebro_task_state,
)

router = APIRouter(
    prefix="/api/v1/cerebro",
    tags=["cerebro"],
    dependencies=[Depends(require_control_center_user)],
)
sombra_inbox_router = APIRouter(
    prefix="/api/v1/cerebro/inbox/sombra",
    tags=["cerebro"],
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
APPROVAL_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
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


def require_cerebro_approval(user: AuthenticatedUser) -> None:
    if user.role not in APPROVAL_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "cerebro_approval_role_not_authorized", "role": user.role.value},
        )


def raise_cerebro_error(error: CerebroError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail)


@sombra_inbox_router.post("", response_model=SombraInboxMessageResponse)
async def receive_sombra_message(
    message: SombraInboxMessageCreate,
    request: Request,
    authorization: str | None = Header(default=None),
    x_sombra_message_id: str | None = Header(default=None, alias="X-Sombra-Message-Id"),
    x_sombra_timestamp: str | None = Header(default=None, alias="X-Sombra-Timestamp"),
    x_sombra_signature: str | None = Header(default=None, alias="X-Sombra-Signature"),
) -> SombraInboxMessageResponse:
    raw_body = await request.body()
    try:
        return receive_sombra_inbox_message(
            message,
            authorization=authorization,
            header_message_id=x_sombra_message_id,
            header_timestamp=x_sombra_timestamp,
            signature=x_sombra_signature,
            raw_body=raw_body,
        )
    except CerebroError as error:
        raise_cerebro_error(error)


@router.get("/status", response_model=CerebroStatus)
def read_cerebro_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroStatus:
    require_cerebro_read(current_user)
    return get_cerebro_status()


@router.get("/chief-of-staff/status", response_model=CerebroChiefOfStaffStatus)
def read_chief_of_staff_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroChiefOfStaffStatus:
    require_cerebro_read(current_user)
    return get_chief_of_staff_status()


@router.post("/chat", response_model=CerebroChatResponse)
def write_cerebro_chat(
    request: CerebroChatRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroChatResponse:
    require_cerebro_write(current_user)
    return run_cerebro_chat(request, current_user)


@router.get("/inbox/sombra/recent", response_model=list[SombraInboxRecentMessage])
def read_sombra_inbox_recent(
    limit: int = 20,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[SombraInboxRecentMessage]:
    require_cerebro_read(current_user)
    return list_sombra_inbox_messages(limit=limit)


@router.get("/goals", response_model=list[CerebroCompanyGoal])
def read_company_goals(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CerebroCompanyGoal]:
    require_cerebro_read(current_user)
    return list_company_goals()


@router.post("/goals", response_model=CerebroCompanyGoal, status_code=status.HTTP_201_CREATED)
def write_company_goal(
    request: CerebroCompanyGoalCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroCompanyGoal:
    require_cerebro_write(current_user)
    return create_company_goal(request, current_user)


@router.get("/departments/goals", response_model=list[CerebroDepartmentGoal])
def read_department_goals(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CerebroDepartmentGoal]:
    require_cerebro_read(current_user)
    return list_department_goals()


@router.post(
    "/departments/goals",
    response_model=CerebroDepartmentGoal,
    status_code=status.HTTP_201_CREATED,
)
def write_department_goal(
    request: CerebroDepartmentGoalCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroDepartmentGoal:
    require_cerebro_write(current_user)
    return create_department_goal(request, current_user)


@router.get("/missions", response_model=list[CerebroMission])
def read_missions(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CerebroMission]:
    require_cerebro_read(current_user)
    return list_missions()


@router.post("/missions", response_model=CerebroMission, status_code=status.HTTP_201_CREATED)
def write_mission(
    request: CerebroMissionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroMission:
    require_cerebro_write(current_user)
    return create_mission(request, current_user)


@router.get("/missions/{mission_id}", response_model=CerebroMission)
def read_mission(
    mission_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroMission:
    require_cerebro_read(current_user)
    try:
        return get_mission(mission_id)
    except CerebroError as error:
        raise_cerebro_error(error)


@router.post("/missions/{mission_id}/update", response_model=CerebroMission)
def update_mission(
    mission_id: str,
    request: CerebroMissionUpdateCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroMission:
    require_cerebro_write(current_user)
    try:
        return add_mission_update(mission_id, request, current_user)
    except CerebroError as error:
        raise_cerebro_error(error)


@router.post("/missions/{mission_id}/dispatch", response_model=CerebroMission)
def dispatch_mission_to_department(
    mission_id: str,
    request: CerebroMissionDispatchRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroMission:
    require_cerebro_write(current_user)
    try:
        return dispatch_mission(mission_id, request, current_user)
    except CerebroError as error:
        raise_cerebro_error(error)


@router.get("/alerts", response_model=list[CerebroAlert])
def read_alerts(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CerebroAlert]:
    require_cerebro_read(current_user)
    return list_alerts()


@router.post("/alerts", response_model=CerebroAlert, status_code=status.HTTP_201_CREATED)
def write_alert(
    request: CerebroAlertCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroAlert:
    require_cerebro_write(current_user)
    return create_alert(request, current_user)


@router.get("/revenue", response_model=list[CerebroRevenueOpportunity])
def read_revenue_opportunities(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CerebroRevenueOpportunity]:
    require_cerebro_read(current_user)
    return list_revenue_opportunities()


@router.post(
    "/revenue/opportunities",
    response_model=CerebroRevenueOpportunity,
    status_code=status.HTTP_201_CREATED,
)
def write_revenue_opportunity(
    request: CerebroRevenueOpportunityCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroRevenueOpportunity:
    require_cerebro_write(current_user)
    return create_revenue_opportunity(request, current_user)


@router.get("/approval-requests", response_model=list[CerebroApprovalRequest])
def read_approval_requests(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CerebroApprovalRequest]:
    require_cerebro_read(current_user)
    return list_approval_requests()


@router.post(
    "/approval-requests",
    response_model=CerebroApprovalRequest,
    status_code=status.HTTP_201_CREATED,
)
def write_approval_request(
    request: CerebroApprovalRequestCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroApprovalRequest:
    require_cerebro_write(current_user)
    return create_approval_request(request, current_user)


@router.post("/approval-requests/{request_id}/approve", response_model=CerebroApprovalRequest)
def approve_approval_request(
    request_id: str,
    request: CerebroApprovalActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroApprovalRequest:
    require_cerebro_approval(current_user)
    try:
        return update_approval_request_status(
            request_id,
            "approve",
            request or CerebroApprovalActionRequest(),
            current_user,
        )
    except CerebroError as error:
        raise_cerebro_error(error)


@router.post("/approval-requests/{request_id}/reject", response_model=CerebroApprovalRequest)
def reject_approval_request(
    request_id: str,
    request: CerebroApprovalActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroApprovalRequest:
    require_cerebro_approval(current_user)
    try:
        return update_approval_request_status(
            request_id,
            "reject",
            request or CerebroApprovalActionRequest(),
            current_user,
        )
    except CerebroError as error:
        raise_cerebro_error(error)


@router.get("/checkpoints/morning", response_model=CerebroCheckpoint)
def read_morning_checkpoint(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroCheckpoint:
    require_cerebro_read(current_user)
    return build_checkpoint("morning")


@router.get("/checkpoints/midday", response_model=CerebroCheckpoint)
def read_midday_checkpoint(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroCheckpoint:
    require_cerebro_read(current_user)
    return build_checkpoint("midday")


@router.get("/checkpoints/evening", response_model=CerebroCheckpoint)
def read_evening_checkpoint(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CerebroCheckpoint:
    require_cerebro_read(current_user)
    return build_checkpoint("evening")


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
