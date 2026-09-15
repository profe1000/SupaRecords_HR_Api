from __future__ import annotations

from datetime import datetime
from typing import Any
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
