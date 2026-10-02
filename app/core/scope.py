"""Business/branch scoping.

Every logged-in staff member belongs to a branch, and every branch to a business.
Nothing outside the staff member's business is ever visible.

- Super Admin and General Admin see the whole business and can filter by branch.
- Everyone else (HR Manager included) is locked to their own branch.
"""
from __future__ import annotations

from dataclasses import dataclass

from fastapi import Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.sql import Select

from app.core.auth import can_filter_branches, get_current_staff, get_manager
from app.models import BusinessBranch, Staff


@dataclass
class BusinessScope:
    staff: Staff
    business_id: int
    # Set for staff limited to their own branch; None for business-wide roles.
    locked_branch_id: int | None = None

    def branch_ids(self) -> Select:
        """Subquery of the (non-deleted) branch ids in this business."""
        return select(BusinessBranch.id).where(
            BusinessBranch.business_id == self.business_id,
            BusinessBranch.deleted_at.is_(None),
        )

    def effective_branch(self, branch_id: int | None) -> int | None:
        """The branch a query should be limited to: always the locked branch when there is one."""
        return self.locked_branch_id if self.locked_branch_id is not None else branch_id

    def check_branch(self, db: Session, branch_id: int | None) -> int | None:
        """Validate an optional branch filter/value: 404 outside the business, 403 outside a locked branch."""
        if branch_id is None:
            return None
        branch = db.get(BusinessBranch, branch_id)
        if branch is None or branch.deleted_at is not None or branch.business_id != self.business_id:
            raise HTTPException(status_code=404, detail="Branch not found")
        if self.locked_branch_id is not None and branch_id != self.locked_branch_id:
            raise HTTPException(status_code=403, detail="You can only access your own branch")
        return branch_id

    def staff_filter(self, column, branch_id: int | None = None):
        """WHERE clause limiting a staff.branch_id-like column to what this user may see."""
        branch_id = self.effective_branch(branch_id)
        if branch_id is not None:
            return column == branch_id
        return column.in_(self.branch_ids())

    def check_staff(self, db: Session, staff_id: int) -> Staff:
        """Load a staff member, 404 if this user may not see them."""
        target = db.get(Staff, staff_id)
        if target is None or target.branch is None or target.branch.business_id != self.business_id:
            raise HTTPException(status_code=404, detail="Staff not found")
        if self.locked_branch_id is not None and target.branch_id != self.locked_branch_id:
            raise HTTPException(status_code=404, detail="Staff not found")
        return target


def _scope_for(staff: Staff) -> BusinessScope:
    if staff.branch is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is not linked to a business branch. Contact your administrator.",
        )
    return BusinessScope(
        staff=staff,
        business_id=staff.branch.business_id,
        locked_branch_id=None if can_filter_branches(staff) else staff.branch_id,
    )


def get_scope(staff: Staff = Depends(get_current_staff)) -> BusinessScope:
    return _scope_for(staff)


def get_manager_scope(staff: Staff = Depends(get_manager)) -> BusinessScope:
    return _scope_for(staff)


def get_admin_scope(staff: Staff = Depends(get_current_staff)) -> BusinessScope:
    """Super Admin / General Admin only (business-wide settings such as branches)."""
    if not can_filter_branches(staff):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action is limited to Super Admin and General Admin",
        )
    return _scope_for(staff)
