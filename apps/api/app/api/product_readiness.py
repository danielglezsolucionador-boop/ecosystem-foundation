from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.product_readiness import (
    ProductReadinessAuditRequest,
    ProductReadinessForjaRequest,
    ProductReadinessGap,
    ProductReadinessMarketingPackage,
    ProductReadinessProduct,
    ProductReadinessStatus,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.product_readiness import (
    ProductReadinessError,
    audit_product_readiness,
    generate_marketing_package,
    get_marketing_package,
    get_product,
    get_product_readiness_status,
    list_gaps,
    send_gap_to_forja,
)

router = APIRouter(
    prefix="/api/v1/product-readiness",
    tags=["product-readiness"],
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
    ControlCenterRole.auditor,
}


def require_product_readiness_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "product_readiness_role_not_authorized", "role": user.role.value},
        )


def require_product_readiness_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "product_readiness_write_role_not_authorized", "role": user.role.value},
        )


def raise_product_readiness_error(error: ProductReadinessError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=ProductReadinessStatus)
def read_product_readiness_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProductReadinessStatus:
    require_product_readiness_read(current_user)
    return get_product_readiness_status()


@router.get("/dcft", response_model=ProductReadinessProduct)
def read_dcft_readiness(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProductReadinessProduct:
    require_product_readiness_read(current_user)
    return get_product("dcft")


@router.post("/dcft/audit", response_model=ProductReadinessProduct)
def audit_dcft_readiness(
    request: ProductReadinessAuditRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProductReadinessProduct:
    require_product_readiness_write(current_user)
    return audit_product_readiness("dcft", request or ProductReadinessAuditRequest(), current_user)


@router.get("/sentinela", response_model=ProductReadinessProduct)
def read_sentinela_readiness(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProductReadinessProduct:
    require_product_readiness_read(current_user)
    return get_product("sentinela")


@router.post("/sentinela/audit", response_model=ProductReadinessProduct)
def audit_sentinela_readiness(
    request: ProductReadinessAuditRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProductReadinessProduct:
    require_product_readiness_write(current_user)
    return audit_product_readiness("sentinela", request or ProductReadinessAuditRequest(), current_user)


@router.get("/gaps", response_model=list[ProductReadinessGap])
def read_product_readiness_gaps(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ProductReadinessGap]:
    require_product_readiness_read(current_user)
    return list_gaps()


@router.post("/gaps/{gap_id}/send-to-forja", response_model=ProductReadinessGap)
def send_product_readiness_gap_to_forja(
    gap_id: str,
    request: ProductReadinessForjaRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProductReadinessGap:
    require_product_readiness_write(current_user)
    try:
        return send_gap_to_forja(gap_id, request or ProductReadinessForjaRequest(), current_user)
    except ProductReadinessError as error:
        raise_product_readiness_error(error)


@router.get("/marketing-package", response_model=ProductReadinessMarketingPackage)
def read_product_readiness_marketing_package(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProductReadinessMarketingPackage:
    require_product_readiness_read(current_user)
    return get_marketing_package()


@router.post("/marketing-package/generate", response_model=ProductReadinessMarketingPackage)
def generate_product_readiness_marketing_package(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ProductReadinessMarketingPackage:
    require_product_readiness_write(current_user)
    return generate_marketing_package(current_user)
