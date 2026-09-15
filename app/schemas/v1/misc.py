from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class MetaResponse(BaseModel):
    service: str = "hotel-management-api"
    version: str = "v1"
