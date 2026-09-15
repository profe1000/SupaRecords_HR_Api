from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class VendorBase(BaseModel):
    branch_id: int
    # primary contact fields
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    # legacy display name (kept for compatibility)
    name: str = Field(min_length=1, max_length=200)
    vendor_type: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    opening_balance: Decimal = Field(default=0)
    status: str = "ACTIVE"


class VendorCreate(BaseModel):
    branch_id: int
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    vendor_type: Optional[str] = None
    opening_balance: Decimal = Field(default=0)
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: str = "ACTIVE"


class VendorUpdate(BaseModel):
    first_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    company_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    vendor_type: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    opening_balance: Optional[Decimal] = None


class VendorCreditCreate(BaseModel):
    vendor_id: int
    payment_method_id: Optional[int] = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="NGN", min_length=3, max_length=8)
    description: Optional[str] = None
    reference: Optional[str] = None


class VendorCreditUpdate(BaseModel):
    description: Optional[str] = None


class VendorCreditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vendor_id: int
    payment_id: int
    original_amount: Decimal
    remaining_amount: Decimal
    currency: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class VendorRead(VendorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    credit_balance: Decimal = Decimal("0")
    active_credits: list[VendorCreditRead] = Field(default_factory=list)