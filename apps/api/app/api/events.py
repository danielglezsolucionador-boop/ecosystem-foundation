from fastapi import APIRouter, HTTPException, status as http_status

from app.schemas.events import (
    EventAuditEvent,
    EventCatalogItem,
    EventConsumer,
    EventCreate,
    EventRecord,
    EventReplayRequest,
    EventReplayResult,
    EventStatus,
    EventStatusSummary,
)
from app.services.events import (
    EventValidationError,
    get_event,
    get_event_status,
    list_dead_letter_events,
    list_event_audit,
    list_event_catalog,
    list_event_consumers,
    list_events,
    publish_event,
    replay_event,
)

router = APIRouter(prefix="/api/v1/events", tags=["events"])


@router.get("", response_model=list[EventRecord])
def read_events(
    status: EventStatus | None = None,
    type: str | None = None,
    source: str | None = None,
) -> list[EventRecord]:
    return list_events(status=status, type=type, source=source)


@router.post("", response_model=EventRecord, status_code=http_status.HTTP_201_CREATED)
def create_event(event: EventCreate) -> EventRecord:
    try:
        return publish_event(event)
    except EventValidationError as exc:
        raise HTTPException(status_code=400, detail=exc.detail) from exc


@router.get("/status", response_model=EventStatusSummary)
def read_event_status() -> EventStatusSummary:
    return get_event_status()


@router.get("/catalog", response_model=list[EventCatalogItem])
def read_event_catalog() -> list[EventCatalogItem]:
    return list(list_event_catalog())


@router.get("/consumers", response_model=list[EventConsumer])
def read_event_consumers() -> list[EventConsumer]:
    return list(list_event_consumers())


@router.get("/audit", response_model=list[EventAuditEvent])
def read_event_audit() -> list[EventAuditEvent]:
    return list_event_audit()


@router.get("/dead-letter", response_model=list[EventRecord])
def read_dead_letter_events() -> list[EventRecord]:
    return list_dead_letter_events()


@router.get("/{event_id}", response_model=EventRecord)
def read_event(event_id: str) -> EventRecord:
    event = get_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "event_not_found",
                "event_id": event_id,
            },
        )

    return event


@router.post("/{event_id}/replay", response_model=EventReplayResult)
def replay_internal_event(
    event_id: str,
    request: EventReplayRequest | None = None,
) -> EventReplayResult:
    result = replay_event(
        event_id=event_id,
        reason=request.reason if request else "manual_replay",
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "event_not_found",
                "event_id": event_id,
            },
        )

    return result
