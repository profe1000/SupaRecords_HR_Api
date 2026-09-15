from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams, apply_search, apply_sorting, paginate
from app.models import Business
from app.schemas.v1.business import BusinessCreate, BusinessUpdate


class BusinessService:
    def list(self, db: Session, params: ListQueryParams):
        stmt = select(Business).where(Business.deleted_at.is_(None))
        stmt = apply_search(
            stmt,
            Business,
            params.search,
            ["business_name", "email", "phone_number"],
        )
        stmt = apply_sorting(stmt, Business, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def get(self, db: Session, business_id: int) -> Business:
        business = db.get(Business, business_id)
        if business is None or business.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Business not found")
        return business

    def create(self, db: Session, payload: BusinessCreate) -> Business:
        business = Business(**payload.model_dump(exclude_none=True))
        db.add(business)
        db.commit()
        db.refresh(business)
        return business

    def update(
        self,
        db: Session,
        business_id: int,
        payload: BusinessUpdate,
    ) -> Business:
        business = self.get(db, business_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(business, field, value)
        db.commit()
        db.refresh(business)
        return business

    def delete(self, db: Session, business_id: int) -> dict[str, int | bool]:
        business = self.get(db, business_id)
        business.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return {"deleted": True, "id": business_id}