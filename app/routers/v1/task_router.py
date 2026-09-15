from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams
from app.dependencies import get_db
from app.schemas.v1.common import success_response
from app.schemas.v1.task import TaskCreate, TaskRead, TaskUpdate
from app.services.v1.task_service import TaskService


router = APIRouter(prefix="/tasks", tags=["tasks"])
service = TaskService()


@router.get("/")
def list_tasks(
    assigned_staff_id: int | None = None,
    task_type: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    params: ListQueryParams = Depends(),
    db: Session = Depends(get_db),
):
    items, meta = service.list(
        db,
        params,
        assigned_staff_id=assigned_staff_id,
        task_type=task_type,
        status=status,
        priority=priority,
    )
    data = [TaskRead.model_validate(item) for item in items]
    return success_response(data, message="Tasks retrieved successfully", meta=meta)


@router.post("/", response_model=TaskRead)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db)):
    task = TaskRead.model_validate(service.get(db, task_id))
    return success_response(task, message="Task retrieved successfully")


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    db: Session = Depends(get_db),
):
    return service.update(db, task_id, payload)


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    return {"data": service.delete(db, task_id)}