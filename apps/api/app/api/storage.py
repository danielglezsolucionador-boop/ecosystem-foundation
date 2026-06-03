from fastapi import APIRouter

from app.schemas.storage import StorageStatus
from app.services.storage import get_storage_status

router = APIRouter(prefix="/api/v1/storage", tags=["storage"])


@router.get("/status", response_model=StorageStatus)
def read_storage_status() -> StorageStatus:
    return get_storage_status()

