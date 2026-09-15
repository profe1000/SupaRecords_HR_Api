from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"


class MetaResponse(BaseModel):
    service: str = "business-hr-api"
    version: str = "v1"
