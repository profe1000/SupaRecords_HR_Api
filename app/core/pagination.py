from __future__ import annotations

from typing import Any, Sequence

from fastapi import Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.schemas.v1.common import PaginationMeta


class ListQueryParams:
    """Common query params for list endpoints: pagination, sorting and free-text search."""

    def __init__(
        self,
        page: int = Query(1, ge=1, description="Page number"),
        perPage: int = Query(20, ge=1, le=200, description="Items per page"),
        sort_by: str | None = Query(None, description="Field name to sort by"),
        sort_order: str = Query("desc", pattern="^(?i)(asc|desc)$", description="Sort direction: asc or desc"),
        search: str | None = Query(None, description="Free text search"),
    ):
        self.page = page
        self.per_page = perPage
        self.sort_by = sort_by
        self.sort_order = sort_order.lower()
        self.search = search


def apply_search(stmt: Select, model: type, search: str | None, fields: Sequence[str]) -> Select:
    if not search or not fields:
        return stmt
    conditions = []
    for field_name in fields:
        column = getattr(model, field_name, None)
        if column is not None:
            conditions.append(column.ilike(f"%{search}%"))
    if conditions:
        stmt = stmt.where(or_(*conditions))
    return stmt


def apply_sorting(stmt: Select, model: type, sort_by: str | None, sort_order: str, default_field: str = "created_at") -> Select:
    field_name = sort_by if sort_by and hasattr(model, sort_by) else default_field
    column = getattr(model, field_name, None)
    if column is None:
        return stmt
    return stmt.order_by(column.asc() if sort_order == "asc" else column.desc())


def paginate(db: Session, stmt: Select, params: ListQueryParams) -> tuple[Sequence[Any], PaginationMeta]:
    total = db.scalar(select(func.count()).select_from(stmt.order_by(None).subquery())) or 0
    offset = (params.page - 1) * params.per_page
    items = db.scalars(stmt.offset(offset).limit(params.per_page)).all()
    total_pages = (total + params.per_page - 1) // params.per_page if params.per_page else 0
    meta = PaginationMeta(total=total, page=params.page, perPage=params.per_page, totalPages=total_pages)
    return items, meta
