from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_staff, get_leave_approver
from app.core.scope import BusinessScope, get_scope
from app.core.pagination import ListQueryParams
from app.dependencies import get_db
from app.models import Staff
from app.schemas.v1.common import success_response
from app.schemas.v1.leave import LeaveApplicationCreate, LeaveApplicationRead, ReviewDecision
from app.services.v1.leave_service import LeaveService, current_year


router = APIRouter(prefix="/leave", tags=["leave"])
service = LeaveService()


@router.get("/me/balance")
def get_my_balance(
    year: int | None = None,
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    balance = service.balance(db, staff.id, year or current_year())
    return success_response(balance, message="Leave balance retrieved successfully")


@router.get("/me/applications")
def list_my_applications(
    status: str | None = None,
    year: int | None = None,
    params: ListQueryParams = Depends(),
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    items, meta = service.list(db, params, staff_id=staff.id, status=status, year=year)
    data = [LeaveApplicationRead.model_validate(item) for item in items]
    return success_response(data, message="Leave applications retrieved successfully", meta=meta)


@router.post("/applications")
def apply_for_leave(
    payload: LeaveApplicationCreate,
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    application = service.apply(db, staff, payload)
    return success_response(LeaveApplicationRead.model_validate(application), message="Leave application submitted")


@router.post("/applications/{application_id}/cancel")
def cancel_application(
    application_id: int,
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    application = service.cancel(db, staff, application_id)
    return success_response(LeaveApplicationRead.model_validate(application), message="Leave application cancelled")


@router.get("/applications")
def list_applications(
    status: str | None = None,
    year: int | None = None,
    staff_id: int | None = None,
    branch_id: int | None = None,
    params: ListQueryParams = Depends(),
    _approver: Staff = Depends(get_leave_approver),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    scope.check_branch(db, branch_id)
    items, meta = service.list(
        db, params, staff_id=staff_id, status=status, year=year, branch_id=branch_id, scope=scope
    )
    data = [LeaveApplicationRead.model_validate(item) for item in items]
    return success_response(data, message="Leave applications retrieved successfully", meta=meta)


@router.get("/balances/{staff_id}")
def get_staff_balance(
    staff_id: int,
    year: int | None = None,
    _approver: Staff = Depends(get_leave_approver),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    scope.check_staff(db, staff_id)
    balance = service.balance(db, staff_id, year or current_year())
    return success_response(balance, message="Leave balance retrieved successfully")


@router.post("/applications/{application_id}/approve")
def approve_application(
    application_id: int,
    payload: ReviewDecision | None = None,
    _approver: Staff = Depends(get_leave_approver),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    application = service.review(db, scope, application_id, True, payload.comment if payload else None)
    return success_response(LeaveApplicationRead.model_validate(application), message="Leave application approved")


@router.post("/applications/{application_id}/reject")
def reject_application(
    application_id: int,
    payload: ReviewDecision,
    _approver: Staff = Depends(get_leave_approver),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    application = service.review(db, scope, application_id, False, payload.comment)
    return success_response(LeaveApplicationRead.model_validate(application), message="Leave application rejected")
