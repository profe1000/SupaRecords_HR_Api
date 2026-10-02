from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.auth import get_current_staff, get_request_approver
from app.core.scope import BusinessScope, get_scope
from app.core.pagination import ListQueryParams
from app.dependencies import get_db
from app.models import Staff
from app.schemas.v1.common import success_response
from app.schemas.v1.leave import ReviewDecision
from app.schemas.v1.staff_request import StaffRequestCreate, StaffRequestRead
from app.services.v1.staff_request_service import StaffRequestService


router = APIRouter(prefix="/requests", tags=["requests"])
service = StaffRequestService()


@router.get("/me")
def list_my_requests(
    status: str | None = None,
    request_type: str | None = None,
    params: ListQueryParams = Depends(),
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    items, meta = service.list(db, params, staff_id=staff.id, status=status, request_type=request_type)
    data = [StaffRequestRead.model_validate(item) for item in items]
    return success_response(data, message="Requests retrieved successfully", meta=meta)


@router.post("/")
def submit_request(
    payload: StaffRequestCreate,
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    request = service.create(db, staff, payload)
    return success_response(StaffRequestRead.model_validate(request), message="Request submitted")


@router.post("/{request_id}/cancel")
def cancel_request(
    request_id: int,
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    request = service.cancel(db, staff, request_id)
    return success_response(StaffRequestRead.model_validate(request), message="Request cancelled")


@router.get("/")
def list_requests(
    status: str | None = None,
    request_type: str | None = None,
    staff_id: int | None = None,
    branch_id: int | None = None,
    params: ListQueryParams = Depends(),
    _approver: Staff = Depends(get_request_approver),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    scope.check_branch(db, branch_id)
    items, meta = service.list(
        db,
        params,
        staff_id=staff_id,
        status=status,
        request_type=request_type,
        branch_id=branch_id,
        scope=scope,
    )
    data = [StaffRequestRead.model_validate(item) for item in items]
    return success_response(data, message="Requests retrieved successfully", meta=meta)


@router.post("/{request_id}/approve")
def approve_request(
    request_id: int,
    payload: ReviewDecision | None = None,
    _approver: Staff = Depends(get_request_approver),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    request = service.review(db, scope, request_id, True, payload.comment if payload else None)
    return success_response(StaffRequestRead.model_validate(request), message="Request approved")


@router.post("/{request_id}/reject")
def reject_request(
    request_id: int,
    payload: ReviewDecision,
    _approver: Staff = Depends(get_request_approver),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    request = service.review(db, scope, request_id, False, payload.comment)
    return success_response(StaffRequestRead.model_validate(request), message="Request rejected")
