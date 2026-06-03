from pydantic import BaseModel


class StorageStatus(BaseModel):
    status: str
    backend: str
    configured: bool
    persistent: bool
    schema_version: str

