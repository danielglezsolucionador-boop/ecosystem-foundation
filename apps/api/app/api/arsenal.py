from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.schemas.arsenal import (
    ArsenalBrokerRequest,
    ArsenalBrokerResponse,
    ArsenalBrokerStatus,
    ArsenalCatalogItem,
    ArsenalCatalogItemCreate,
    ArsenalCatalogItemEvaluateRequest,
    ArsenalCategory,
    ArsenalLinkedInOAuthStartResponse,
    ArsenalLinkedInPostRequest,
    ArsenalLinkedInPostResponse,
    ArsenalLinkedInStatus,
    ArsenalOffice,
    ArsenalReadiness,
    ArsenalResource,
    ArsenalResourceCreate,
    ArsenalResourceStatus,
    ArsenalResourceType,
    ArsenalRisk,
    ArsenalRiskCreate,
    ArsenalStatus,
)
from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.header_audit import HeaderAuditReport, HeaderAuditRequest
from app.services.arsenal import (
    ArsenalError,
    build_linkedin_oauth_start,
    create_catalog_item,
    create_risk,
    disable_resource,
    evaluate_catalog_item,
    get_broker_status,
    get_catalog_item,
    get_linkedin_status,
    get_readiness,
    get_resource,
    get_resource_for_office,
    get_status,
    list_catalog_items,
    list_categories,
    list_resources,
    list_risks,
    prepare_linkedin_post,
    register_resource,
    replace_resource,
    run_broker_request,
    send_catalog_item_to_forja,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.header_csp_auditor import (
    HeaderAuditError,
    get_header_audit,
    list_header_audits,
    run_header_audit,
)

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


def raise_header_audit_error(error: HeaderAuditError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=ArsenalStatus)
def read_arsenal_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalStatus:
    require_arsenal_read(current_user)
    return get_status()


@router.get("/broker/status", response_model=ArsenalBrokerStatus)
def read_arsenal_broker_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalBrokerStatus:
    require_arsenal_read(current_user)
    return get_broker_status()


@router.post("/broker/complete", response_model=ArsenalBrokerResponse)
def write_arsenal_broker_completion(
    request: ArsenalBrokerRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalBrokerResponse:
    require_arsenal_write(current_user)
    try:
        return run_broker_request(request, current_user)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.get("/linkedin/status", response_model=ArsenalLinkedInStatus)
def read_arsenal_linkedin_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalLinkedInStatus:
    require_arsenal_read(current_user)
    return get_linkedin_status()


@router.get(
    "/linkedin/oauth/start",
    response_model=ArsenalLinkedInOAuthStartResponse,
)
def read_arsenal_linkedin_oauth_start(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalLinkedInOAuthStartResponse:
    require_arsenal_read(current_user)
    return build_linkedin_oauth_start()


@router.post("/linkedin/posts", response_model=ArsenalLinkedInPostResponse)
def write_arsenal_linkedin_post(
    request: ArsenalLinkedInPostRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalLinkedInPostResponse:
    require_arsenal_write(current_user)
    try:
        return prepare_linkedin_post(request, current_user)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.get("/resources", response_model=list[ArsenalResource])
def read_arsenal_resources(
    name: str | None = None,
    resource_type: ArsenalResourceType | None = Query(default=None, alias="type"),
    office: ArsenalOffice | None = None,
    category: str | None = None,
    resource_status: ArsenalResourceStatus | None = Query(
        default=None,
        alias="status",
    ),
    active_only: bool = False,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[ArsenalResource]:
    require_arsenal_read(current_user)
    try:
        return list_resources(
            name=name,
            resource_type=resource_type,
            office=office,
            category=category,
            status=resource_status,
            active_only=active_only,
            actor=current_user,
        )
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.get("/resources/{resource_id}", response_model=ArsenalResource)
def read_arsenal_resource(
    resource_id: str,
    office: ArsenalOffice | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalResource:
    require_arsenal_read(current_user)
    try:
        if office:
            return get_resource_for_office(office, resource_id, current_user)
        return get_resource(resource_id)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.post(
    "/tools/header-csp-auditor/analyze",
    response_model=HeaderAuditReport,
)
def analyze_headers_with_arsenal(
    request: HeaderAuditRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> HeaderAuditReport:
    require_arsenal_write(current_user)
    try:
        return run_header_audit(request, current_user)
    except HeaderAuditError as error:
        raise_header_audit_error(error)


@router.get(
    "/tools/header-csp-auditor/results",
    response_model=list[HeaderAuditReport],
)
def read_header_audit_results(
    limit: int = Query(default=20, ge=1, le=100),
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[HeaderAuditReport]:
    require_arsenal_read(current_user)
    return list_header_audits(limit=limit)


@router.get(
    "/tools/header-csp-auditor/results/{report_id}",
    response_model=HeaderAuditReport,
)
def read_header_audit_result(
    report_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> HeaderAuditReport:
    require_arsenal_read(current_user)
    try:
        return get_header_audit(report_id)
    except HeaderAuditError as error:
        raise_header_audit_error(error)


@router.post(
    "/resources",
    response_model=ArsenalResource,
    status_code=status.HTTP_201_CREATED,
)
def write_arsenal_resource(
    request: ArsenalResourceCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalResource:
    require_arsenal_write(current_user)
    try:
        return register_resource(request, current_user)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.post(
    "/resources/{resource_id}/replace",
    response_model=ArsenalResource,
    status_code=status.HTTP_201_CREATED,
)
def replace_arsenal_resource(
    resource_id: str,
    request: ArsenalResourceCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalResource:
    require_arsenal_write(current_user)
    try:
        return replace_resource(resource_id, request, current_user)
    except ArsenalError as error:
        raise_arsenal_error(error)


@router.post("/resources/{resource_id}/disable", response_model=ArsenalResource)
def disable_arsenal_resource(
    resource_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> ArsenalResource:
    require_arsenal_write(current_user)
    try:
        return disable_resource(resource_id, current_user)
    except ArsenalError as error:
        raise_arsenal_error(error)


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
