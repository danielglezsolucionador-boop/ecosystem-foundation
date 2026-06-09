from fastapi import APIRouter, Depends, HTTPException, status as http_status

from app.schemas.audit import (
    AuditoriaDecisionRequest,
    AuditoriaReview,
    AuditoriaReviewCreate,
    AuditoriaStatus,
)
from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.services.audit import (
    create_auditoria_review,
    decide_auditoria_review,
    get_auditoria_review,
    get_auditoria_status,
    list_auditoria_queue,
    list_auditoria_reviews,
)
from app.services.auth import get_current_user

router = APIRouter(prefix="/api/v1/auditoria", tags=["auditoria"])

AUDITORIA_READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}
AUDITORIA_CREATE_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
}
AUDITORIA_DECISION_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.auditor,
}


def ensure_auditoria_role(
    user: AuthenticatedUser,
    allowed_roles: set[ControlCenterRole],
    action: str,
) -> None:
    if user.role not in allowed_roles:
        raise HTTPException(
            status_code=403,
            detail={
                "error": "auditoria_role_not_authorized",
                "role": user.role.value,
                "action": action,
            },
        )


@router.get("/status", response_model=AuditoriaStatus)
def read_auditoria_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuditoriaStatus:
    ensure_auditoria_role(current_user, AUDITORIA_READ_ROLES, "read_status")
    return get_auditoria_status()


@router.get("/reviews", response_model=list[AuditoriaReview])
def read_auditoria_reviews(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[AuditoriaReview]:
    ensure_auditoria_role(current_user, AUDITORIA_READ_ROLES, "read_reviews")
    return list_auditoria_reviews()


@router.post(
    "/reviews",
    response_model=AuditoriaReview,
    status_code=http_status.HTTP_201_CREATED,
)
def write_auditoria_review(
    request: AuditoriaReviewCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuditoriaReview:
    ensure_auditoria_role(current_user, AUDITORIA_CREATE_ROLES, "create_review")
    return create_auditoria_review(request)


@router.get("/reviews/{review_id}", response_model=AuditoriaReview)
def read_auditoria_review(
    review_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuditoriaReview:
    ensure_auditoria_role(current_user, AUDITORIA_READ_ROLES, "read_review")
    review = get_auditoria_review(review_id)
    if review is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "auditoria_review_not_found", "review_id": review_id},
        )
    return review


@router.post("/reviews/{review_id}/decision", response_model=AuditoriaReview)
def decide_review(
    review_id: str,
    request: AuditoriaDecisionRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AuditoriaReview:
    ensure_auditoria_role(current_user, AUDITORIA_DECISION_ROLES, "decide_review")
    try:
        review = decide_auditoria_review(review_id, request)
    except PermissionError as exc:
        raise HTTPException(
            status_code=403,
            detail={"error": str(exc), "review_id": review_id},
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail={"error": str(exc), "review_id": review_id},
        ) from exc

    if review is None:
        raise HTTPException(
            status_code=404,
            detail={"error": "auditoria_review_not_found", "review_id": review_id},
        )
    return review


@router.get("/queue", response_model=list[AuditoriaReview])
def read_auditoria_queue(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[AuditoriaReview]:
    ensure_auditoria_role(current_user, AUDITORIA_READ_ROLES, "read_queue")
    return list_auditoria_queue()
