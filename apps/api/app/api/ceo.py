from fastapi import APIRouter, Depends, HTTPException

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.ceo import CeoDailyCenter, CeoDailyView, CeoDecisionActionRequest
from app.schemas.governance import GovernanceDecision, GovernanceRole
from app.services.auth import get_current_user, governance_role, require_control_center_user
from app.services.ceo import (
    approve_ceo_decision,
    build_evening_view,
    build_morning_view,
    get_ceo_daily_center,
    list_ceo_decisions,
    reject_ceo_decision,
)
from app.services.governance import GovernanceError

router = APIRouter(
    prefix="/api/v1/ceo",
    tags=["ceo"],
    dependencies=[Depends(require_control_center_user)],
)

CEO_READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}


def role_from_user(user: AuthenticatedUser) -> GovernanceRole:
    return GovernanceRole(governance_role(user.role))


def ensure_ceo_read(user: AuthenticatedUser) -> None:
    if user.role not in CEO_READ_ROLES:
        raise HTTPException(
            status_code=403,
            detail={"error": "ceo_daily_center_role_not_authorized", "role": user.role.value},
        )


def raise_governance_error(error: GovernanceError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/daily-center", response_model=CeoDailyCenter)
def read_daily_center(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CeoDailyCenter:
    ensure_ceo_read(current_user)
    return get_ceo_daily_center()


@router.get("/morning", response_model=CeoDailyView)
def read_morning(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CeoDailyView:
    ensure_ceo_read(current_user)
    return build_morning_view()


@router.get("/evening", response_model=CeoDailyView)
def read_evening(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> CeoDailyView:
    ensure_ceo_read(current_user)
    return build_evening_view()


@router.get("/decisions", response_model=list[GovernanceDecision])
def read_ceo_decisions(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[GovernanceDecision]:
    ensure_ceo_read(current_user)
    return list_ceo_decisions()


@router.post("/decisions/{decision_id}/approve", response_model=GovernanceDecision)
def approve_decision_from_ceo_center(
    decision_id: str,
    request: CeoDecisionActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceDecision:
    try:
        return approve_ceo_decision(
            decision_id,
            request or CeoDecisionActionRequest(),
            role_from_user(current_user),
        )
    except GovernanceError as error:
        raise_governance_error(error)


@router.post("/decisions/{decision_id}/reject", response_model=GovernanceDecision)
def reject_decision_from_ceo_center(
    decision_id: str,
    request: CeoDecisionActionRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> GovernanceDecision:
    try:
        return reject_ceo_decision(
            decision_id,
            request or CeoDecisionActionRequest(),
            role_from_user(current_user),
        )
    except GovernanceError as error:
        raise_governance_error(error)
