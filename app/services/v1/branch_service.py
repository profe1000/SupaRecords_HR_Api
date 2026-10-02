from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.scope import BusinessScope
from app.models import BusinessBranch, JobOpening, Staff, Task
from app.schemas.v1.branch import BranchCreate, BranchRead, BranchUpdate


class BranchService:
    """Branches of the caller's business. Managed by Super Admin / General Admin only."""

    def _main_branch_id(self, db: Session, business_id: int) -> int | None:
        # The first branch created for the business (e.g. the HQ created at sign-up).
        return db.scalar(
            select(func.min(BusinessBranch.id)).where(
                BusinessBranch.business_id == business_id, BusinessBranch.deleted_at.is_(None)
            )
        )

    def _counts(self, db: Session, model, column, branch_ids: list[int]) -> dict[int, int]:
        if not branch_ids:
            return {}
        rows = db.execute(
            select(column, func.count(model.id))
            .where(column.in_(branch_ids), model.deleted_at.is_(None))
            .group_by(column)
        ).all()
        return {branch_id: count for branch_id, count in rows}

    def _read(self, db: Session, branches: list[BusinessBranch], main_id: int | None) -> list[BranchRead]:
        ids = [branch.id for branch in branches]
        staff = self._counts(db, Staff, Staff.branch_id, ids)
        tasks = self._counts(db, Task, Task.branch_id, ids)
        jobs = self._counts(db, JobOpening, JobOpening.branch_id, ids)
        result = []
        for branch in branches:
            read = BranchRead.model_validate(branch)
            read.is_main = branch.id == main_id
            read.staff_count = staff.get(branch.id, 0)
            read.task_count = tasks.get(branch.id, 0)
            read.job_count = jobs.get(branch.id, 0)
            result.append(read)
        return result

    def list(self, db: Session, scope: BusinessScope) -> list[BranchRead]:
        branches = db.scalars(
            select(BusinessBranch)
            .where(BusinessBranch.business_id == scope.business_id, BusinessBranch.deleted_at.is_(None))
            .order_by(BusinessBranch.id)
        ).all()
        return self._read(db, list(branches), self._main_branch_id(db, scope.business_id))

    def get(self, db: Session, scope: BusinessScope, branch_id: int) -> BusinessBranch:
        branch = db.get(BusinessBranch, branch_id)
        if branch is None or branch.deleted_at is not None or branch.business_id != scope.business_id:
            raise HTTPException(status_code=404, detail="Branch not found")
        return branch

    def read_one(self, db: Session, scope: BusinessScope, branch: BusinessBranch) -> BranchRead:
        return self._read(db, [branch], self._main_branch_id(db, scope.business_id))[0]

    def _check_name_free(self, db: Session, scope: BusinessScope, name: str, exclude_id: int | None = None):
        stmt = select(BusinessBranch.id).where(
            BusinessBranch.business_id == scope.business_id,
            BusinessBranch.deleted_at.is_(None),
            func.lower(BusinessBranch.branch_name) == name.strip().lower(),
        )
        if exclude_id is not None:
            stmt = stmt.where(BusinessBranch.id != exclude_id)
        if db.scalar(stmt) is not None:
            raise HTTPException(status_code=409, detail="A branch with this name already exists")

    def create(self, db: Session, scope: BusinessScope, payload: BranchCreate) -> BusinessBranch:
        self._check_name_free(db, scope, payload.branch_name)
        values = payload.model_dump()
        values["branch_name"] = values["branch_name"].strip()
        branch = BusinessBranch(
            **values, business_id=scope.business_id, status="ACTIVE", created_by=scope.staff.id
        )
        db.add(branch)
        db.commit()
        db.refresh(branch)
        return branch

    def update(self, db: Session, scope: BusinessScope, branch_id: int, payload: BranchUpdate) -> BusinessBranch:
        branch = self.get(db, scope, branch_id)
        values = payload.model_dump(exclude_unset=True)
        if values.get("branch_name") is not None:
            values["branch_name"] = values["branch_name"].strip()
            self._check_name_free(db, scope, values["branch_name"], exclude_id=branch.id)
        elif "branch_name" in values:
            values.pop("branch_name")  # a branch always keeps a name
        for field, value in values.items():
            setattr(branch, field, value)
        branch.updated_by = scope.staff.id
        db.commit()
        db.refresh(branch)
        return branch

    def delete(self, db: Session, scope: BusinessScope, branch_id: int) -> dict[str, int | bool]:
        branch = self.get(db, scope, branch_id)
        if branch.id == self._main_branch_id(db, scope.business_id):
            raise HTTPException(status_code=400, detail="The first (main) branch of the business cannot be deleted")

        read = self.read_one(db, scope, branch)
        in_use = [
            f"{count} {label}{'' if count == 1 else 's'}"
            for count, label in (
                (read.staff_count, "staff member"),
                (read.task_count, "task"),
                (read.job_count, "job opening"),
            )
            if count
        ]
        if in_use:
            raise HTTPException(
                status_code=400,
                detail=f"This branch still has {', '.join(in_use)}. Move or remove them before deleting the branch.",
            )

        branch.deleted_at = datetime.now(timezone.utc)
        branch.deleted_by = scope.staff.id
        db.commit()
        return {"deleted": True, "id": branch_id}
