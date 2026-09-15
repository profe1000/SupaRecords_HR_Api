"""Seed initial roles, accounts, business, branch, and login history.

Usage:
    python scripts/seed.py

Set these variables to override the development defaults:
    DATABASE_URL
    INITIAL_ADMIN_EMAIL, INITIAL_ADMIN_USERNAME, INITIAL_ADMIN_PASSWORD
    INITIAL_STAFF_EMAIL, INITIAL_STAFF_PASSWORD
"""

from __future__ import annotations

from datetime import datetime, timezone
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from sqlalchemy.orm import Session
import bcrypt

from app.db import SessionLocal
from app.models import (
    Admin,
    AdminLogin,
    AdminRole,
    Business,
    BusinessBranch,
    Staff,
    StaffLogin,
    StaffRole,
)


ADMIN_ROLE_NAMES = ("Super Admin", "General Admin", "Manager")
STAFF_ROLE_NAMES = (
    "Super Admin (Staff)",
    "General Admin (Staff)",
    "HR Manager(Staff)",
    "Finance Manager(Staff)",
    "Other (Staff)",
)
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def seed_roles(db: Session, model: type[AdminRole], role_names: tuple[str, ...]):
    roles = {}
    for role_name in role_names:
        role = db.query(model).filter(model.name == role_name).one_or_none()
        if role is None:
            role = model(
                name=role_name,
                title=role_name,
                description=f"{role_name} access level",
                is_system_role=role_name.startswith("Super Admin"),
                is_active=True,
            )
            db.add(role)
            db.flush()
        roles[role_name] = role
    return roles


def seed_business_and_branch(db: Session) -> BusinessBranch:
    business = (
        db.query(Business)
        .filter(Business.business_name == "SupaRecords")
        .one_or_none()
    )
    if business is None:
        business = Business(business_name="SupaRecords", status="ACTIVE")
        db.add(business)
        db.flush()

    branch = (
        db.query(BusinessBranch)
        .filter(
            BusinessBranch.business_id == business.id,
            BusinessBranch.branch_name == "Initial Branch HQ",
        )
        .one_or_none()
    )
    if branch is None:
        branch = BusinessBranch(
            business_id=business.id,
            branch_name="Initial Branch HQ",
            status="ACTIVE",
        )
        db.add(branch)
        db.flush()
    return branch


def seed_admin(db: Session, role: AdminRole) -> Admin:
    email = os.getenv("INITIAL_ADMIN_EMAIL", "admin@suparecords.local")
    username = os.getenv("INITIAL_ADMIN_USERNAME", "superadmin")
    password = os.getenv("INITIAL_ADMIN_PASSWORD", "Admin@123")
    admin = db.query(Admin).filter(Admin.email == email).one_or_none()
    if admin is None:
        admin = Admin(
            fullname="Initial Super Admin",
            username=username,
            email=email,
            hashed_password=hash_password(password),
            is_superadmin=True,
            is_active=True,
            admin_role_id=role.id,
            email_verified=True,
            email_verified_at=datetime.now(timezone.utc),
        )
        db.add(admin)
        db.flush()
    else:
        admin.admin_role_id = role.id
        admin.is_superadmin = True
        admin.is_active = True
    return admin


def seed_staff(db: Session, branch: BusinessBranch, role: StaffRole) -> Staff:
    email = os.getenv("INITIAL_STAFF_EMAIL", "user@suparecords.local")
    password = os.getenv("INITIAL_STAFF_PASSWORD", "Staff@123")
    staff = db.query(Staff).filter(Staff.email == email).one_or_none()
    if staff is None:
        staff = Staff(
            branch_id=branch.id,
            first_name="Initial",
            last_name="Staff",
            email=email,
            password_hash=hash_password(password),
            status="ACTIVE",
            staff_role_id=role.id,
        )
        db.add(staff)
        db.flush()
    else:
        staff.branch_id = branch.id
        staff.staff_role_id = role.id
        staff.status = "ACTIVE"
    return staff


def seed_initial_logins(db: Session, admin: Admin, staff: Staff) -> None:
    login_time = datetime.now(timezone.utc)
    if db.query(AdminLogin).filter(AdminLogin.admin_id == admin.id).first() is None:
        db.add(
            AdminLogin(
                admin_id=admin.id,
                login_time=login_time,
                login_status="SUCCESS",
                device_name="Initial seed",
            )
        )
    if db.query(StaffLogin).filter(StaffLogin.staff_id == staff.id).first() is None:
        db.add(
            StaffLogin(
                staff_id=staff.id,
                login_time=login_time,
                status="SUCCESS",
                device="Initial seed",
            )
        )


def seed() -> None:
    db = SessionLocal()
    try:
        admin_roles = seed_roles(db, AdminRole, ADMIN_ROLE_NAMES)
        staff_roles = seed_roles(db, StaffRole, STAFF_ROLE_NAMES)
        branch = seed_business_and_branch(db)
        admin = seed_admin(db, admin_roles["Super Admin"])
        staff = seed_staff(db, branch, staff_roles["Super Admin (Staff)"])
        seed_initial_logins(db, admin, staff)
        db.commit()
        print("Initial roles, accounts, business, branch, and login history seeded.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
