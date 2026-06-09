from fastapi import APIRouter, Depends, HTTPException, status

from app.schemas.auth import AuthenticatedUser, ControlCenterRole
from app.schemas.publishing import (
    PublishingCalendarEntry,
    PublishingChannel,
    PublishingChannelCreate,
    PublishingContentCreate,
    PublishingContentItem,
    PublishingGrowthMetric,
    PublishingGrowthMetricCreate,
    PublishingMarkPublishedRequest,
    PublishingScheduleRequest,
    PublishingStatus,
)
from app.services.auth import get_current_user, require_control_center_user
from app.services.publishing import (
    PublishingError,
    create_channel,
    create_content_item,
    create_growth_metric,
    get_content_item,
    get_publishing_status,
    list_calendar_entries,
    list_channels,
    list_content_items,
    list_growth_metrics,
    mark_content_published,
    schedule_content_item,
)

router = APIRouter(
    prefix="/api/v1/publishing",
    tags=["publishing"],
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


def require_publishing_read(user: AuthenticatedUser) -> None:
    if user.role not in READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "publishing_role_not_authorized", "role": user.role.value},
        )


def require_publishing_write(user: AuthenticatedUser) -> None:
    if user.role not in WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "publishing_write_role_not_authorized", "role": user.role.value},
        )


def raise_publishing_error(error: PublishingError) -> None:
    raise HTTPException(status_code=error.status_code, detail=error.detail) from error


@router.get("/status", response_model=PublishingStatus)
def read_publishing_status(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PublishingStatus:
    require_publishing_read(current_user)
    return get_publishing_status()


@router.get("/channels", response_model=list[PublishingChannel])
def read_publishing_channels(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[PublishingChannel]:
    require_publishing_read(current_user)
    return list_channels()


@router.post("/channels", response_model=PublishingChannel, status_code=status.HTTP_201_CREATED)
def write_publishing_channel(
    request: PublishingChannelCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PublishingChannel:
    require_publishing_write(current_user)
    return create_channel(request, current_user)


@router.get("/calendar", response_model=list[PublishingCalendarEntry])
def read_publishing_calendar(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[PublishingCalendarEntry]:
    require_publishing_read(current_user)
    return list_calendar_entries()


@router.post("/calendar", response_model=PublishingContentItem, status_code=status.HTTP_201_CREATED)
def write_publishing_calendar(
    request: PublishingContentCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PublishingContentItem:
    require_publishing_write(current_user)
    return create_content_item(request, current_user)


@router.get("/content", response_model=list[PublishingContentItem])
def read_publishing_content(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[PublishingContentItem]:
    require_publishing_read(current_user)
    return list_content_items()


@router.post("/content", response_model=PublishingContentItem, status_code=status.HTTP_201_CREATED)
def write_publishing_content(
    request: PublishingContentCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PublishingContentItem:
    require_publishing_write(current_user)
    return create_content_item(request, current_user)


@router.get("/content/{content_id}", response_model=PublishingContentItem)
def read_publishing_content_item(
    content_id: str,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PublishingContentItem:
    require_publishing_read(current_user)
    try:
        return get_content_item(content_id)
    except PublishingError as error:
        raise_publishing_error(error)


@router.post("/content/{content_id}/schedule", response_model=PublishingContentItem)
def schedule_publishing_content(
    content_id: str,
    request: PublishingScheduleRequest,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PublishingContentItem:
    require_publishing_write(current_user)
    try:
        return schedule_content_item(content_id, request, current_user)
    except PublishingError as error:
        raise_publishing_error(error)


@router.post("/content/{content_id}/mark-published", response_model=PublishingContentItem)
def mark_publishing_content_published(
    content_id: str,
    request: PublishingMarkPublishedRequest | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PublishingContentItem:
    require_publishing_write(current_user)
    try:
        return mark_content_published(content_id, request or PublishingMarkPublishedRequest(), current_user)
    except PublishingError as error:
        raise_publishing_error(error)


@router.get("/growth", response_model=list[PublishingGrowthMetric])
def read_publishing_growth(
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> list[PublishingGrowthMetric]:
    require_publishing_read(current_user)
    return list_growth_metrics()


@router.post("/growth/metrics", response_model=PublishingGrowthMetric, status_code=status.HTTP_201_CREATED)
def write_publishing_growth_metric(
    request: PublishingGrowthMetricCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
) -> PublishingGrowthMetric:
    require_publishing_write(current_user)
    return create_growth_metric(request, current_user)
