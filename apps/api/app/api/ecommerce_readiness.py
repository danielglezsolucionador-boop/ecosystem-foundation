from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.ecommerce_readiness import AmazonReadinessStatus, CommerceOpportunity, EcommerceReadinessStatus
from app.services.auth import get_current_user, require_control_center_user
from app.services.ecommerce_readiness import (
    get_amazon_readiness_status,
    get_ecommerce_readiness_status,
    list_amazon_opportunities,
    list_amazon_risks,
    list_ecommerce_approval_needed,
    list_ecommerce_opportunities,
)

ecommerce_router = APIRouter(
    prefix="/api/v1/ecommerce-readiness",
    tags=["ecommerce-readiness"],
    dependencies=[Depends(require_control_center_user)],
)
amazon_router = APIRouter(
    prefix="/api/v1/amazon-readiness",
    tags=["amazon-readiness"],
    dependencies=[Depends(require_control_center_user)],
)

READ_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}


def require_commerce_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "commerce_readiness_role_not_authorized", "role": user.role.value},
        )


@ecommerce_router.get("/status", response_model=EcommerceReadinessStatus)
def read_ecommerce_readiness_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> EcommerceReadinessStatus:
    require_commerce_read(current_user)
    return get_ecommerce_readiness_status()


@ecommerce_router.get("/opportunities", response_model=list[CommerceOpportunity])
def read_ecommerce_readiness_opportunities(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CommerceOpportunity]:
    require_commerce_read(current_user)
    return list_ecommerce_opportunities()


@ecommerce_router.get("/approval-needed", response_model=list[CommerceOpportunity])
def read_ecommerce_readiness_approval_needed(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CommerceOpportunity]:
    require_commerce_read(current_user)
    return list_ecommerce_approval_needed()


@amazon_router.get("/status", response_model=AmazonReadinessStatus)
def read_amazon_readiness_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> AmazonReadinessStatus:
    require_commerce_read(current_user)
    return get_amazon_readiness_status()


@amazon_router.get("/opportunities", response_model=list[CommerceOpportunity])
def read_amazon_readiness_opportunities(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CommerceOpportunity]:
    require_commerce_read(current_user)
    return list_amazon_opportunities()


@amazon_router.get("/risks", response_model=list[CommerceOpportunity])
def read_amazon_readiness_risks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[CommerceOpportunity]:
    require_commerce_read(current_user)
    return list_amazon_risks()
