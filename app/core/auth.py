from __future__ import annotations

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.dependencies import get_db
from app.models import Staff

# Staff role names (see scripts/seed.py) with management access: they see the whole
# admin area and approve leave and requests. Every other role only gets self-service
# pages (tasks, leave applications, request submission).
MANAGER_ROLE_NAMES = {
    "Super Admin (Staff)",
    "General Admin (Staff)",
    "HR Manager(Staff)",
}
# Request types that must include an amount.
FINANCIAL_REQUEST_TYPES = {"CASH_ADVANCE", "LOAN", "EXPENSE_REIMBURSEMENT"}


def get_current_staff(
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
) -> Staff:
    if not authorization or " " not in authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be in the format: Bearer <token>",
        )
    scheme, token = authorization.split(" ", 1)
    payload = decode_access_token(token) if scheme.lower() == "bearer" else None
    if payload is None or payload.get("user_type") != "staff":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired staff token",
        )
    try:
        staff = db.get(Staff, int(payload.get("sub")))
    except (TypeError, ValueError):
        staff = None
    if staff is None or staff.deleted_at is not None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Staff not found")
    return staff


def _role_name(staff: Staff) -> str | None:
    return staff.staff_role.name if staff.staff_role is not None else None


# Higher number = more authority. Used to stop e.g. HR resetting a Super Admin's password.
ROLE_RANK = {
    "Super Admin (Staff)": 3,
    "General Admin (Staff)": 2,
    "HR Manager(Staff)": 1,
}


# Roles that see the whole business and can filter by branch; everyone else is
# limited to their own branch.
BUSINESS_WIDE_ROLE_NAMES = {"Super Admin (Staff)", "General Admin (Staff)"}


def role_rank(staff: Staff) -> int:
    return ROLE_RANK.get(_role_name(staff), 0)


def role_name_rank(role_name: str | None) -> int:
    return ROLE_RANK.get(role_name, 0)


def can_filter_branches(staff: Staff) -> bool:
    return _role_name(staff) in BUSINESS_WIDE_ROLE_NAMES


def is_manager(staff: Staff) -> bool:
    return _role_name(staff) in MANAGER_ROLE_NAMES


can_approve_leave = is_manager
can_approve_requests = is_manager


def get_leave_approver(staff: Staff = Depends(get_current_staff)) -> Staff:
    if not can_approve_leave(staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to approve leave")
    return staff


def get_request_approver(staff: Staff = Depends(get_current_staff)) -> Staff:
    if not can_approve_requests(staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You are not allowed to approve requests")
    return staff


def get_manager(staff: Staff = Depends(get_current_staff)) -> Staff:
    if not is_manager(staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This action is limited to Admin and HR")
    return staff
