from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, Optional
import uuid

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    JSON,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

from decimal import Decimal
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class AuditMixin:
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_by: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id", use_alter=True), nullable=True
    )
    updated_by: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id", use_alter=True), nullable=True
    )
    deleted_by: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id", use_alter=True), nullable=True
    )


class AuditTrail(Base):
    __tablename__ = "audit_trail"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    staff_id: Mapped[int | None] = mapped_column(
        ForeignKey("staff.id"), nullable=True
    )
    entity_type: Mapped[str] = mapped_column(String(120), nullable=False)
    entity_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    action: Mapped[str] = mapped_column(String(50), nullable=False)
    old_values: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)
    new_values: Mapped[dict | list | str | None] = mapped_column(JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class InventorySyncMixin:
    inventory_synced: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
    inventory_last_synced_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    inventory_sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)


class AdminRole(Base):
    __tablename__ = "admin_roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    permissions: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    admins: Mapped[list["Admin"]] = relationship(
        "Admin", back_populates="admin_role", foreign_keys="[Admin.admin_role_id]"
    )


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    fullname: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    profile_image: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    is_superadmin: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    admin_role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("admin_roles.id"), nullable=True
    )
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_ip: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    failed_login_attempts: Mapped[int] = mapped_column(Integer, default=0)
    email_verified: Mapped[bool] = mapped_column(Boolean, default=False)
    email_verified_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("admins.id", use_alter=True, name="fk_admins_created_by"), nullable=True
    )
    updated_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("admins.id", use_alter=True, name="fk_admins_updated_by"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    admin_role: Mapped[Optional["AdminRole"]] = relationship(
        "AdminRole", back_populates="admins", foreign_keys=[admin_role_id]
    )
    login_history: Mapped[list["AdminLogin"]] = relationship("AdminLogin", back_populates="admin")


class AdminLogin(Base):
    __tablename__ = "admin_logins"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    admin_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("admins.id"), nullable=False, index=True)
    login_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    logout_time: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    ip_address: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    device_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    browser: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    operating_system: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    login_status: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="SUCCESS, FAILED, LOGOUT, TOKEN_REFRESH"
    )
    failure_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    access_token: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    refresh_token: Mapped[Optional[str]] = mapped_column(String(2048), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    admin: Mapped["Admin"] = relationship("Admin", back_populates="login_history")



class StaffRole(Base):
    __tablename__ = "staff_roles"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    permissions: Mapped[Optional[Any]] = mapped_column(JSON, nullable=True)
    is_system_role: Mapped[bool] = mapped_column(Boolean, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    staff: Mapped[list["Staff"]] = relationship(
        "Staff", back_populates="staff_role", foreign_keys="[Staff.staff_role_id]"
    )


class Staff(AuditMixin, Base):
    __tablename__ = "staff"

    branch_id: Mapped[int | None] = mapped_column(
        ForeignKey("business_branch.id", use_alter=True), nullable=True
    )
    first_name: Mapped[str] = mapped_column(String(120), nullable=False)
    last_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    department: Mapped[str | None] = mapped_column(String(100), nullable=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    staff_role_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        ForeignKey("staff_roles.id"), nullable=True
    )

    staff_role: Mapped[Optional["StaffRole"]] = relationship(
        "StaffRole", back_populates="staff", foreign_keys=[staff_role_id]
    )


class StaffLogin(AuditMixin, Base):
    __tablename__ = "staff_login"

    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device: Mapped[str | None] = mapped_column(String(255), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(255), nullable=True)
    login_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    logout_time: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)


class StaffOnboarding(AuditMixin, Base):
    __tablename__ = "staff_onboarding"
    __table_args__ = (UniqueConstraint("staff_id"),)

    staff_id: Mapped[int] = mapped_column(ForeignKey("staff.id"), nullable=False)
    personal_information: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    employment_information: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    emergency_contact: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    identification: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    bank_information: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    next_of_kin: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    skills_and_qualifications: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    family_background: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    references: Mapped[list[dict[str, Any]]] = mapped_column(JSON, nullable=False)
    reference_verification: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    declaration: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    hr_use_only: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    onboarding_status: Mapped[str] = mapped_column(
        String(50), nullable=False, default="DRAFT"
    )
    submitted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )


class Business(AuditMixin, Base):
    """Top-level business account. Physical, operational detail lives on BusinessBranch."""

    __tablename__ = "business"

    business_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)


class BusinessBranch(AuditMixin, InventorySyncMixin, Base):
    """A physical location belonging to a business. Operational records key off branch_id."""

    __tablename__ = "business_branch"

    business_id: Mapped[int] = mapped_column(ForeignKey("business.id", use_alter=True), nullable=False)
    branch_name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    country: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    postal_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    star_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    check_in_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    check_out_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    inventory_software_business_branch_id: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )
    inventory_software_api_key: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )


class BusinessImage(AuditMixin, Base):
    __tablename__ = "business_image"

    branch_id: Mapped[int] = mapped_column(
        ForeignKey("business_branch.id"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(String(500), nullable=False)
    is_cover: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.text("false")
    )


class Task(AuditMixin, Base):
    __tablename__ = "task"
    assigned_staff_id: Mapped[int | None] = mapped_column(ForeignKey("staff.id"), nullable=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    task_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="OPEN")
    priority: Mapped[str] = mapped_column(String(50), nullable=False, default="MEDIUM")
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class ActivityLog(AuditMixin, Base):
    __tablename__ = "activity_log"

    user_type: Mapped[str] = mapped_column(String(50), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    action: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    device: Mapped[str | None] = mapped_column(String(255), nullable=True)


class BusinessSetting(AuditMixin, Base):
    __tablename__ = "business_setting"
    __table_args__ = (UniqueConstraint("branch_id"),)

    branch_id: Mapped[int] = mapped_column(
        ForeignKey("business_branch.id"), nullable=False
    )
    currency: Mapped[str | None] = mapped_column(String(8), nullable=True)
    timezone: Mapped[str | None] = mapped_column(String(64), nullable=True)
    tax_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    service_charge_percentage: Mapped[Decimal | None] = mapped_column(
        Numeric(5, 2), nullable=True
    )
    booking_expiration_minutes: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    allow_partial_payment: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default=sa.text("false")
    )
