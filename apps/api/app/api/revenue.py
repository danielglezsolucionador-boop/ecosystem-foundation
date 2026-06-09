from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.revenue import (
    RevenueApprovalRequest,
    RevenueDailyReport,
    RevenueDepartmentContribution,
    RevenueGoal,
    RevenueGoalCreate,
    RevenueOpportunity,
    RevenueOpportunityCreate,
    RevenueOpportunityEvaluateRequest,
    RevenueSprintDaily,
    RevenueSprintMission,
    RevenueSprintMissionCreate,
    RevenueSprintReport,
    RevenueSprintReportCreate,
    RevenueSprintRoute,
    RevenueSprintRouteCreate,
    RevenueSprintStatus,
    RevenueStatus,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.revenue import (
    RevenueError,
    create_goal,
    create_opportunity,
    create_revenue_sprint_mission,
    create_revenue_sprint_report,
    create_sprint_route,
    evaluate_opportunity,
    get_daily_report,
    get_department_contribution,
    get_opportunity,
    get_revenue_status,
    get_revenue_sprint_approval_needed,
    get_revenue_sprint_daily,
    get_revenue_sprint_risks,
    get_revenue_sprint_status,
    list_approval_requests,
    list_goals,
    list_opportunities,
    list_sprint_missions,
    list_sprint_routes,
    request_approval_for_opportunity,
    start_revenue_sprint,
)

router = APIRouter(
    prefix="/api/v1/revenue",
    tags=["revenue"],
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


def require_revenue_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "revenue_role_not_authorized", "role": user.role.value},
        )


def require_revenue_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "revenue_write_role_not_authorized", "role": user.role.value},
        )


def raise_revenue_error(error: RevenueError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=RevenueStatus)
def read_revenue_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueStatus:
    require_revenue_read(current_user)
    return get_revenue_status()


@router.get("/goals", response_model=list[RevenueGoal])
def read_revenue_goals(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RevenueGoal]:
    require_revenue_read(current_user)
    return list_goals()


@router.post("/goals", response_model=RevenueGoal, status_code=status.HTTP_201_CREATED)
def write_revenue_goal(
    request: RevenueGoalCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueGoal:
    require_revenue_write(current_user)
    return create_goal(request, current_user)


@router.get("/opportunities", response_model=list[RevenueOpportunity])
def read_revenue_opportunities(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RevenueOpportunity]:
    require_revenue_read(current_user)
    return list_opportunities()


@router.post(
    "/opportunities",
    response_model=RevenueOpportunity,
    status_code=status.HTTP_201_CREATED,
)
def write_revenue_opportunity(
    request: RevenueOpportunityCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueOpportunity:
    require_revenue_write(current_user)
    return create_opportunity(request, current_user)


@router.get("/opportunities/{opportunity_id}", response_model=RevenueOpportunity)
def read_revenue_opportunity(
    opportunity_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueOpportunity:
    require_revenue_read(current_user)
    try:
        return get_opportunity(opportunity_id)
    except RevenueError as error:
        raise_revenue_error(error)


@router.post("/opportunities/{opportunity_id}/evaluate", response_model=RevenueOpportunity)
def evaluate_revenue_opportunity(
    opportunity_id: str,
    request: RevenueOpportunityEvaluateRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueOpportunity:
    require_revenue_write(current_user)
    try:
        return evaluate_opportunity(
            opportunity_id,
            request or RevenueOpportunityEvaluateRequest(),
            current_user,
        )
    except RevenueError as error:
        raise_revenue_error(error)


@router.post(
    "/opportunities/{opportunity_id}/request-approval",
    response_model=RevenueApprovalRequest,
)
def request_revenue_approval(
    opportunity_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueApprovalRequest:
    require_revenue_write(current_user)
    try:
        return request_approval_for_opportunity(opportunity_id, current_user)
    except RevenueError as error:
        raise_revenue_error(error)


@router.get("/approval-requests", response_model=list[RevenueApprovalRequest])
def read_revenue_approval_requests(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RevenueApprovalRequest]:
    require_revenue_read(current_user)
    return list_approval_requests()


@router.get("/daily-report", response_model=RevenueDailyReport)
def read_revenue_daily_report(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueDailyReport:
    require_revenue_read(current_user)
    return get_daily_report()


@router.get("/department-contribution", response_model=list[RevenueDepartmentContribution])
def read_revenue_department_contribution(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RevenueDepartmentContribution]:
    require_revenue_read(current_user)
    return get_department_contribution()


@router.get("/sprint/status", response_model=RevenueSprintStatus)
def read_revenue_sprint_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueSprintStatus:
    require_revenue_read(current_user)
    return get_revenue_sprint_status()


@router.post("/sprint/start", response_model=RevenueSprintStatus)
def start_revenue_execution_sprint(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueSprintStatus:
    require_revenue_write(current_user)
    return start_revenue_sprint(current_user)


@router.get("/sprint/routes", response_model=list[RevenueSprintRoute])
def read_revenue_sprint_routes(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RevenueSprintRoute]:
    require_revenue_read(current_user)
    return list_sprint_routes()


@router.post("/sprint/routes", response_model=RevenueSprintRoute, status_code=status.HTTP_201_CREATED)
def write_revenue_sprint_route(
    request: RevenueSprintRouteCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueSprintRoute:
    require_revenue_write(current_user)
    try:
        return create_sprint_route(request, current_user)
    except RevenueError as error:
        raise_revenue_error(error)


@router.get("/sprint/missions", response_model=list[RevenueSprintMission])
def read_revenue_sprint_missions(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RevenueSprintMission]:
    require_revenue_read(current_user)
    return list_sprint_missions()


@router.post("/sprint/missions", response_model=RevenueSprintMission, status_code=status.HTTP_201_CREATED)
def write_revenue_sprint_mission(
    request: RevenueSprintMissionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueSprintMission:
    require_revenue_write(current_user)
    try:
        return create_revenue_sprint_mission(request, current_user)
    except RevenueError as error:
        raise_revenue_error(error)


@router.get("/sprint/daily", response_model=RevenueSprintDaily)
def read_revenue_sprint_daily(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueSprintDaily:
    require_revenue_read(current_user)
    return get_revenue_sprint_daily()


@router.get("/sprint/risks")
def read_revenue_sprint_risks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[dict]:
    require_revenue_read(current_user)
    return get_revenue_sprint_risks()


@router.get("/sprint/approval-needed", response_model=list[RevenueSprintRoute])
def read_revenue_sprint_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[RevenueSprintRoute]:
    require_revenue_read(current_user)
    return get_revenue_sprint_approval_needed()


@router.post("/sprint/report", response_model=RevenueSprintReport, status_code=status.HTTP_201_CREATED)
def write_revenue_sprint_report(
    request: RevenueSprintReportCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> RevenueSprintReport:
    require_revenue_write(current_user)
    return create_revenue_sprint_report(request, current_user)
