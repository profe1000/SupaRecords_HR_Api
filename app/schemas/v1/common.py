from __future__ import annotations

from typing import Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int = 0
    page: int = 1
    perPage: int = 20
    totalPages: int = 0


class StandardResponse(BaseModel, Generic[T]):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    status: str = "success"
    message: str = ""
    data: T
    meta: Optional[PaginationMeta] = None


def success_response(data, message: str = "Success", meta: Optional[PaginationMeta] = None) -> dict:
    return {"status": "success", "message": message, "data": data, "meta": meta}
