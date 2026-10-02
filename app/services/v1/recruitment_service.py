from __future__ import annotations

from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import case, func, or_, select, true
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams, apply_search, apply_sorting, paginate
from app.core.scope import BusinessScope
from app.models import Business, BusinessBranch, JobApplicant, JobOpening
from app.schemas.v1.common import PaginationMeta
from app.schemas.v1.recruitment import (
    JobApplicantUpdate,
    JobApplicationCreate,
    JobOpeningCreate,
    JobOpeningRead,
    JobOpeningUpdate,
)


def _branch_filter(branch_id: int | None):
    """Jobs for one branch also include business-wide jobs (branch_id NULL)."""
    if branch_id is None:
        return true()
    return or_(JobOpening.branch_id == branch_id, JobOpening.branch_id.is_(None))


class RecruitmentService:
    # --- job openings (HR) ------------------------------------------------

    def get_job(self, db: Session, job_id: int, scope: BusinessScope) -> JobOpening:
        job = db.get(JobOpening, job_id)
        if (
            job is None
            or job.deleted_at is not None
            or job.business_id != scope.business_id
            or (scope.locked_branch_id is not None and job.branch_id != scope.locked_branch_id)
        ):
            raise HTTPException(status_code=404, detail="Job opening not found")
        return job

    def _hr_branch_filter(self, scope: BusinessScope, branch_id: int | None):
        # Branch-locked staff only see their branch's jobs; business-wide jobs belong to admins.
        if scope.locked_branch_id is not None:
            return JobOpening.branch_id == scope.locked_branch_id
        return _branch_filter(branch_id)

    def list_jobs(
        self,
        db: Session,
        params: ListQueryParams,
        scope: BusinessScope,
        status: str | None = None,
        branch_id: int | None = None,
    ) -> tuple[list[JobOpeningRead], PaginationMeta]:
        stmt = select(JobOpening).where(
            JobOpening.deleted_at.is_(None),
            JobOpening.business_id == scope.business_id,
            self._hr_branch_filter(scope, branch_id),
        )
        if status is not None:
            stmt = stmt.where(JobOpening.status == status.upper())
        stmt = apply_search(stmt, JobOpening, params.search, ["title", "department", "location"])
        stmt = apply_sorting(stmt, JobOpening, params.sort_by, params.sort_order)
        jobs, meta = paginate(db, stmt, params)
        return self._with_counts(db, jobs), meta

    def _with_counts(self, db: Session, jobs) -> list[JobOpeningRead]:
        ids = [job.id for job in jobs]
        counts: dict[int, tuple[int, int]] = {}
        if ids:
            rows = db.execute(
                select(
                    JobApplicant.job_opening_id,
                    func.count(JobApplicant.id),
                    func.sum(case((JobApplicant.status == "NEW", 1), else_=0)),
                )
                .where(JobApplicant.job_opening_id.in_(ids), JobApplicant.deleted_at.is_(None))
                .group_by(JobApplicant.job_opening_id)
            ).all()
            counts = {row[0]: (row[1] or 0, row[2] or 0) for row in rows}
        result = []
        for job in jobs:
            read = JobOpeningRead.model_validate(job)
            read.applicant_count, read.new_applicant_count = counts.get(job.id, (0, 0))
            result.append(read)
        return result

    def job_read(self, db: Session, job: JobOpening) -> JobOpeningRead:
        return self._with_counts(db, [job])[0]

    def create_job(self, db: Session, payload: JobOpeningCreate, scope: BusinessScope) -> JobOpening:
        values = payload.model_dump()
        scope.check_branch(db, values["branch_id"])
        if scope.locked_branch_id is not None:
            values["branch_id"] = scope.locked_branch_id
        job = JobOpening(**values, business_id=scope.business_id, created_by=scope.staff.id)
        db.add(job)
        db.commit()
        db.refresh(job)
        return job

    def update_job(self, db: Session, job_id: int, payload: JobOpeningUpdate, scope: BusinessScope) -> JobOpening:
        job = self.get_job(db, job_id, scope)
        values = payload.model_dump(exclude_unset=True)
        scope.check_branch(db, values.get("branch_id"))
        if scope.locked_branch_id is not None and "branch_id" in values and values["branch_id"] is None:
            raise HTTPException(status_code=403, detail="Only Super Admin or General Admin can post business-wide jobs")
        for field, value in values.items():
            setattr(job, field, value)
        job.updated_by = scope.staff.id
        db.commit()
        db.refresh(job)
        return job

    def delete_job(self, db: Session, job_id: int, scope: BusinessScope) -> dict[str, int | bool]:
        job = self.get_job(db, job_id, scope)
        job.deleted_at = datetime.now(timezone.utc)
        job.deleted_by = scope.staff.id
        db.commit()
        return {"deleted": True, "id": job_id}

    # --- careers page (public, per business) -----------------------------

    def careers_context(self, db: Session, business_id: int) -> dict:
        business = db.get(Business, business_id)
        if business is None or business.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Careers page not found")
        branches = db.scalars(
            select(BusinessBranch)
            .where(BusinessBranch.business_id == business_id, BusinessBranch.deleted_at.is_(None))
            .order_by(BusinessBranch.branch_name)
        ).all()
        return {
            "business": {"id": business.id, "business_name": business.business_name},
            "branches": [
                {"id": b.id, "branch_name": b.branch_name, "city": b.city, "state": b.state} for b in branches
            ],
        }

    def _accepting_applications(self, business_id: int):
        return (
            JobOpening.deleted_at.is_(None),
            JobOpening.business_id == business_id,
            JobOpening.status == "OPEN",
            or_(JobOpening.closing_date.is_(None), JobOpening.closing_date >= date.today()),
        )

    def list_open_jobs(self, db: Session, business_id: int, params: ListQueryParams, branch_id: int | None = None):
        stmt = select(JobOpening).where(*self._accepting_applications(business_id), _branch_filter(branch_id))
        stmt = apply_search(stmt, JobOpening, params.search, ["title", "department", "location"])
        stmt = apply_sorting(stmt, JobOpening, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def get_open_job(self, db: Session, business_id: int, job_id: int) -> JobOpening:
        job = db.scalar(
            select(JobOpening).where(JobOpening.id == job_id, *self._accepting_applications(business_id))
        )
        if job is None:
            raise HTTPException(status_code=404, detail="This job is no longer accepting applications")
        return job

    def apply(self, db: Session, business_id: int, job_id: int, payload: JobApplicationCreate) -> JobApplicant:
        job = self.get_open_job(db, business_id, job_id)
        email = payload.email.lower()
        duplicate = db.scalar(
            select(JobApplicant.id).where(
                JobApplicant.job_opening_id == job.id,
                func.lower(JobApplicant.email) == email,
                JobApplicant.deleted_at.is_(None),
            )
        )
        if duplicate is not None:
            raise HTTPException(status_code=409, detail="You have already applied for this job")
        applicant = JobApplicant(
            job_opening_id=job.id,
            full_name=payload.full_name.strip(),
            email=email,
            phone=payload.phone,
            cv_url=str(payload.cv_url),
            cover_letter=payload.cover_letter,
            status="NEW",
        )
        db.add(applicant)
        db.commit()
        db.refresh(applicant)
        return applicant

    # --- applicants (HR) --------------------------------------------------

    def list_applicants(
        self, db: Session, job_id: int, params: ListQueryParams, scope: BusinessScope, status: str | None = None
    ):
        self.get_job(db, job_id, scope)
        stmt = select(JobApplicant).where(
            JobApplicant.job_opening_id == job_id, JobApplicant.deleted_at.is_(None)
        )
        if status is not None:
            stmt = stmt.where(JobApplicant.status == status.upper())
        stmt = apply_search(stmt, JobApplicant, params.search, ["full_name", "email", "phone"])
        stmt = apply_sorting(stmt, JobApplicant, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def update_applicant(
        self, db: Session, applicant_id: int, payload: JobApplicantUpdate, scope: BusinessScope
    ) -> JobApplicant:
        applicant = db.get(JobApplicant, applicant_id)
        if applicant is None or applicant.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Applicant not found")
        try:
            self.get_job(db, applicant.job_opening_id, scope)
        except HTTPException:
            raise HTTPException(status_code=404, detail="Applicant not found")
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(applicant, field, value)
        applicant.updated_by = scope.staff.id
        db.commit()
        db.refresh(applicant)
        return applicant
