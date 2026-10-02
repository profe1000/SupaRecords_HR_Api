from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class StaffLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class StaffCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: EmailStr
    password: str = Field(..., min_length=6)
    branch_id: int
    phone: str | None = Field(default=None, max_length=50)
    department: str | None = Field(default=None, max_length=100)
    staff_role_id: UUID | None = None
    # Optional leave allowance, in calendar days, for `leave_year` (defaults to the current year).
    leave_days: int | None = Field(default=None, ge=0, le=366)
    leave_year: int | None = Field(default=None, ge=2000, le=2100)


class StaffUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=120)
    last_name: str | None = Field(default=None, min_length=1, max_length=120)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=6)
    branch_id: int | None = None
    phone: str | None = Field(default=None, max_length=50)
    department: str | None = Field(default=None, max_length=100)
    staff_role_id: UUID | None = None
    status: Literal["ACTIVE", "INACTIVE", "SUSPENDED"] | None = None
    leave_days: int | None = Field(default=None, ge=0, le=366)
    leave_year: int | None = Field(default=None, ge=2000, le=2100)


class StaffChangePassword(BaseModel):
    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=6, max_length=128)


class StaffPasswordReset(BaseModel):
    # Leave empty to have the system generate a temporary password.
    new_password: str | None = Field(default=None, min_length=6, max_length=128)
    send_email: bool = True


class StaffPasswordResetResponse(BaseModel):
    staff_id: int
    # Returned once so the admin can pass it on if the email was not sent.
    temporary_password: str
    email_sent: bool
    email_error: str | None = None


class StaffPermissions(BaseModel):
    is_manager: bool
    # Super Admin / General Admin: whole business, branch filter, branch management.
    can_filter_branches: bool
    can_approve_leave: bool
    can_approve_requests: bool


class StaffRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int | None
    first_name: str
    last_name: str
    email: EmailStr
    phone: str | None
    department: str | None
    status: str | None
    staff_role_id: UUID | None
    created_at: datetime


class StaffCreateResponse(StaffRead):
    email_sent: bool = False
    email_message_id: str | None = None
    email_error: str | None = None


class StaffBranchRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    branch_name: str
    description: str | None = None
    email: str | None = None
    phone_number: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    address: str | None = None
    postal_code: str | None = None
    status: str | None = None


class StaffRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    title: str | None
    description: str | None
    permissions: Any | None
    is_system_role: bool
    is_active: bool


class StaffAuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    staff: StaffRead



class StaffRegister(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: str
    password: str = Field(..., min_length=6)
    business_name: str = Field(..., min_length=2, max_length=255)
StaffLogin = StaffLoginRequest
