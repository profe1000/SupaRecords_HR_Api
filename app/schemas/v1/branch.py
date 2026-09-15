from __future__ import annotations

from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class BranchBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    hotel_id: int
    branch_name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)
    star_rating: Optional[int] = Field(default=None, ge=1, le=5)
    currency: Optional[str] = Field(default=None, max_length=8)
    timezone: Optional[str] = Field(default=None, max_length=64)
    status: Optional[str] = Field(default=None, max_length=50)


class BranchCreate(BranchBase):
    pass


class BranchUpdate(BaseModel):
    hotel_id: Optional[int] = None
    branch_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)
    postal_code: Optional[str] = Field(default=None, max_length=20)
    latitude: Optional[Decimal] = Field(default=None, ge=-90, le=90)
    longitude: Optional[Decimal] = Field(default=None, ge=-180, le=180)
    star_rating: Optional[int] = Field(default=None, ge=1, le=5)
    currency: Optional[str] = Field(default=None, max_length=8)
    timezone: Optional[str] = Field(default=None, max_length=64)
    status: Optional[str] = Field(default=None, max_length=50)


class BranchRead(BranchBase):
    id: int
