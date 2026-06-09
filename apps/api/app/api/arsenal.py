from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.arsenal import (
    ArsenalCatalogItem,
    ArsenalCatalogItemCreate,
    ArsenalCatalogItemEvaluateRequest,
    ArsenalCategory,
    ArsenalReadiness,
    ArsenalRisk,
    ArsenalRiskCreate,
    ArsenalStatus,
)
from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.services.arsenal import (
    ArsenalError,
    create_catalog_item,
    create_risk,
    evaluate_catalog_item,
    get_catalog_item,
    get_readiness,
    get_status,
    list_catalog_items,
    list_categories,
    list_risks,
    send_catalog_item_to_forja,
)
from app.services.auth import get_current_user, require_control_center_user

router = APIRouter(
    prefix="/api/v1/arsenal",
    tags=["arsenal"],
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
AUDIT_ROLES = {
    ControlCenterRole.ceo,
    ControlCenterRole.admin,
    ControlCenterRole.operator,
    ControlCenterRole.auditor,
}


def require_arsenal_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "arsenal_role_not_authorized", "role": user.role.value},
        )


def require_arsenal_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "arsenal_write_role_not_authorized", "role": user.role.value},
        )


def require_arsenal_audit(user: AuthenticatedUser) -> None:
    if user.role not in AUDIT_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "arsenal_audit_role_not_authorized", "role": user.role.value},
        )


def raise_arsenal_error(error: ArsenalError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=ArsenalStatus)
def read_arsenal_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalStatus:
    require_arsenal_read(current_user)
    return get_status()


@router.get("/catalog", response_model=list[ArsenalCatalogItem])
def read_arsenal_catalog(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ArsenalCatalogItem]:
    require_arsenal_read(current_user)
    return list_catalog_items()


@router.post("/catalog", response_model=ArsenalCatalogItem, status_code=status.HTTP_201_CREATED)
def write_arsenal_catalog_item(
    request: ArsenalCatalogItemCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalCatalogItem:
    require_arsenal_write(current_user)
    try:
        return create_catalog_item(request, current_user)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.get("/catalog/{item_id}", response_model=ArsenalCatalogItem)
def read_arsenal_catalog_item(
    item_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalCatalogItem:
    require_arsenal_read(current_user)
    try:
        return get_catalog_item(item_id)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.post("/catalog/{item_id}/evaluate", response_model=ArsenalCatalogItem)
def evaluate_arsenal_catalog_item(
    item_id: str,
    request: ArsenalCatalogItemEvaluateRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalCatalogItem:
    require_arsenal_audit(current_user)
    try:
        return evaluate_catalog_item(
            item_id,
            request or ArsenalCatalogItemEvaluateRequest(),
            current_user,
        )
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.post("/catalog/{item_id}/send-to-forja")
def send_arsenal_catalog_item_to_forja(
    item_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> dict[str, object]:
    require_arsenal_write(current_user)
    try:
        return send_catalog_item_to_forja(item_id, current_user)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.get("/categories", response_model=list[ArsenalCategory])
def read_arsenal_categories(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ArsenalCategory]:
    require_arsenal_read(current_user)
    return list_categories()


@router.get("/risks", response_model=list[ArsenalRisk])
def read_arsenal_risks(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ArsenalRisk]:
    require_arsenal_read(current_user)
    return list_risks()


@router.post("/risks", response_model=ArsenalRisk, status_code=status.HTTP_201_CREATED)
def write_arsenal_risk(
    request: ArsenalRiskCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalRisk:
    require_arsenal_write(current_user)
    try:
        return create_risk(request, current_user)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.get("/readiness", response_model=ArsenalReadiness)
def read_arsenal_readiness(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalReadiness:
    require_arsenal_read(current_user)
    return get_readiness()
