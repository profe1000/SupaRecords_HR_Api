from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.auth import FINANCIAL_REQUEST_TYPES
from app.core.pagination import ListQueryParams, apply_sorting, paginate
from app.core.scope import BusinessScope
from app.models import Staff, StaffRequest
from app.schemas.v1.staff_request import StaffRequestCreate


class StaffRequestService:
    def get(self, db: Session, request_id: int, for_update: bool = False) -> StaffRequest:
        request = db.get(StaffRequest, request_id, with_for_update=for_update)
        if request is None or request.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Request not found")
        return request

    def list(
        self,
        db: Session,
        params: ListQueryParams,
        staff_id: int | None = None,
        status: str | None = None,
        request_type: str | None = None,
        branch_id: int | None = None,
        scope: BusinessScope | None = None,
    ):
        stmt = select(StaffRequest).join(Staff, StaffRequest.staff_id == Staff.id).where(
            StaffRequest.deleted_at.is_(None)
        )
        if scope is not None:
            stmt = stmt.where(scope.staff_filter(Staff.branch_id, branch_id))
        elif branch_id is not None:
            stmt = stmt.where(Staff.branch_id == branch_id)
        if staff_id is not None:
            stmt = stmt.where(StaffRequest.staff_id == staff_id)
        if status is not None:
            stmt = stmt.where(StaffRequest.status == status.upper())
        if request_type is not None:
            stmt = stmt.where(StaffRequest.request_type == request_type.upper())
        if params.search:
            term = f"%{params.search}%"
            stmt = stmt.where(
                StaffRequest.title.ilike(term)
                | Staff.first_name.ilike(term)
                | Staff.last_name.ilike(term)
                | Staff.email.ilike(term)
            )
        stmt = apply_sorting(stmt, StaffRequest, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def create(self, db: Session, staff: Staff, payload: StaffRequestCreate) -> StaffRequest:
        if payload.request_type in FINANCIAL_REQUEST_TYPES and not payload.amount:
            raise HTTPException(status_code=400, detail="An amount is required for this request type")
        request = StaffRequest(
            staff_id=staff.id,
            request_type=payload.request_type,
            title=payload.title,
            description=payload.description,
            amount=payload.amount,
            status="PENDING",
            created_by=staff.id,
        )
        db.add(request)
        db.commit()
        db.refresh(request)
        return request

    def cancel(self, db: Session, staff: Staff, request_id: int) -> StaffRequest:
        request = self.get(db, request_id, for_update=True)
        if request.staff_id != staff.id:
            raise HTTPException(status_code=403, detail="You can only cancel your own requests")
        if request.status != "PENDING":
            raise HTTPException(status_code=400, detail="Only pending requests can be cancelled")
        request.status = "CANCELLED"
        request.updated_by = staff.id
        db.commit()
        db.refresh(request)
        return request

    def review(
        self, db: Session, scope: BusinessScope, request_id: int, approve: bool, comment: str | None
    ) -> StaffRequest:
        approver = scope.staff
        request = self.get(db, request_id, for_update=True)
        try:
            scope.check_staff(db, request.staff_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail="Request not found")
        if request.status != "PENDING":
            raise HTTPException(status_code=400, detail=f"Request is already {request.status.lower()}")
        if request.staff_id == approver.id:
            raise HTTPException(status_code=403, detail="You cannot review your own request")
        if not approve and not comment:
            raise HTTPException(status_code=400, detail="A comment is required when rejecting a request")

        request.status = "APPROVED" if approve else "REJECTED"
        request.reviewed_by = approver.id
        request.reviewed_at = datetime.now(timezone.utc)
        request.review_comment = comment
        request.updated_by = approver.id
        db.commit()
        db.refresh(request)
        return request
