from __future__ import annotations

from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams, apply_sorting, paginate
from app.models import Task
from app.schemas.v1.task import TaskCreate, TaskUpdate


class TaskService:
    def list(
        self,
        db: Session,
        params: ListQueryParams,
        assigned_staff_id: int | None = None,
        task_type: str | None = None,
        status: str | None = None,
        priority: str | None = None,
    ):
        stmt = select(Task).where(Task.deleted_at.is_(None))
        if assigned_staff_id is not None:
            stmt = stmt.where(Task.assigned_staff_id == assigned_staff_id)
        if task_type is not None:
            stmt = stmt.where(Task.task_type == task_type)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        if priority is not None:
            stmt = stmt.where(Task.priority == priority)
        stmt = apply_sorting(stmt, Task, params.sort_by, params.sort_order)
        return paginate(db, stmt, params)

    def get(self, db: Session, task_id: int) -> Task:
        task = db.get(Task, task_id)
        if task is None or task.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

    def create(self, db: Session, payload: TaskCreate) -> Task:
        task = Task(**payload.model_dump())
        db.add(task)
        db.commit()
        db.refresh(task)
        return task

    def update(self, db: Session, task_id: int, payload: TaskUpdate) -> Task:
        task = self.get(db, task_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(task, field, value)
        db.commit()
        db.refresh(task)
        return task

    def delete(self, db: Session, task_id: int) -> dict[str, int | bool]:
        task = self.get(db, task_id)
        task.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return {"deleted": True, "id": task.id}