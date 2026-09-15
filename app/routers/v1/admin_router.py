from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams
from app.dependencies import get_db
from app.schemas.v1.admin import AdminCreate, AdminLoginRequest, AdminRead, AdminRoleRead, AuthResponse
from app.schemas.v1.common import success_response
from app.services.v1.admin_service import AdminService


router = APIRouter(prefix="/admins", tags=["admins"])
service = AdminService()


@router.post("/login", response_model=AuthResponse)
def login(payload: AdminLoginRequest, db: Session = Depends(get_db)):
    return service.login(db, payload)


@router.post("/", response_model=AdminRead)
def create_admin(payload: AdminCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.get("/")
def list_admins(params: ListQueryParams = Depends(), db: Session = Depends(get_db)):
    items, meta = service.list(db, params)
    data = [AdminRead.model_validate(item, from_attributes=True) for item in items]
    return success_response(data, message="Admins retrieved successfully", meta=meta)


@router.get("/roles")
def list_admin_roles(params: ListQueryParams = Depends(), db: Session = Depends(get_db)):
    items, meta = service.list_roles(db, params)
    data = [AdminRoleRead.model_validate(item, from_attributes=True) for item in items]
    return success_response(data, message="Admin roles retrieved successfully", meta=meta)


@router.get("/roles/by-name/{name}")
def get_admin_role_by_name(name: str, db: Session = Depends(get_db)):
    role = service.get_role_by_name(db, name)
    return success_response(AdminRoleRead.model_validate(role, from_attributes=True), message="Admin role retrieved successfully")


@router.get("/roles/{role_id}")
def get_admin_role(role_id: UUID, db: Session = Depends(get_db)):
    role = service.get_role(db, role_id)
    return success_response(AdminRoleRead.model_validate(role, from_attributes=True), message="Admin role retrieved successfully")


@router.get("/{admin_id}")
def get_admin(admin_id: UUID, db: Session = Depends(get_db)):
    admin = service.get(db, admin_id)
    return success_response(AdminRead.model_validate(admin, from_attributes=True), message="Admin retrieved successfully")