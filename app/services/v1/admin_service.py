from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Admin, AdminLogin, AdminRole
from app.core.pagination import ListQueryParams, apply_search, apply_sorting, paginate
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.v1.admin import AdminCreate, AdminLoginRequest


class AdminService:
    def login(self, db: Session, payload: AdminLoginRequest):
        admin = db.scalar(select(Admin).where(Admin.email == payload.email))
        if admin is None or not admin.is_active or not verify_password(payload.password, admin.hashed_password):
            if admin is not None:
                admin.failed_login_attempts += 1
                db.add(AdminLogin(admin_id=admin.id, login_status="FAILED", failure_reason="Invalid credentials"))
                db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid admin credentials")

        now = datetime.now(timezone.utc)
        admin.last_login_at = now
        admin.failed_login_attempts = 0
        db.add(AdminLogin(admin_id=admin.id, login_time=now, login_status="SUCCESS"))
        db.commit()
        return {
            "access_token": create_access_token({"sub": str(admin.id), "user_type": "admin"}),
            "token_type": "bearer",
            "admin": admin,
        }

    def create(self, db: Session, payload: AdminCreate):
        if db.scalar(select(Admin).where((Admin.email == payload.email) | (Admin.username == payload.username))):
            raise HTTPException(status_code=409, detail="Admin email or username already exists")
        admin = Admin(
            fullname=payload.fullname,
            username=payload.username,
            email=payload.email,
            phone_number=payload.phone_number,
            profile_image=payload.profile_image,
            hashed_password=hash_password(payload.password),
            admin_role_id=payload.admin_role_id,
            is_superadmin=payload.is_superadmin,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)
        return admin

    def list(self, db: Session, params: ListQueryParams):
        stmt = select(Admin)
        stmt = apply_search(stmt, Admin, params.search, ["fullname", "username", "email"])
        stmt = apply_sorting(stmt, Admin, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def get(self, db: Session, admin_id: UUID):
        admin = db.get(Admin, admin_id)
        if admin is None:
            raise HTTPException(status_code=404, detail="Admin not found")
        return admin

    def list_roles(self, db: Session, params: ListQueryParams):
        stmt = select(AdminRole)
        stmt = apply_search(stmt, AdminRole, params.search, ["name"])
        stmt = apply_sorting(stmt, AdminRole, params.sort_by, params.sort_order, default_field="name")
        return paginate(db, stmt, params)

    def get_role(self, db: Session, role_id: UUID):
        role = db.get(AdminRole, role_id)
        if role is None:
            raise HTTPException(status_code=404, detail="Admin role not found")
        return role

    def get_role_by_name(self, db: Session, name: str):
        role = db.scalar(select(AdminRole).where(AdminRole.name == name))
        if role is None:
            raise HTTPException(status_code=404, detail="Admin role not found")
        return role