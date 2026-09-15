from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AdminLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class AdminCreate(BaseModel):
    fullname: str | None = Field(default=None, max_length=200)
    username: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6)
    phone_number: str | None = Field(default=None, max_length=50)
    profile_image: str | None = Field(default=None, max_length=2048)
    admin_role_id: UUID | None = None
    is_superadmin: bool = False


class AdminRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    fullname: str | None
    username: str
    email: EmailStr
    phone_number: str | None
    profile_image: str | None
    is_superadmin: bool
    is_active: bool
    admin_role_id: UUID | None
    created_at: datetime


class AdminRoleRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    title: str | None
    description: str | None
    permissions: Any | None
    is_system_role: bool
    is_active: bool


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin: AdminRead