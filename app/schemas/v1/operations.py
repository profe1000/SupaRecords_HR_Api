from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class CustomerCreditCreate(BaseModel):
    guest_id: int
    branch_id: int
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="NGN", min_length=3, max_length=8)
    description: Optional[str] = None


class CreditAllocationInput(BaseModel):
    customer_credit_id: int
    amount: Decimal = Field(gt=0)


class CreditPaymentCreate(BaseModel):
    booking_id: int
    allocations: list[CreditAllocationInput] = Field(min_length=1)


class LaundryCreditPaymentCreate(BaseModel):
    laundry_order_id: int
    allocations: list[CreditAllocationInput] = Field(min_length=1)


class CustomerCreditRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    guest_id: int
    branch_id: int
    reference: str
    original_amount: Decimal
    remaining_amount: Decimal
    currency: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None


class RoomMaintenanceCreate(BaseModel):
    room_id: int
    assigned_staff_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    maintenance_type: Literal["CLEANING", "REPAIRS", "REPLACE"] = "REPAIRS"
    status: str = "OPEN"
    priority: str = "MEDIUM"


class RoomMaintenanceUpdate(BaseModel):
    assigned_staff_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    maintenance_type: Optional[Literal["CLEANING", "REPAIRS", "REPLACE"]] = None
    status: Optional[str] = None
    priority: Optional[str] = None


class ExpenseCategoryCreate(BaseModel):
    branch_id: int
    name: str = Field(min_length=1, max_length=120)
    description: Optional[str] = None
    # `inventory_expenses_category_id` removed from client payloads; server-managed


class ExpenseItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    quantity: Decimal = Field(default=1, gt=0)
    unit_cost: Decimal = Field(gt=0)


class ExpenseCreate(BaseModel):
    branch_id: int
    expense_category_id: int
    vendor_id: Optional[int] = None
    description: Optional[str] = None
    requested_by: Optional[int] = None
    items: list[ExpenseItemCreate] = Field(min_length=1)


class ExpenseApproval(BaseModel):
    approved_by: int
    approved: bool = True


class OutflowPaymentCreate(BaseModel):
    payment_method_id: Optional[int] = None
    amount: Decimal = Field(gt=0)
    currency: str = Field(default="NGN", min_length=3, max_length=8)
    reference: Optional[str] = None


class LaundryItemTypeCreate(BaseModel):
    branch_id: int
    name: str = Field(min_length=1, max_length=120)
    price: Decimal = Field(ge=0)


class LaundryOrderItemCreate(BaseModel):
    laundry_item_type_id: int
    quantity: int = Field(gt=0)
    unit_price: Optional[Decimal] = Field(default=None, ge=0)


class LaundryOrderCreate(BaseModel):
    branch_id: int
    room_id: int
    guest_id: Optional[int] = None
    notes: Optional[str] = None
    items: list[LaundryOrderItemCreate] = Field(min_length=1)


class LaundryPaymentCreate(BaseModel):
    payment_method_id: Optional[int] = None
    amount: Decimal = Field(gt=0)