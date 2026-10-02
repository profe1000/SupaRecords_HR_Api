from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams
from app.core.scope import BusinessScope, get_scope
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
    branch_id: int | None = None,
    params: ListQueryParams = Depends(),
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    scope.check_branch(db, branch_id)
    items, meta = service.list(
        db,
        params,
        scope,
        assigned_staff_id=assigned_staff_id,
        task_type=task_type,
        status=status,
        priority=priority,
        branch_id=branch_id,
    )
    data = [TaskRead.model_validate(item) for item in items]
    return success_response(data, message="Tasks retrieved successfully", meta=meta)


@router.post("/", response_model=TaskRead)
def create_task(payload: TaskCreate, scope: BusinessScope = Depends(get_scope), db: Session = Depends(get_db)):
    return service.create(db, payload, scope)


@router.get("/{task_id}")
def get_task(task_id: int, scope: BusinessScope = Depends(get_scope), db: Session = Depends(get_db)):
    task = TaskRead.model_validate(service.get(db, task_id, scope))
    return success_response(task, message="Task retrieved successfully")


@router.put("/{task_id}", response_model=TaskRead)
def update_task(
    task_id: int,
    payload: TaskUpdate,
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    return service.update(db, task_id, payload, scope)


@router.delete("/{task_id}")
def delete_task(task_id: int, scope: BusinessScope = Depends(get_scope), db: Session = Depends(get_db)):
    return {"data": service.delete(db, task_id, scope)}
