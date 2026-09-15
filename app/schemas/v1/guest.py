from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class GuestBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: str = Field(..., min_length=1, max_length=120)
    last_name: str = Field(..., min_length=1, max_length=120)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    gender: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    id_type: Optional[str] = Field(default=None, max_length=50)
    id_number: Optional[str] = Field(default=None, max_length=100)
    profile_image: Optional[str] = Field(default=None, max_length=500)
    guest_type: Optional[str] = Field(default=None, max_length=50)
    email_verified: bool = False
    phone_verified: bool = False
    opening_balance: Decimal = Field(default=0)


class GuestCreate(GuestBase):
    pass


class GuestUpdate(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    first_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    email: Optional[str] = Field(default=None, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=50)
    gender: Optional[str] = Field(default=None, max_length=20)
    date_of_birth: Optional[date] = None
    nationality: Optional[str] = Field(default=None, max_length=100)
    country: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    id_type: Optional[str] = Field(default=None, max_length=50)
    id_number: Optional[str] = Field(default=None, max_length=100)
    profile_image: Optional[str] = Field(default=None, max_length=500)
    guest_type: Optional[str] = Field(default=None, max_length=50)
    email_verified: Optional[bool] = None
    phone_verified: Optional[bool] = None


class GuestRead(GuestBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None
    credit_balance: Decimal = Decimal("0")
    active_credits: list[dict] = Field(default_factory=list)
