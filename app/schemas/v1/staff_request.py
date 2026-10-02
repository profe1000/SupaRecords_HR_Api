from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.v1.leave import ApprovalStatus, StaffSummary

RequestType = Literal["CASH_ADVANCE", "LOAN", "EXPENSE_REIMBURSEMENT", "EQUIPMENT", "OTHER"]


class StaffRequestCreate(BaseModel):
    request_type: RequestType
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=5000)
    amount: Decimal | None = Field(default=None, ge=0, max_digits=14, decimal_places=2)


class StaffRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    staff_id: int
    request_type: str
    title: str
    description: str | None
    amount: Decimal | None
    status: ApprovalStatus
    reviewed_by: int | None
    reviewed_at: datetime | None
    review_comment: str | None
    created_at: datetime
    staff: StaffSummary
    reviewer: StaffSummary | None = None
