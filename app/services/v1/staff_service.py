from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Hotel, HotelBranch, Staff, StaffLogin, StaffRole
from app.core.pagination import ListQueryParams, apply_search, apply_sorting, paginate
from app.core.security import create_access_token, hash_password, verify_password
from app.schemas.v1.staff import StaffCreate, StaffCreateResponse, StaffLoginRequest
from app.services.v1.email_service import send_welcome_email


class StaffService:
    def _get_or_create_hq_branch(self, db: Session, hotel_name: str) -> HotelBranch:
        hotel = db.scalar(select(Hotel).where(Hotel.hotel_name == hotel_name))
        if hotel is None:
            hotel = Hotel(hotel_name=hotel_name, status="ACTIVE")
            db.add(hotel)
            db.flush()

        branch = db.scalar(
            select(HotelBranch).where(
                HotelBranch.hotel_id == hotel.id,
                HotelBranch.branch_name == "HQ Branch",
            )
        )
        if branch is None:
            branch = HotelBranch(
                hotel_id=hotel.id,
                branch_name="HQ Branch",
                status="ACTIVE",
            )
            db.add(branch)
            db.flush()
        return branch

    def _get_branch(self, db: Session, branch_id: int) -> HotelBranch:
        branch = db.get(HotelBranch, branch_id)
        if branch is None:
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
        self._get_branch(db, payload.branch_id)
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
        db.commit()
        db.refresh(staff)
        email_result = send_welcome_email(
            staff.email,
            staff.first_name,
            staff.last_name,
        )
        response = StaffCreateResponse.model_validate(staff).model_dump()
        response["email_sent"] = email_result["sent"]
        response["email_message_id"] = email_result["message_id"]
        response["email_error"] = email_result["error"]
        return response

    def register(
        self,
        db: Session,
        first_name: str,
        last_name: str,
        email: str,
        password: str,
        hotel_name: str,
    ):
        branch = self._get_or_create_hq_branch(db, hotel_name)
        payload = StaffCreate(
            first_name=first_name,
            last_name=last_name,
            email=email,
            password=password,
            branch_id=branch.id,
        )
        return self.create(db, payload)

    def list(self, db: Session, params: ListQueryParams, branch_id: int | None = None):
        stmt = select(Staff)
        if branch_id is not None:
            stmt = stmt.where(Staff.branch_id == branch_id)
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

        branch = db.get(HotelBranch, staff.branch_id)
        if branch is None:
            raise HTTPException(status_code=404, detail="Branch not found")
        return branch

    def list_branches(self, db: Session, staff_id: int):
        staff = self.get(db, staff_id)
        if staff.branch_id is None:
            return []

        branch = db.get(HotelBranch, staff.branch_id)
        return [branch] if branch is not None else []

    def list_staff_by_branch(self, db: Session, branch_id: int, params: ListQueryParams):
        branch = db.get(HotelBranch, branch_id)
        if branch is None:
            raise HTTPException(status_code=404, detail="Branch not found")
        stmt = select(Staff).where(Staff.branch_id == branch_id)
        stmt = apply_search(stmt, Staff, params.search, ["first_name", "last_name", "email", "phone", "department"])
        stmt = apply_sorting(stmt, Staff, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

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