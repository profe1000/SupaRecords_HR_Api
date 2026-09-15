from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class TaskBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    assigned_staff_id: int | None = None
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    task_type: str = Field(..., min_length=1, max_length=50)
    status: str = Field(default="OPEN", min_length=1, max_length=50)
    priority: str = Field(default="MEDIUM", min_length=1, max_length=50)


class TaskCreate(TaskBase):
    pass


class TaskUpdate(BaseModel):
    assigned_staff_id: int | None = None
    title: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    task_type: str | None = Field(default=None, min_length=1, max_length=50)
    status: str | None = Field(default=None, min_length=1, max_length=50)
    priority: str | None = Field(default=None, min_length=1, max_length=50)
    resolved_at: datetime | None = None


class TaskRead(TaskBase):
    id: int
    resolved_at: datetime | None = None
    created_at: datetime
    updated_at: datetime