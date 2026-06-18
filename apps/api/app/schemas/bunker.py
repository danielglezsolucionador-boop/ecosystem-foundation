from enum import StrEnum

from pydantic import BaseModel, Field


class BunkerSealedStatus(StrEnum):
    sealed = "SELLADO"
    reviewed_by_ceo = "REVISADO_POR_CEO"
    share_with_cerebro = "COMPARTIR_CON_CEREBRO"
    archived = "ARCHIVADO"


class BunkerSealedAccess(StrEnum):
    ceo_only = "CEO_ONLY"


class SealedReport(BaseModel):
    id: str = Field(min_length=1)
    source: str = Field(default="SOMBRA", min_length=1)
    classification: str = Field(default="SECRETO_MILITAR_CEO", min_length=1)
    original_message_id: str = Field(min_length=1)
    filename_or_id: str = Field(min_length=1)
    vault_path: str = Field(min_length=1)
    content_sha256: str = Field(min_length=64, max_length=64)
    content_size_bytes: int = Field(ge=0)
    status: BunkerSealedStatus = BunkerSealedStatus.sealed
    access: BunkerSealedAccess = BunkerSealedAccess.ceo_only
    source_created_at: str | None = None
    received_at: str = Field(min_length=1)
    updated_at: str = Field(min_length=1)
    audit_access_count: int = Field(default=0, ge=0)
    metadata: dict[str, object] = Field(default_factory=dict)


class SealedReportStatusUpdate(BaseModel):
    status: BunkerSealedStatus
    reason: str | None = Field(default=None, max_length=400)
