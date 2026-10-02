from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import extract, func, select
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams, apply_sorting, paginate
from app.core.scope import BusinessScope
from app.models import LeaveAllowance, LeaveApplication, Staff
from app.schemas.v1.leave import LeaveApplicationCreate, LeaveBalance

ACTIVE_STATUSES = ("PENDING", "APPROVED")


class LeaveService:
    # --- allowance -------------------------------------------------------

    def get_allowance(self, db: Session, staff_id: int, year: int) -> LeaveAllowance | None:
        return db.scalar(
            select(LeaveAllowance).where(
                LeaveAllowance.staff_id == staff_id,
                LeaveAllowance.year == year,
                LeaveAllowance.deleted_at.is_(None),
            )
        )

    def list_allowances(self, db: Session, staff_id: int) -> list[LeaveAllowance]:
        return list(
            db.scalars(
                select(LeaveAllowance)
                .where(LeaveAllowance.staff_id == staff_id, LeaveAllowance.deleted_at.is_(None))
                .order_by(LeaveAllowance.year.desc())
            )
        )

    def set_allowance(
        self, db: Session, staff_id: int, year: int, total_days: int, actor_id: int | None = None, commit: bool = True
    ) -> LeaveAllowance:
        used = self._sum_days(db, staff_id, year, "APPROVED")
        if total_days < used:
            raise HTTPException(
                status_code=400,
                detail=f"Leave allowance for {year} cannot be less than the {used} day(s) already approved",
            )
        allowance = self.get_allowance(db, staff_id, year)
        if allowance is None:
            allowance = LeaveAllowance(staff_id=staff_id, year=year, created_by=actor_id)
            db.add(allowance)
        allowance.total_days = total_days
        allowance.updated_by = actor_id
        if commit:
            db.commit()
            db.refresh(allowance)
        else:
            db.flush()
        return allowance

    # --- balance ---------------------------------------------------------

    def _sum_days(self, db: Session, staff_id: int, year: int, status: str, exclude_id: int | None = None) -> int:
        stmt = select(func.coalesce(func.sum(LeaveApplication.days), 0)).where(
            LeaveApplication.staff_id == staff_id,
            LeaveApplication.status == status,
            LeaveApplication.deleted_at.is_(None),
            extract("year", LeaveApplication.start_date) == year,
        )
        if exclude_id is not None:
            stmt = stmt.where(LeaveApplication.id != exclude_id)
        return int(db.scalar(stmt) or 0)

    def balance(self, db: Session, staff_id: int, year: int) -> LeaveBalance:
        allowance = self.get_allowance(db, staff_id, year)
        total = allowance.total_days if allowance else 0
        used = self._sum_days(db, staff_id, year, "APPROVED")
        pending = self._sum_days(db, staff_id, year, "PENDING")
        return LeaveBalance(
            staff_id=staff_id,
            year=year,
            total_days=total,
            used_days=used,
            pending_days=pending,
            remaining_days=total - used,
        )

    # --- applications ----------------------------------------------------

    def get(self, db: Session, application_id: int, for_update: bool = False) -> LeaveApplication:
        application = db.get(LeaveApplication, application_id, with_for_update=for_update)
        if application is None or application.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Leave application not found")
        return application

    def list(
        self,
        db: Session,
        params: ListQueryParams,
        staff_id: int | None = None,
        status: str | None = None,
        year: int | None = None,
        branch_id: int | None = None,
        scope: BusinessScope | None = None,
    ):
        stmt = select(LeaveApplication).join(Staff, LeaveApplication.staff_id == Staff.id).where(
            LeaveApplication.deleted_at.is_(None)
        )
        if scope is not None:
            stmt = stmt.where(scope.staff_filter(Staff.branch_id, branch_id))
        elif branch_id is not None:
            stmt = stmt.where(Staff.branch_id == branch_id)
        if staff_id is not None:
            stmt = stmt.where(LeaveApplication.staff_id == staff_id)
        if status is not None:
            stmt = stmt.where(LeaveApplication.status == status.upper())
        if year is not None:
            stmt = stmt.where(extract("year", LeaveApplication.start_date) == year)
        if params.search:
            term = f"%{params.search}%"
            stmt = stmt.where(
                Staff.first_name.ilike(term) | Staff.last_name.ilike(term) | Staff.email.ilike(term)
            )
        stmt = apply_sorting(stmt, LeaveApplication, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def apply(self, db: Session, staff: Staff, payload: LeaveApplicationCreate) -> LeaveApplication:
        days = (payload.end_date - payload.start_date).days + 1
        year = payload.start_date.year

        overlapping = db.scalar(
            select(LeaveApplication.id).where(
                LeaveApplication.staff_id == staff.id,
                LeaveApplication.status.in_(ACTIVE_STATUSES),
                LeaveApplication.deleted_at.is_(None),
                LeaveApplication.start_date <= payload.end_date,
                LeaveApplication.end_date >= payload.start_date,
            )
        )
        if overlapping is not None:
            raise HTTPException(status_code=409, detail="You already have a pending or approved leave in this period")

        balance = self.balance(db, staff.id, year)
        available = balance.remaining_days - balance.pending_days
        if days > available:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Insufficient leave balance for {year}: requested {days} day(s), "
                    f"{max(available, 0)} available ({balance.pending_days} day(s) awaiting approval)"
                ),
            )

        application = LeaveApplication(
            staff_id=staff.id,
            leave_type=payload.leave_type,
            start_date=payload.start_date,
            end_date=payload.end_date,
            days=days,
            reason=payload.reason,
            status="PENDING",
            created_by=staff.id,
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return application

    def cancel(self, db: Session, staff: Staff, application_id: int) -> LeaveApplication:
        application = self.get(db, application_id, for_update=True)
        if application.staff_id != staff.id:
            raise HTTPException(status_code=403, detail="You can only cancel your own leave applications")
        if application.status != "PENDING":
            raise HTTPException(status_code=400, detail="Only pending leave applications can be cancelled")
        application.status = "CANCELLED"
        application.updated_by = staff.id
        db.commit()
        db.refresh(application)
        return application

    def review(
        self, db: Session, scope: BusinessScope, application_id: int, approve: bool, comment: str | None
    ) -> LeaveApplication:
        approver = scope.staff
        application = self.get(db, application_id, for_update=True)
        try:
            scope.check_staff(db, application.staff_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail="Leave application not found")
        if application.status != "PENDING":
            raise HTTPException(status_code=400, detail=f"Leave application is already {application.status.lower()}")
        if application.staff_id == approver.id:
            raise HTTPException(status_code=403, detail="You cannot review your own leave application")

        if approve:
            year = application.start_date.year
            allowance = self.get_allowance(db, application.staff_id, year)
            total = allowance.total_days if allowance else 0
            used = self._sum_days(db, application.staff_id, year, "APPROVED")
            if used + application.days > total:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        f"Approving would exceed the staff's {year} allowance: "
                        f"{total - used} day(s) left, {application.days} requested"
                    ),
                )
        elif not comment:
            raise HTTPException(status_code=400, detail="A comment is required when rejecting leave")

        application.status = "APPROVED" if approve else "REJECTED"
        application.reviewed_by = approver.id
        application.reviewed_at = datetime.now(timezone.utc)
        application.review_comment = comment
        application.updated_by = approver.id
        db.commit()
        db.refresh(application)
        return application


def current_year() -> int:
    return date.today().year
