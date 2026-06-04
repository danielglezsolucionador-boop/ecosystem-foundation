from fastapi import APIRouter, HTTPException, status

from app.schemas.audit import (
    AuditCategory,
    AuditEvent,
    AuditEventCreate,
    AuditOverview,
    AuditReport,
    AuditReportGenerateRequest,
)
from app.services.audit import (
    create_audit_event,
    get_audit_event,
    get_audit_overview,
    list_audit_events,
    list_audit_reports,
    run_local_audit,
)

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.get("", response_model=AuditOverview)
def read_audit_overview() -> AuditOverview:
    return get_audit_overview()


@router.post("/run", response_model=AuditReport, status_code=status.HTTP_201_CREATED)
def create_audit_report() -> AuditReport:
    return run_local_audit()


@router.post(
    "/reports/generate",
    response_model=AuditReport,
    status_code=status.HTTP_201_CREATED,
)
def generate_audit_report(
    request: AuditReportGenerateRequest | None = None,
) -> AuditReport:
    return run_local_audit()


@router.get("/reports", response_model=list[AuditReport])
def read_audit_reports() -> list[AuditReport]:
    return list_audit_reports()


@router.post("/events", response_model=AuditEvent, status_code=status.HTTP_201_CREATED)
def write_audit_event(event: AuditEventCreate) -> AuditEvent:
    return create_audit_event(event)


@router.get("/events/{event_id}", response_model=AuditEvent)
def read_audit_event(event_id: str) -> AuditEvent:
    event = get_audit_event(event_id)

    if event is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "audit_event_not_found",
                "event_id": event_id,
            },
        )

    return event


@router.get("/security", response_model=list[AuditEvent])
def read_security_audit_events() -> list[AuditEvent]:
    return list_audit_events(AuditCategory.security)


@router.get("/configuration", response_model=list[AuditEvent])
def read_configuration_audit_events() -> list[AuditEvent]:
    return list_audit_events(AuditCategory.configuration)


@router.get("/integration", response_model=list[AuditEvent])
def read_integration_audit_events() -> list[AuditEvent]:
    return list_audit_events(AuditCategory.integration)


@router.get("/runtime", response_model=list[AuditEvent])
def read_runtime_audit_events() -> list[AuditEvent]:
    return list_audit_events(AuditCategory.runtime)


@router.get("/errors", response_model=list[AuditEvent])
def read_error_audit_events() -> list[AuditEvent]:
    return list_audit_events(AuditCategory.error)
