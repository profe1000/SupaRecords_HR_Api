from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BranchFields(BaseModel):
    description: Optional[str] = Field(default=None, max_length=2000)
    email: Optional[EmailStr] = None
    phone_number: Optional[str] = Field(default=None, max_length=50)
    country: Optional[str] = Field(default=None, max_length=100)
    state: Optional[str] = Field(default=None, max_length=100)
    city: Optional[str] = Field(default=None, max_length=100)
    address: Optional[str] = Field(default=None, max_length=255)


class BranchCreate(BranchFields):
    """The branch is always created in the caller's business."""

    branch_name: str = Field(..., min_length=1, max_length=255)


class BranchUpdate(BranchFields):
    branch_name: Optional[str] = Field(default=None, min_length=1, max_length=255)


class BranchRead(BranchFields):
    model_config = ConfigDict(from_attributes=True)

    id: int
    business_id: int
    branch_name: str
    email: Optional[str] = None
    status: Optional[str] = None
    # The business's first branch: it can never be deleted.
    is_main: bool = False
    staff_count: int = 0
    task_count: int = 0
    job_count: int = 0
