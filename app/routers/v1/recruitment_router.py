from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams
from app.core.scope import BusinessScope, get_manager_scope
from app.dependencies import get_db
from app.schemas.v1.common import success_response
from app.schemas.v1.recruitment import (
    JobApplicantRead,
    JobApplicantUpdate,
    JobApplicationCreate,
    JobOpeningCreate,
    JobOpeningPublicRead,
    JobOpeningUpdate,
)
from app.services.v1.recruitment_service import RecruitmentService


service = RecruitmentService()

# Public careers page for one business: no login required.
careers_router = APIRouter(prefix="/careers/{business_id}", tags=["careers"])


@careers_router.get("")
def get_careers_context(business_id: int, db: Session = Depends(get_db)):
    """Business name and branches, for the careers page header and branch filter."""
    return success_response(service.careers_context(db, business_id), message="Careers page retrieved successfully")


@careers_router.get("/jobs")
def list_open_jobs(
    business_id: int,
    branch_id: int | None = None,
    params: ListQueryParams = Depends(),
    db: Session = Depends(get_db),
):
    items, meta = service.list_open_jobs(db, business_id, params, branch_id=branch_id)
    data = [JobOpeningPublicRead.model_validate(item) for item in items]
    return success_response(data, message="Job openings retrieved successfully", meta=meta)


@careers_router.get("/jobs/{job_id}")
def get_open_job(business_id: int, job_id: int, db: Session = Depends(get_db)):
    job = service.get_open_job(db, business_id, job_id)
    return success_response(JobOpeningPublicRead.model_validate(job), message="Job opening retrieved successfully")


@careers_router.post("/jobs/{job_id}/apply")
def apply_for_job(business_id: int, job_id: int, payload: JobApplicationCreate, db: Session = Depends(get_db)):
    service.apply(db, business_id, job_id, payload)
    return success_response({"submitted": True}, message="Your application has been received")


# HR: manage openings and applicants within their business.
router = APIRouter(prefix="/jobs", tags=["recruitment"])


@router.get("/")
def list_jobs(
    status: str | None = None,
    branch_id: int | None = None,
    params: ListQueryParams = Depends(),
    scope: BusinessScope = Depends(get_manager_scope),
    db: Session = Depends(get_db),
):
    scope.check_branch(db, branch_id)
    data, meta = service.list_jobs(db, params, scope, status=status, branch_id=branch_id)
    return success_response(data, message="Job openings retrieved successfully", meta=meta)


@router.post("/")
def create_job(
    payload: JobOpeningCreate,
    scope: BusinessScope = Depends(get_manager_scope),
    db: Session = Depends(get_db),
):
    job = service.create_job(db, payload, scope)
    return success_response(service.job_read(db, job), message="Job opening created")


@router.patch("/applicants/{applicant_id}")
def update_applicant(
    applicant_id: int,
    payload: JobApplicantUpdate,
    scope: BusinessScope = Depends(get_manager_scope),
    db: Session = Depends(get_db),
):
    applicant = service.update_applicant(db, applicant_id, payload, scope)
    return success_response(JobApplicantRead.model_validate(applicant), message="Applicant updated")


@router.get("/{job_id}")
def get_job(job_id: int, scope: BusinessScope = Depends(get_manager_scope), db: Session = Depends(get_db)):
    job = service.get_job(db, job_id, scope)
    return success_response(service.job_read(db, job), message="Job opening retrieved successfully")


@router.put("/{job_id}")
def update_job(
    job_id: int,
    payload: JobOpeningUpdate,
    scope: BusinessScope = Depends(get_manager_scope),
    db: Session = Depends(get_db),
):
    job = service.update_job(db, job_id, payload, scope)
    return success_response(service.job_read(db, job), message="Job opening updated")


@router.delete("/{job_id}")
def delete_job(job_id: int, scope: BusinessScope = Depends(get_manager_scope), db: Session = Depends(get_db)):
    return success_response(service.delete_job(db, job_id, scope), message="Job opening deleted")


@router.get("/{job_id}/applicants")
def list_applicants(
    job_id: int,
    status: str | None = None,
    params: ListQueryParams = Depends(),
    scope: BusinessScope = Depends(get_manager_scope),
    db: Session = Depends(get_db),
):
    items, meta = service.list_applicants(db, job_id, params, scope, status=status)
    data = [JobApplicantRead.model_validate(item) for item in items]
    return success_response(data, message="Applicants retrieved successfully", meta=meta)
