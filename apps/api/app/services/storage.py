from app.core.database import initialize_database
from app.schemas.storage import StorageStatus


def get_storage_status() -> StorageStatus:
    status = initialize_database()
    return StorageStatus(**status.__dict__)

