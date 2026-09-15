from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Staff, StaffOnboarding
from app.schemas.v1.onboarding import StaffOnboardingCreate, StaffOnboardingUpdate


SECTION_FIELDS = (
    "personal_information",
    "employment_information",
    "emergency_contact",
    "identification",
    "bank_information",
    "next_of_kin",
    "skills_and_qualifications",
    "family_background",
    "references",
    "reference_verification",
    "declaration",
    "hr_use_only",
)


class OnboardingService:
    def _get_staff(self, db: Session, staff_id: int) -> Staff:
        staff = db.get(Staff, staff_id)
        if staff is None or staff.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Staff not found")
        return staff

    def get(self, db: Session, staff_id: int) -> StaffOnboarding:
        onboarding = db.scalar(
            select(StaffOnboarding).where(
                StaffOnboarding.staff_id == staff_id,
                StaffOnboarding.deleted_at.is_(None),
            )
        )
        if onboarding is None:
            raise HTTPException(status_code=404, detail="Staff onboarding form not found")
        return onboarding

    def upsert(
        self,
        db: Session,
        staff_id: int,
        payload: StaffOnboardingUpdate,
    ) -> StaffOnboarding:
        self._get_staff(db, staff_id)
        onboarding = db.scalar(
            select(StaffOnboarding).where(StaffOnboarding.staff_id == staff_id)
        )

        if onboarding is None or onboarding.deleted_at is not None:
            create_payload = StaffOnboardingCreate.model_validate(
                payload.model_dump(
                    exclude_unset=True,
                    exclude_none=True,
                    by_alias=True,
                )
            )
            values = create_payload.model_dump(mode="json", by_alias=True)
            status = values.pop("onboarding_status")
            submitted_at = (
                datetime.now(timezone.utc)
                if status in {"SUBMITTED", "VERIFIED"}
                else None
            )

        if onboarding is None:
            onboarding = StaffOnboarding(
                staff_id=staff_id,
                onboarding_status=status,
                submitted_at=submitted_at,
                **values,
            )
            db.add(onboarding)
        elif onboarding.deleted_at is not None:
            for field, value in values.items():
                setattr(onboarding, field, value)
            onboarding.onboarding_status = status
            onboarding.submitted_at = submitted_at
            onboarding.deleted_at = None
        else:
            supplied = payload.model_fields_set
            for field in SECTION_FIELDS:
                if field not in supplied:
                    continue
                section = getattr(payload, field)
                if section is None:
                    continue
                if field == "references":
                    value: Any = [
                        item.model_dump(mode="json", by_alias=True) for item in section
                    ]
                else:
                    current = getattr(onboarding, field) or {}
                    changes = section.model_dump(
                        mode="json",
                        by_alias=True,
                        exclude_unset=True,
                    )
                    value = {**current, **changes}
                setattr(onboarding, field, value)

            if "onboarding_status" in supplied and payload.onboarding_status is not None:
                onboarding.onboarding_status = payload.onboarding_status
                if payload.onboarding_status in {"SUBMITTED", "VERIFIED"}:
                    onboarding.submitted_at = onboarding.submitted_at or datetime.now(
                        timezone.utc
                    )
                else:
                    onboarding.submitted_at = None

        db.commit()
        db.refresh(onboarding)
        return onboarding