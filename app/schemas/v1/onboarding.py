from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class PersonalInformation(BaseModel):
    first_name: str | None = Field(default=None, max_length=120)
    middle_name: str | None = Field(default=None, max_length=120)
    last_name: str | None = Field(default=None, max_length=120)
    date_of_birth: date | None = None
    gender: str | None = Field(default=None, max_length=50)
    marital_status: str | None = Field(default=None, max_length=50)
    nationality: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=50)
    email_address: EmailStr | None = None
    residential_address: str | None = None
    state_lga: str | None = Field(default=None, max_length=150)


class EmploymentInformation(BaseModel):
    date_of_employment: date | None = None
    department: str | None = Field(default=None, max_length=100)
    job_title: str | None = Field(default=None, max_length=150)
    staff_role: str | None = Field(default=None, max_length=150)
    branch_location: str | None = Field(default=None, max_length=255)
    reporting_manager: str | None = Field(default=None, max_length=255)
    employment_status: str | None = Field(default=None, max_length=50)
    probation_end_date: date | None = None
    employment_type: Literal[
        "FULL_TIME",
        "PART_TIME",
        "CONTRACT",
        "TEMPORARY",
        "INTERN",
        "YOUTH_CORP",
    ] | None = None


class ContactInformation(BaseModel):
    name: str | None = Field(default=None, max_length=255)
    relationship: str | None = Field(default=None, max_length=100)
    phone_number: str | None = Field(default=None, max_length=50)
    address: str | None = None


class IdentificationInformation(BaseModel):
    id_type: str | None = Field(default=None, max_length=100)
    id_number: str | None = Field(default=None, max_length=150)


class BankInformation(BaseModel):
    bank_name: str | None = Field(default=None, max_length=150)
    account_name: str | None = Field(default=None, max_length=255)
    account_number: str | None = Field(default=None, max_length=50)
    payment_method: str | None = Field(default=None, max_length=100)
    salary_grade: str | None = Field(default=None, max_length=100)


class SkillsAndQualifications(BaseModel):
    highest_qualification: str | None = Field(default=None, max_length=150)
    institution: str | None = Field(default=None, max_length=255)
    course_of_study: str | None = Field(default=None, max_length=255)
    professional_certifications: list[str] = Field(default_factory=list)
    skills: list[str] = Field(default_factory=list)
    years_of_experience: float | None = Field(default=None, ge=0)


class FamilyBackground(BaseModel):
    father_name: str | None = Field(default=None, max_length=255)
    father_occupation: str | None = Field(default=None, max_length=255)
    mother_name: str | None = Field(default=None, max_length=255)
    mother_occupation: str | None = Field(default=None, max_length=255)
    spouse_name: str | None = Field(default=None, max_length=255)
    spouse_occupation: str | None = Field(default=None, max_length=255)
    number_of_children: int | None = Field(default=None, ge=0)
    children_names: list[str] = Field(default_factory=list)
    other_dependants: list[str] = Field(default_factory=list)
    family_address: str | None = None
    family_contact_number: str | None = Field(default=None, max_length=50)
    additional_family_information: str | None = None


class ReferenceInformation(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    relationship_to_employee: str | None = Field(default=None, max_length=100)
    occupation_position: str | None = Field(default=None, max_length=255)
    company_organization: str | None = Field(default=None, max_length=255)
    phone_number: str | None = Field(default=None, max_length=50)
    email_address: EmailStr | None = None
    address: str | None = None


class ReferenceVerification(BaseModel):
    reference_checked_by: str | None = Field(default=None, max_length=255)
    date_checked: date | None = None
    verification_status: str | None = Field(default=None, max_length=50)
    hr_remarks: str | None = None


class DeclarationInformation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    information_confirmed: bool = False
    employee_signature: str | None = None
    hr_officer: str | None = Field(default=None, max_length=255)
    declaration_date: date | None = Field(default=None, alias="date")
    authorized_signature: str | None = None


class HRUseOnly(BaseModel):
    employee_record_number: str | None = Field(default=None, max_length=100)
    date_received: date | None = None
    verified_by: str | None = Field(default=None, max_length=255)
    verification_date: date | None = None


class StaffOnboardingBase(BaseModel):
    personal_information: PersonalInformation = Field(default_factory=PersonalInformation)
    employment_information: EmploymentInformation = Field(default_factory=EmploymentInformation)
    emergency_contact: ContactInformation = Field(default_factory=ContactInformation)
    identification: IdentificationInformation = Field(default_factory=IdentificationInformation)
    bank_information: BankInformation = Field(default_factory=BankInformation)
    next_of_kin: ContactInformation = Field(default_factory=ContactInformation)
    skills_and_qualifications: SkillsAndQualifications = Field(default_factory=SkillsAndQualifications)
    family_background: FamilyBackground = Field(default_factory=FamilyBackground)
    references: list[ReferenceInformation] = Field(default_factory=list, max_length=2)
    reference_verification: ReferenceVerification = Field(default_factory=ReferenceVerification)
    declaration: DeclarationInformation = Field(default_factory=DeclarationInformation)
    hr_use_only: HRUseOnly = Field(default_factory=HRUseOnly)
    onboarding_status: Literal["DRAFT", "SUBMITTED", "VERIFIED"] = "DRAFT"


class StaffOnboardingCreate(StaffOnboardingBase):
    pass


class StaffOnboardingUpdate(BaseModel):
    personal_information: PersonalInformation | None = None
    employment_information: EmploymentInformation | None = None
    emergency_contact: ContactInformation | None = None
    identification: IdentificationInformation | None = None
    bank_information: BankInformation | None = None
    next_of_kin: ContactInformation | None = None
    skills_and_qualifications: SkillsAndQualifications | None = None
    family_background: FamilyBackground | None = None
    references: list[ReferenceInformation] | None = Field(default=None, max_length=2)
    reference_verification: ReferenceVerification | None = None
    declaration: DeclarationInformation | None = None
    hr_use_only: HRUseOnly | None = None
    onboarding_status: Literal["DRAFT", "SUBMITTED", "VERIFIED"] | None = None


class StaffOnboardingRead(StaffOnboardingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    staff_id: int
    submitted_at: datetime | None
    created_at: datetime
    updated_at: datetime