from pydantic import BaseModel, Field


class AuditCheck(BaseModel):
    id: str = Field(min_length=1)
    status: str = Field(pattern="^(pass|fail)$")
    detail: str = Field(min_length=1)


class AuditReport(BaseModel):
    id: str
    status: str = Field(pattern="^(pass|fail)$")
    checks: list[AuditCheck]
    created_at: str

