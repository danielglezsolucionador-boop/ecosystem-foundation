from pydantic import BaseModel, Field


class IntegrationContract(BaseModel):
    id: str = Field(min_length=1)
    name: str = Field(min_length=1)
    provider: str = Field(min_length=1)
    endpoint: str = Field(min_length=1)
    method: str = Field(min_length=1)
    status: str = Field(min_length=1)
    external_dependency: bool
    description: str = Field(min_length=1)

