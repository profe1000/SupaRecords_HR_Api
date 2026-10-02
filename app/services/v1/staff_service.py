from __future__ import annotations

from datetime import datetime, timezone
import secrets
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Business, BusinessBranch, Staff, StaffLogin, StaffRole
from app.core.auth import can_filter_branches, role_name_rank, role_rank
from app.core.pagination import ListQueryParams, apply_search, apply_sorting, paginate
from app.core.scope import BusinessScope
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.v1.staff import (
    StaffChangePassword,
    StaffCreate,
    StaffCreateResponse,
    StaffLoginRequest,
    StaffPasswordReset,
    StaffPasswordResetResponse,
    StaffUpdate,
)
from app.services.v1.email_service import send_password_reset_email, send_welcome_email
from app.services.v1.leave_service import LeaveService, current_year


class StaffService:
    def _get_or_create_hq_branch(self, db: Session, business_name: str) -> BusinessBranch:
        business = db.scalar(
            select(Business).where(Business.business_name == business_name)
        )
        if business is None:
            business = Business(business_name=business_name, status="ACTIVE")
            db.add(business)
            db.flush()

        branch = db.scalar(
            select(BusinessBranch).where(
                BusinessBranch.business_id == business.id,
                BusinessBranch.branch_name == "HQ Branch",
            )
        )
        if branch is None:
            branch = BusinessBranch(
                business_id=business.id,
                branch_name="HQ Branch",
                status="ACTIVE",
            )
            db.add(branch)
            db.flush()
        return branch

    def _get_branch(self, db: Session, branch_id: int) -> BusinessBranch:
        branch = db.get(BusinessBranch, branch_id)
        if branch is None or branch.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Branch not found")
        return branch

    def login(self, db: Session, payload: StaffLoginRequest):
        staff = db.scalar(select(Staff).where(Staff.email == payload.email))
        if staff is None or not staff.password_hash or not verify_password(payload.password, staff.password_hash):
            if staff is not None:
                db.add(StaffLogin(staff_id=staff.id, login_time=datetime.now(timezone.utc), status="FAILED"))
                db.commit()
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid staff credentials")
        db.add(StaffLogin(staff_id=staff.id, login_time=datetime.now(timezone.utc), status="SUCCESS"))
        db.commit()
        return {
            "access_token": create_access_token({"sub": str(staff.id), "user_type": "staff"}),
            "token_type": "bearer",
            "staff": staff,
        }

    def create(self, db: Session, payload: StaffCreate):
        if db.scalar(select(Staff).where(Staff.email == payload.email)):
            raise HTTPException(status_code=409, detail="Staff email already exists")
        branch = self._get_branch(db, payload.branch_id)
        business = db.get(Business, branch.business_id)
        staff = Staff(
            first_name=payload.first_name,
            last_name=payload.last_name,
            email=payload.email,
            phone=payload.phone,
            department=payload.department,
            branch_id=payload.branch_id,
            staff_role_id=payload.staff_role_id,
            password_hash=hash_password(payload.password),
            status="ACTIVE",
        )
        db.add(staff)
        db.flush()
        if payload.leave_days is not None:
            LeaveService().set_allowance(
                db, staff.id, payload.leave_year or current_year(), payload.leave_days, commit=False
            )
        db.commit()
        db.refresh(staff)
        email_result = send_welcome_email(
            staff.email,
            staff.first_name,
            staff.last_name,
            business_name=business.business_name if business else branch.branch_name,
            branch_name=branch.branch_name,
        )
        response = StaffCreateResponse.model_validate(staff).model_dump()
        response["email_sent"] = email_result["sent"]
        response["email_message_id"] = email_result["message_id"]
        response["email_error"] = email_result["error"]
        return response

    # --- role guards ----------------------------------------------------------

    def guard_role_assignment(self, db: Session, actor: Staff, role_id: UUID | None) -> None:
        """Nobody can hand out a role higher than their own."""
        if role_id is None:
            return
        role = self.get_role(db, role_id)
        if role_name_rank(role.name) > role_rank(actor):
            raise HTTPException(status_code=403, detail="You cannot assign a role higher than your own")

    def guard_edit(self, db: Session, actor: Staff, target: Staff, values: dict) -> None:
        if target.id != actor.id and role_rank(target) > role_rank(actor):
            raise HTTPException(status_code=403, detail="You cannot edit someone with a higher role than yours")
        if "staff_role_id" in values and values["staff_role_id"] != target.staff_role_id:
            if target.id == actor.id:
                raise HTTPException(status_code=403, detail="You cannot change your own role")
            self.guard_role_assignment(db, actor, values["staff_role_id"])

    def assignable_roles(self, db: Session, actor: Staff) -> list[StaffRole]:
        roles = db.scalars(
            select(StaffRole).where(StaffRole.is_active.is_(True)).order_by(StaffRole.name)
        ).all()
        return [role for role in roles if role_name_rank(role.name) <= role_rank(actor)]

    def update(self, db: Session, staff_id: int, payload: StaffUpdate, actor: Staff):
        actor_id = actor.id
        staff = self.get(db, staff_id)
        values = payload.model_dump(exclude_unset=True)
        self.guard_edit(db, actor, staff, values)
        leave_days = values.pop("leave_days", None)
        leave_year = values.pop("leave_year", None)
        password = values.pop("password", None)

        if values.get("email") and values["email"] != staff.email:
            if db.scalar(select(Staff).where(Staff.email == values["email"], Staff.id != staff.id)):
                raise HTTPException(status_code=409, detail="Staff email already exists")
        if "branch_id" in values and values["branch_id"] is None:
            raise HTTPException(status_code=400, detail="Every staff member must belong to a branch")
        if values.get("branch_id") is not None:
            self._get_branch(db, values["branch_id"])

        for field, value in values.items():
            setattr(staff, field, value)
        if password:
            staff.password_hash = hash_password(password)
        staff.updated_by = actor_id
        if leave_days is not None:
            LeaveService().set_allowance(
                db, staff.id, leave_year or current_year(), leave_days, actor_id=actor_id, commit=False
            )
        db.commit()
        db.refresh(staff)
        return staff

    def change_password(self, db: Session, staff: Staff, payload: StaffChangePassword) -> None:
        if not staff.password_hash or not verify_password(payload.current_password, staff.password_hash):
            raise HTTPException(status_code=400, detail="Current password is incorrect")
        if payload.current_password == payload.new_password:
            raise HTTPException(status_code=400, detail="New password must be different from the current password")
        staff.password_hash = hash_password(payload.new_password)
        staff.updated_by = staff.id
        db.commit()

    def reset_password(
        self, db: Session, scope: BusinessScope, staff_id: int, payload: StaffPasswordReset
    ) -> StaffPasswordResetResponse:
        target = scope.check_staff(db, staff_id)
        if role_rank(target) > role_rank(scope.staff):
            raise HTTPException(
                status_code=403,
                detail="You cannot reset the password of someone with a higher role than yours",
            )
        new_password = payload.new_password or self._temporary_password()
        target.password_hash = hash_password(new_password)
        target.updated_by = scope.staff.id
        db.commit()

        email_result = {"sent": False, "error": None}
        if payload.send_email:
            business = db.get(Business, scope.business_id)
            email_result = send_password_reset_email(
                target.email, target.first_name, business.business_name, new_password
            )
        return StaffPasswordResetResponse(
            staff_id=target.id,
            temporary_password=new_password,
            email_sent=email_result["sent"],
            email_error=email_result["error"],
        )

    @staticmethod
    def _temporary_password() -> str:
        # 10 characters, no look-alikes (0/O, 1/l/I) so it is easy to read out or type.
        alphabet = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789"
        return "".join(secrets.choice(alphabet) for _ in range(10))

    def register(
        self,
        db: Session,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        business_name: str,
    ):
        branch = self._get_or_create_hq_branch(db, business_name)
        payload = StaffCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            branch_id=branch.id,
        )
        return self.create(db, payload)

    def list(self, db: Session, params: ListQueryParams, scope: BusinessScope, branch_id: int | None = None):
        stmt = select(Staff).where(Staff.deleted_at.is_(None), scope.staff_filter(Staff.branch_id, branch_id))
        stmt = apply_search(stmt, Staff, params.search, ["first_name", "last_name", "email", "phone", "department"])
        stmt = apply_sorting(stmt, Staff, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def get(self, db: Session, staff_id: int):
        staff = db.get(Staff, staff_id)
        if staff is None:
            raise HTTPException(status_code=404, detail="Staff not found")
        return staff

    def get_branch(self, db: Session, staff_id: int):
        staff = self.get(db, staff_id)
        if staff.branch_id is None:
            raise HTTPException(status_code=404, detail="Staff is not assigned to any branch")

        branch = db.get(BusinessBranch, staff.branch_id)
        if branch is None:
            raise HTTPException(status_code=404, detail="Branch not found")
        return branch

    def list_branches(self, db: Session, staff_id: int):
        staff = self.get(db, staff_id)
        if staff.branch_id is None:
            return []

        branch = db.get(BusinessBranch, staff.branch_id)
        return [branch] if branch is not None else []

    def business_context(self, db: Session, scope: BusinessScope) -> dict:
        business = db.get(Business, scope.business_id)
        stmt = select(BusinessBranch).where(
            BusinessBranch.business_id == scope.business_id, BusinessBranch.deleted_at.is_(None)
        )
        if scope.locked_branch_id is not None:
            stmt = stmt.where(BusinessBranch.id == scope.locked_branch_id)
        branches = db.scalars(stmt.order_by(BusinessBranch.branch_name)).all()
        return {
            "business": {"id": business.id, "business_name": business.business_name},
            "current_branch_id": scope.staff.branch_id,
            # Super Admin / General Admin: whole business with a branch filter.
            # Everyone else: only `locked_branch_id`, and `branches` holds just that branch.
            "can_filter_branches": can_filter_branches(scope.staff),
            "locked_branch_id": scope.locked_branch_id,
            "branches": [
                {"id": b.id, "branch_name": b.branch_name, "city": b.city, "state": b.state} for b in branches
            ],
        }

    def colleagues(self, db: Session, staff_id: int) -> list[dict]:
        """Names of active staff in the same business (used by the public onboarding form)."""
        staff = self.get(db, staff_id)
        if staff.branch is None:
            return []
        scope = BusinessScope(staff=staff, business_id=staff.branch.business_id)
        rows = db.scalars(
            select(Staff)
            .where(Staff.deleted_at.is_(None), scope.staff_filter(Staff.branch_id))
            .order_by(Staff.first_name, Staff.last_name)
        ).all()
        return [{"id": s.id, "first_name": s.first_name, "last_name": s.last_name} for s in rows]

    def list_roles(self, db: Session, params: ListQueryParams):
        stmt = select(StaffRole)
        stmt = apply_search(stmt, StaffRole, params.search, ["name"])
        stmt = apply_sorting(stmt, StaffRole, params.sort_by, params.sort_order, default_field="name")
        return paginate(db, stmt, params)

    def get_role(self, db: Session, role_id: UUID):
        role = db.get(StaffRole, role_id)
        if role is None:
            raise HTTPException(status_code=404, detail="Staff role not found")
        return role

    def get_role_by_name(self, db: Session, name: str):
        role = db.scalar(select(StaffRole).where(StaffRole.name == name))
        if role is None:
            raise HTTPException(status_code=404, detail="Staff role not found")
        return role