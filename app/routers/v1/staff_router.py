from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import (
    can_approve_leave,
    can_approve_requests,
    can_filter_branches,
    get_current_staff,
    get_leave_approver,
    is_manager,
)
from app.core.scope import BusinessScope, get_manager_scope, get_scope
from app.core.pagination import ListQueryParams
from app.core.security import decode_access_token
from app.dependencies import get_db
from app.models import Staff
from app.schemas.v1.leave import LeaveAllowanceRead, LeaveAllowanceUpsert
from app.schemas.v1.common import success_response
from app.schemas.v1.onboarding import (
    StaffOnboardingRead,
    StaffOnboardingUpdate,
)
from app.schemas.v1.staff import (
    StaffAuthResponse,
    StaffBranchRead,
    StaffChangePassword,
    StaffCreate,
    StaffCreateResponse,
    StaffLoginRequest,
    StaffPasswordReset,
    StaffPermissions,
    StaffRead,
    StaffRoleRead,
    StaffUpdate,
)
from app.services.v1.leave_service import LeaveService
from app.services.v1.staff_service import StaffService
from app.services.v1.onboarding_service import OnboardingService


router = APIRouter(prefix="/staffs", tags=["staffs"])
service = StaffService()
onboarding_service = OnboardingService()
leave_service = LeaveService()


def resolve_staff_id_from_request(
    staff_id: int | None = None,
    authorization: str | None = Header(default=None, alias="Authorization"),
) -> int:
    if staff_id is not None:
        return staff_id

    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="staff_id or bearer token is required",
        )

    try:
        scheme, token = authorization.split(" ", 1)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header must be in the format: Bearer <token>",
        ) from exc

    if scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization scheme must be Bearer",
        )

    payload = decode_access_token(token)
    if payload is None or payload.get("user_type") != "staff":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired staff token",
        )

    try:
        return int(payload.get("sub"))
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token does not contain a valid staff id",
        ) from exc


@router.post("/login", response_model=StaffAuthResponse)
def login(payload: StaffLoginRequest, db: Session = Depends(get_db)):
    return service.login(db, payload)


@router.post("/", response_model=StaffCreateResponse)
def create_staff(
    payload: StaffCreate,
    scope: BusinessScope = Depends(get_manager_scope),
    db: Session = Depends(get_db),
):
    scope.check_branch(db, payload.branch_id)
    service.guard_role_assignment(db, scope.staff, payload.staff_role_id)
    return service.create(db, payload)


@router.get("/")
def list_staff(
    branch_id: int | None = None,
    params: ListQueryParams = Depends(),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    scope.check_branch(db, branch_id)
    items, meta = service.list(db, params, scope, branch_id=branch_id)
    data = [StaffRead.model_validate(item, from_attributes=True) for item in items]
    return success_response(data, message="Staff retrieved successfully", meta=meta)


@router.get("/roles")
def list_staff_roles(params: ListQueryParams = Depends(), db: Session = Depends(get_db)):
    items, meta = service.list_roles(db, params)
    data = [StaffRoleRead.model_validate(item, from_attributes=True) for item in items]
    return success_response(data, message="Staff roles retrieved successfully", meta=meta)


@router.get("/roles/by-name/{name}")
def get_staff_role_by_name(name: str, db: Session = Depends(get_db)):
    role = service.get_role_by_name(db, name)
    return success_response(StaffRoleRead.model_validate(role, from_attributes=True), message="Staff role retrieved successfully")


@router.get("/roles/{role_id}")
def get_staff_role(role_id: UUID, db: Session = Depends(get_db)):
    role = service.get_role(db, role_id)
    return success_response(StaffRoleRead.model_validate(role, from_attributes=True), message="Staff role retrieved successfully")


@router.get("/me/permissions")
def get_my_permissions(staff: Staff = Depends(get_current_staff)):
    data = StaffPermissions(
        is_manager=is_manager(staff),
        can_filter_branches=can_filter_branches(staff),
        can_approve_leave=can_approve_leave(staff),
        can_approve_requests=can_approve_requests(staff),
    )
    return success_response(data, message="Staff permissions retrieved successfully")


@router.get("/me/assignable-roles")
def list_my_assignable_roles(scope: BusinessScope = Depends(get_manager_scope), db: Session = Depends(get_db)):
    """Roles the current user may give to staff (never higher than their own)."""
    data = [StaffRoleRead.model_validate(role, from_attributes=True) for role in service.assignable_roles(db, scope.staff)]
    return success_response(data, message="Assignable roles retrieved successfully")


@router.get("/me/business")
def get_my_business(scope: BusinessScope = Depends(get_scope), db: Session = Depends(get_db)):
    return success_response(service.business_context(db, scope), message="Business retrieved successfully")


@router.post("/me/change-password")
def change_my_password(
    payload: StaffChangePassword,
    staff: Staff = Depends(get_current_staff),
    db: Session = Depends(get_db),
):
    service.change_password(db, staff, payload)
    return success_response({"changed": True}, message="Password changed successfully")


@router.get("/branch")
def get_current_staff_branch(
    staff_id: int | None = None,
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    resolved_staff_id = resolve_staff_id_from_request(staff_id, authorization)
    branch = service.get_branch(db, resolved_staff_id)
    return success_response(StaffBranchRead.model_validate(branch, from_attributes=True), message="Staff branch retrieved successfully")


@router.get("/branches")
def list_current_staff_branches(
    staff_id: int | None = None,
    authorization: str | None = Header(default=None, alias="Authorization"),
    db: Session = Depends(get_db),
):
    resolved_staff_id = resolve_staff_id_from_request(staff_id, authorization)
    branches = service.list_branches(db, resolved_staff_id)
    data = [StaffBranchRead.model_validate(item, from_attributes=True) for item in branches]
    return success_response(data, message="Staff branches retrieved successfully")


@router.get("/{staff_id}/branch")
def get_staff_branch(staff_id: int, db: Session = Depends(get_db)):
    branch = service.get_branch(db, staff_id)
    return success_response(StaffBranchRead.model_validate(branch, from_attributes=True), message="Staff branch retrieved successfully")


@router.get("/{staff_id}/branches")
def list_staff_branches(staff_id: int, db: Session = Depends(get_db)):
    branches = service.list_branches(db, staff_id)
    data = [StaffBranchRead.model_validate(item, from_attributes=True) for item in branches]
    return success_response(data, message="Staff branches retrieved successfully")


@router.get("/by-branch/{branch_id}")
def list_staff_by_branch(
    branch_id: int,
    params: ListQueryParams = Depends(),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    scope.check_branch(db, branch_id)
    items, meta = service.list(db, params, scope, branch_id=branch_id)
    data = [StaffRead.model_validate(item, from_attributes=True) for item in items]
    return success_response(data, message="Staff retrieved successfully", meta=meta)


@router.get("/{staff_id}/onboarding/colleagues")
def list_onboarding_colleagues(staff_id: int, db: Session = Depends(get_db)):
    """Public: names for the 'reporting manager' picker on the onboarding link."""
    return success_response(service.colleagues(db, staff_id), message="Colleagues retrieved successfully")


@router.get("/{staff_id}/onboarding")
def get_staff_onboarding(staff_id: int, db: Session = Depends(get_db)):
    onboarding = onboarding_service.get(db, staff_id)
    data = StaffOnboardingRead.model_validate(onboarding)
    return success_response(data, message="Staff onboarding form retrieved successfully")


@router.put("/{staff_id}/onboarding", response_model=StaffOnboardingRead)
def upsert_staff_onboarding(
    staff_id: int,
    payload: StaffOnboardingUpdate,
    db: Session = Depends(get_db),
):
    return onboarding_service.upsert(db, staff_id, payload)


@router.get("/{staff_id}")
def get_staff(staff_id: int, scope: BusinessScope = Depends(get_scope), db: Session = Depends(get_db)):
    staff = scope.check_staff(db, staff_id)
    return success_response(StaffRead.model_validate(staff, from_attributes=True), message="Staff retrieved successfully")


@router.put("/{staff_id}")
def update_staff(
    staff_id: int,
    payload: StaffUpdate,
    scope: BusinessScope = Depends(get_manager_scope),
    db: Session = Depends(get_db),
):
    scope.check_staff(db, staff_id)
    scope.check_branch(db, payload.branch_id)
    staff = service.update(db, staff_id, payload, actor=scope.staff)
    return success_response(StaffRead.model_validate(staff, from_attributes=True), message="Staff updated successfully")


@router.post("/{staff_id}/reset-password")
def reset_staff_password(
    staff_id: int,
    payload: StaffPasswordReset,
    scope: BusinessScope = Depends(get_manager_scope),
    db: Session = Depends(get_db),
):
    result = service.reset_password(db, scope, staff_id, payload)
    message = "Password reset" + (" and emailed to the staff member" if result.email_sent else "")
    return success_response(result, message=message)


@router.get("/{staff_id}/leave-allowances")
def list_staff_leave_allowances(
    staff_id: int,
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    scope.check_staff(db, staff_id)
    if staff_id != scope.staff.id and not is_manager(scope.staff):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You can only view your own leave allowance")
    data = [LeaveAllowanceRead.model_validate(item) for item in leave_service.list_allowances(db, staff_id)]
    return success_response(data, message="Leave allowances retrieved successfully")


@router.put("/{staff_id}/leave-allowances/{year}")
def set_staff_leave_allowance(
    staff_id: int,
    year: int,
    payload: LeaveAllowanceUpsert,
    approver: Staff = Depends(get_leave_approver),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    scope.check_staff(db, staff_id)
    allowance = leave_service.set_allowance(db, staff_id, year, payload.total_days, actor_id=approver.id)
    return success_response(LeaveAllowanceRead.model_validate(allowance), message="Leave allowance saved")
