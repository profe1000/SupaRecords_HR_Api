from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BusinessBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    business_name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, max_length=50)


class BusinessCreate(BusinessBase):
    pass


class BusinessUpdate(BaseModel):
    business_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, max_length=50)
    website: Optional[str] = Field(default=None, max_length=255)
    status: Optional[str] = Field(default=None, max_length=50)


class BusinessRead(BusinessBase):
    id: int