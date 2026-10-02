from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import AnyHttpUrl, BaseModel, ConfigDict, EmailStr, Field

EmploymentType = Literal["FULL_TIME", "PART_TIME", "CONTRACT", "INTERNSHIP", "TEMPORARY"]
JobStatus = Literal["DRAFT", "OPEN", "CLOSED"]
ApplicantStatus = Literal["NEW", "SHORTLISTED", "INTERVIEW", "OFFERED", "HIRED", "REJECTED"]


class JobOpeningCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=255)
    employment_type: EmploymentType = "FULL_TIME"
    description: str = Field(..., min_length=1)
    requirements: str | None = None
    salary_range: str | None = Field(default=None, max_length=100)
    closing_date: date | None = None
    status: JobStatus = "DRAFT"
    branch_id: int | None = None


class JobOpeningUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=255)
    department: str | None = Field(default=None, max_length=100)
    location: str | None = Field(default=None, max_length=255)
    employment_type: EmploymentType | None = None
    description: str | None = Field(default=None, min_length=1)
    requirements: str | None = None
    salary_range: str | None = Field(default=None, max_length=100)
    closing_date: date | None = None
    status: JobStatus | None = None
    branch_id: int | None = None


class JobOpeningPublicRead(BaseModel):
    """What candidates see on the careers page."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    branch_id: int | None
    title: str
    department: str | None
    location: str | None
    employment_type: str
    description: str
    requirements: str | None
    salary_range: str | None
    closing_date: date | None
    created_at: datetime


class JobOpeningRead(JobOpeningPublicRead):
    business_id: int
    status: JobStatus
    updated_at: datetime
    applicant_count: int = 0
    new_applicant_count: int = 0


class JobApplicationCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=50)
    cv_url: AnyHttpUrl
    cover_letter: str | None = Field(default=None, max_length=5000)


class JobApplicantUpdate(BaseModel):
    status: ApplicantStatus | None = None
    notes: str | None = Field(default=None, max_length=5000)


class JobApplicantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    job_opening_id: int
    full_name: str
    email: str
    phone: str | None
    cv_url: str
    cover_letter: str | None
    status: ApplicantStatus
    notes: str | None
    created_at: datetime
    updated_at: datetime
