from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams
from app.core.security import decode_access_token
from app.dependencies import get_db
from app.schemas.v1.common import success_response
from app.schemas.v1.onboarding import (
    StaffOnboardingCreate,
    StaffOnboardingRead,
    StaffOnboardingUpdate,
)
from app.schemas.v1.staff import (
    StaffAuthResponse,
    StaffBranchRead,
    StaffCreate,
    StaffCreateResponse,
    StaffLoginRequest,
    StaffRead,
    StaffRoleRead,
)
from app.services.v1.staff_service import StaffService
from app.services.v1.onboarding_service import OnboardingService


router = APIRouter(prefix="/staffs", tags=["staffs"])
service = StaffService()
onboarding_service = OnboardingService()


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
def create_staff(payload: StaffCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.get("/")
def list_staff(branch_id: int | None = None, params: ListQueryParams = Depends(), db: Session = Depends(get_db)):
    items, meta = service.list(db, params, branch_id=branch_id)
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
def list_staff_by_branch(branch_id: int, params: ListQueryParams = Depends(), db: Session = Depends(get_db)):
    items, meta = service.list_staff_by_branch(db, branch_id, params)
    data = [StaffRead.model_validate(item, from_attributes=True) for item in items]
    return success_response(data, message="Staff retrieved successfully", meta=meta)


@router.post("/{staff_id}/onboarding", response_model=StaffOnboardingRead)
def create_staff_onboarding(
    staff_id: int,
    payload: StaffOnboardingCreate,
    db: Session = Depends(get_db),
):
    return onboarding_service.create(db, staff_id, payload)


@router.get("/{staff_id}/onboarding")
def get_staff_onboarding(staff_id: int, db: Session = Depends(get_db)):
    onboarding = onboarding_service.get(db, staff_id)
    data = StaffOnboardingRead.model_validate(onboarding)
    return success_response(data, message="Staff onboarding form retrieved successfully")


@router.put("/{staff_id}/onboarding", response_model=StaffOnboardingRead)
def update_staff_onboarding(
    staff_id: int,
    payload: StaffOnboardingUpdate,
    db: Session = Depends(get_db),
):
    return onboarding_service.update(db, staff_id, payload)


@router.get("/{staff_id}")
def get_staff(staff_id: int, db: Session = Depends(get_db)):
    staff = service.get(db, staff_id)
    return success_response(StaffRead.model_validate(staff, from_attributes=True), message="Staff retrieved successfully")