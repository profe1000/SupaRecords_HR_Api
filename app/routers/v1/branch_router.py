from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams
from app.dependencies import get_db
from app.schemas.v1.branch import BranchCreate, BranchRead, BranchUpdate
from app.schemas.v1.common import success_response
from app.services.v1.branch_service import BranchService

router = APIRouter(prefix="/branches", tags=["branches"])
service = BranchService()


@router.get("/")
def list_branches(params: ListQueryParams = Depends(), db: Session = Depends(get_db)):
    items, meta = service.list(db, params)
    data = [BranchRead.model_validate(item, from_attributes=True) for item in items]
    return success_response(data, message="Branches retrieved successfully", meta=meta)


@router.get("/hotel/{hotel_id}")
def list_branches_by_hotel(hotel_id: int, params: ListQueryParams = Depends(), db: Session = Depends(get_db)):
    items, meta = service.list_by_hotel(db, hotel_id, params)
    data = [BranchRead.model_validate(item, from_attributes=True) for item in items]
    return success_response(data, message="Branches retrieved successfully", meta=meta)


@router.get("/{branch_id}")
def get_branch(branch_id: int, db: Session = Depends(get_db)):
    branch = service.get(db, branch_id)
    return success_response(BranchRead.model_validate(branch, from_attributes=True), message="Branch retrieved successfully")


@router.post("/", response_model=BranchRead)
def create_branch(payload: BranchCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.put("/{branch_id}", response_model=BranchRead)
def update_branch(branch_id: int, payload: BranchUpdate, db: Session = Depends(get_db)):
    return service.update(db, branch_id, payload)


@router.delete("/{branch_id}")
def delete_branch(branch_id: int, db: Session = Depends(get_db)):
    return service.delete(db, branch_id)
