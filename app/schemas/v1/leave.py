from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

LeaveType = Literal["ANNUAL", "SICK", "CASUAL", "MATERNITY", "PATERNITY", "COMPASSIONATE", "STUDY", "OTHER"]
ApprovalStatus = Literal["PENDING", "APPROVED", "REJECTED", "CANCELLED"]


class StaffSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    email: str
    department: str | None = None


class LeaveAllowanceUpsert(BaseModel):
    total_days: int = Field(..., ge=0, le=366)


class LeaveAllowanceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    staff_id: int
    year: int
    total_days: int
    updated_at: datetime


class LeaveBalance(BaseModel):
    staff_id: int
    year: int
    total_days: int
    used_days: int
    pending_days: int
    remaining_days: int


class LeaveApplicationCreate(BaseModel):
    leave_type: LeaveType
    start_date: date
    end_date: date
    reason: str | None = Field(default=None, max_length=2000)

    @model_validator(mode="after")
    def check_dates(self):
        if self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if self.end_date.year != self.start_date.year:
            raise ValueError("Leave cannot span two calendar years; submit one application per year")
        return self


class ReviewDecision(BaseModel):
    comment: str | None = Field(default=None, max_length=2000)


class LeaveApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    staff_id: int
    leave_type: str
    start_date: date
    end_date: date
    days: int
    reason: str | None
    status: ApprovalStatus
    reviewed_by: int | None
    reviewed_at: datetime | None
    review_comment: str | None
    created_at: datetime
    staff: StaffSummary
    reviewer: StaffSummary | None = None
