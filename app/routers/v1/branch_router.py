from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.scope import BusinessScope, get_admin_scope
from app.dependencies import get_db
from app.schemas.v1.branch import BranchCreate, BranchUpdate
from app.schemas.v1.common import success_response
from app.services.v1.branch_service import BranchService

# Branch management for the caller's business: Super Admin / General Admin only.
router = APIRouter(prefix="/branches", tags=["branches"])
service = BranchService()


@router.get("/")
def list_branches(scope: BusinessScope = Depends(get_admin_scope), db: Session = Depends(get_db)):
    return success_response(service.list(db, scope), message="Branches retrieved successfully")


@router.post("/")
def create_branch(payload: BranchCreate, scope: BusinessScope = Depends(get_admin_scope), db: Session = Depends(get_db)):
    branch = service.create(db, scope, payload)
    return success_response(service.read_one(db, scope, branch), message="Branch created")


@router.put("/{branch_id}")
def update_branch(
    branch_id: int,
    payload: BranchUpdate,
    scope: BusinessScope = Depends(get_admin_scope),
    db: Session = Depends(get_db),
):
    branch = service.update(db, scope, branch_id, payload)
    return success_response(service.read_one(db, scope, branch), message="Branch updated")


@router.delete("/{branch_id}")
def delete_branch(branch_id: int, scope: BusinessScope = Depends(get_admin_scope), db: Session = Depends(get_db)):
    return success_response(service.delete(db, scope, branch_id), message="Branch deleted")
