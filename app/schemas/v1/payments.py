from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, Field

from app.schemas.v1.guest import GuestRead


class PaymentMethodBase(BaseModel):
    branch_id: Optional[int] = None
    name: str = Field(..., min_length=2, max_length=120)
    description: Optional[str] = None
    type: Optional[str] = Field(default=None, max_length=50)
    is_default: bool = False
    status: Optional[str] = Field(default="ACTIVE", max_length=50)


class PaymentMethodCreate(PaymentMethodBase):
    pass


class PaymentMethodUpdate(PaymentMethodBase):
    branch_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=2, max_length=120)
    description: Optional[str] = None
    type: Optional[str] = Field(default=None, max_length=50)
    is_default: Optional[bool] = None
    status: Optional[str] = Field(default=None, max_length=50)


class PaymentMethodRead(PaymentMethodBase):
    model_config = {"from_attributes": True}

    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentBase(BaseModel):
    booking_id: Optional[int] = None
    laundry_order_id: Optional[int] = None
    expense_id: Optional[int] = None
    payment_method_id: Optional[int] = None
    amount: Optional[Decimal] = Field(default=None, ge=0)
    currency: Optional[str] = Field(default="NGN", min_length=3, max_length=3)
    status: Optional[Literal["PAID", "PENDING", "FAILED", "REFUNDED"]] = Field(default="PAID", max_length=50)
    payment_gateway: Optional[str] = Field(default=None, max_length=120)
    transaction_id: Optional[str] = Field(default=None, max_length=255)
    gateway_response: Optional[dict] = None
    paid_at: Optional[datetime] = None


class PaymentCreate(PaymentBase):
    pass


class CreditAllocationInput(BaseModel):
    customer_credit_id: int
    amount: Decimal = Field(gt=0)


class VendorCreditAllocationInput(BaseModel):
    vendor_credit_id: int
    amount: Decimal = Field(gt=0)


class CreditPaymentCreate(BaseModel):
    booking_id: Optional[int] = None
    laundry_order_id: Optional[int] = None
    expense_id: Optional[int] = None
    allocations: list[CreditAllocationInput | VendorCreditAllocationInput] = Field(min_length=1)


class PaymentInitializeRequest(BaseModel):
    booking_id: int = Field(validation_alias=AliasChoices("booking_id", "boooking_id"))
    email: str = Field(..., min_length=3)
    amount: Decimal = Field(default=0, ge=0)
    currency: str = Field(default="NGN", min_length=3, max_length=3)
    callback_url: Optional[str] = None


class PaymentUpdate(BaseModel):
    amount: Optional[Decimal] = Field(default=None, ge=0)
    payment_method_id: Optional[int] = None
    status: Optional[str] = Field(default=None, max_length=50)
    payment_gateway: Optional[str] = Field(default=None, max_length=120)
    transaction_id: Optional[str] = Field(default=None, max_length=255)
    gateway_response: Optional[dict] = None
    paid_at: Optional[datetime] = None


class PaymentRefund(BaseModel):
    reason: Optional[str] = None
    amount: Optional[Decimal] = Field(default=None, ge=0)


class PaymentInBookingRead(PaymentBase):
    model_config = {"from_attributes": True}

    id: int
    payment_reference: str
    credit_payment_id: Optional[int] = None
    paid_via_credit: bool = False
    direction: str = "INFLOW"
    type: str = "BOOKING"
    laundry_order_id: Optional[int] = None
    expense_id: Optional[int] = None
    payment_method: Optional[PaymentMethodRead] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class PaymentRoomRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    room_number: str
    floor: Optional[str] = None


class PaymentBookingRoomRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    room_id: int
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    room: Optional[PaymentRoomRead] = None


class PaymentBookingRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    booking_reference: str
    guest_id: int
    guest: Optional[GuestRead] = None
    booking_rooms: list[PaymentBookingRoomRead] = Field(default_factory=list)


class PaymentLaundryItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    price: Decimal


class PaymentLaundryOrderItemRead(BaseModel):
    model_config = {"from_attributes": True}

    laundry_item_type_id: int
    quantity: int
    unit_price: Decimal
    total: Decimal
    laundry_item_type: Optional[PaymentLaundryItemRead] = None


class PaymentLaundryOrderRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    order_reference: str
    room_id: int
    guest_id: Optional[int] = None
    total: Decimal
    status: str
    guest: Optional[GuestRead] = None
    room: Optional[PaymentRoomRead] = None
    items: list[PaymentLaundryOrderItemRead] = Field(default_factory=list)


class PaymentVendorRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None


class PaymentExpenseItemRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    quantity: Decimal
    unit_cost: Decimal
    total: Decimal


class PaymentExpenseRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    amount: Decimal
    status: str
    description: Optional[str] = None
    vendor_id: Optional[int] = None
    vendor: Optional[PaymentVendorRead] = None
    items: list[PaymentExpenseItemRead] = Field(default_factory=list)


class CreditPaymentAllocationRead(BaseModel):
    model_config = {"from_attributes": True}

    customer_credit_id: int
    amount: Decimal


class PaymentRead(PaymentInBookingRead):
    booking: Optional[PaymentBookingRead] = None
    laundry_order: Optional[PaymentLaundryOrderRead] = None
    expense: Optional[PaymentExpenseRead] = None
    credit_allocations: list[CreditPaymentAllocationRead] = Field(default_factory=list)
