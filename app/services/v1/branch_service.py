from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Business, BusinessBranch
from app.core.pagination import ListQueryParams, apply_search, apply_sorting, paginate
from app.schemas.v1.branch import BranchCreate, BranchUpdate


class BranchService:
    def _get_business(self, db: Session, business_id: int) -> Business:
        business = db.get(Business, business_id)
        if business is None:
            raise HTTPException(status_code=404, detail="Business not found")
        return business

    def list(self, db: Session, params: ListQueryParams):
        stmt = select(BusinessBranch).where(BusinessBranch.deleted_at.is_(None))
        stmt = apply_search(stmt, BusinessBranch, params.search, ["branch_name"])
        stmt = apply_sorting(stmt, BusinessBranch, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def get(self, db: Session, branch_id: int):
        branch = db.get(BusinessBranch, branch_id)
        if branch is None or branch.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Branch not found")
        return branch

    def create(self, db: Session, payload: BranchCreate):
        self._get_business(db, payload.business_id)

        branch = BusinessBranch(**payload.model_dump(exclude_none=True))
        db.add(branch)
        db.commit()
        db.refresh(branch)
        return branch

    def update(self, db: Session, branch_id: int, payload: BranchUpdate):
        branch = self.get(db, branch_id)

        if payload.business_id is not None:
            self._get_business(db, payload.business_id)

        for field, value in payload.model_dump(exclude_unset=True, exclude_none=True).items():
            setattr(branch, field, value)

        db.commit()
        db.refresh(branch)
        return branch

    def delete(self, db: Session, branch_id: int):
        branch = self.get(db, branch_id)
        branch.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return {"deleted": True, "id": branch_id}

    def list_by_business(self, db: Session, business_id: int, params: ListQueryParams):
        self._get_business(db, business_id)
        stmt = select(BusinessBranch).where(
            BusinessBranch.business_id == business_id,
            BusinessBranch.deleted_at.is_(None),
        )
        stmt = apply_search(stmt, BusinessBranch, params.search, ["branch_name"])
        stmt = apply_sorting(stmt, BusinessBranch, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)
