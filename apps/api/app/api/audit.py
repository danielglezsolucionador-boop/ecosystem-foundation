from fastapi import APIRouter, status

from app.schemas.audit import AuditReport
from app.services.audit import list_audit_reports, run_local_audit

router = APIRouter(prefix="/api/v1/audit", tags=["audit"])


@router.post("/run", response_model=AuditReport, status_code=status.HTTP_201_CREATED)
def create_audit_report() -> AuditReport:
    return run_local_audit()


@router.get("/reports", response_model=list[AuditReport])
def read_audit_reports() -> list[AuditReport]:
    return list_audit_reports()

