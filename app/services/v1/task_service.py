from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams, apply_sorting, paginate
from app.core.scope import BusinessScope
from app.models import Task
from app.schemas.v1.task import TaskCreate, TaskUpdate


class TaskService:
    def list(
        self,
        db: Session,
        params: ListQueryParams,
        scope: BusinessScope,
        assigned_staff_id: int | None = None,
        task_type: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        branch_id: int | None = None,
    ):
        stmt = select(Task).where(Task.deleted_at.is_(None), scope.staff_filter(Task.branch_id, branch_id))
        if assigned_staff_id is not None:
            stmt = stmt.where(Task.assigned_staff_id == assigned_staff_id)
        if task_type is not None:
            stmt = stmt.where(Task.task_type == task_type)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        if params.search:
            term = f"%{params.search}%"
            stmt = stmt.where(or_(Task.title.ilike(term), Task.description.ilike(term)))
        stmt = apply_sorting(stmt, Task, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def get(self, db: Session, task_id: int, scope: BusinessScope) -> Task:
        task = db.get(Task, task_id)
        if task is None or task.deleted_at is not None or task.branch_id is None:
            raise HTTPException(status_code=404, detail="Task not found")
        try:
            scope.check_branch(db, task.branch_id)
        except HTTPException:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def _resolve_branch(
        self, db: Session, scope: BusinessScope, branch_id: int | None, assigned_staff_id: int | None
    ) -> int:
        """A task's branch: the one given, else the assignee's, else the creator's."""
        if branch_id is not None:
            return scope.check_branch(db, branch_id)
        if assigned_staff_id is not None:
            return scope.check_staff(db, assigned_staff_id).branch_id
        return scope.staff.branch_id

    def create(self, db: Session, payload: TaskCreate, scope: BusinessScope) -> Task:
        values = payload.model_dump()
        if values["assigned_staff_id"] is not None:
            scope.check_staff(db, values["assigned_staff_id"])
        values["branch_id"] = self._resolve_branch(db, scope, values.get("branch_id"), values["assigned_staff_id"])
        task = Task(**values, created_by=scope.staff.id)
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update(self, db: Session, task_id: int, payload: TaskUpdate, scope: BusinessScope) -> Task:
        task = self.get(db, task_id, scope)
        values = payload.model_dump(exclude_unset=True)
        if values.get("assigned_staff_id") is not None:
            scope.check_staff(db, values["assigned_staff_id"])
        if values.get("branch_id") is not None:
            scope.check_branch(db, values["branch_id"])
        elif "branch_id" in values:
            values.pop("branch_id")  # a task always keeps a branch
        for field, value in values.items():
            setattr(task, field, value)
        task.updated_by = scope.staff.id
        db.commit()
        db.refresh(task)
        return task

    def delete(self, db: Session, task_id: int, scope: BusinessScope) -> dict[str, int | bool]:
        task = self.get(db, task_id, scope)
        task.deleted_at = datetime.now(timezone.utc)
        task.deleted_by = scope.staff.id
        db.commit()
        return {"deleted": True, "id": task.id}
