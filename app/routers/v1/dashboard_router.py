from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.core.auth import get_current_staff
from app.core.scope import BusinessScope, get_scope
from app.dependencies import get_db
from app.models import LeaveApplication, Staff, StaffRequest, Task
from app.schemas.v1.common import success_response
from app.schemas.v1.leave import LeaveApplicationRead
from app.schemas.v1.task import TaskRead
from app.services.v1.leave_service import LeaveService

CLOSED_TASK_STATUSES = ("RESOLVED", "CLOSED")

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def get_dashboard(
    branch_id: int | None = None,
    scope: BusinessScope = Depends(get_scope),
    db: Session = Depends(get_db),
):
    """Staff counts for the whole business, or one branch when branch_id is given."""
    scope.check_branch(db, branch_id)
    stmt = select(
        func.count(Staff.id),
        func.sum(
            case(
                (func.upper(func.coalesce(Staff.status, "")) == "ACTIVE", 1),
                else_=0,
            )
        ),
    ).where(Staff.deleted_at.is_(None), scope.staff_filter(Staff.branch_id, branch_id))

    number_of_staff, active_staff = db.execute(stmt).one()
    number_of_staff = number_of_staff or 0
    active_staff = active_staff or 0

    return success_response({
        "numberOfStaff": number_of_staff,
        "activeStaff": active_staff,
        "inActiveStaff": number_of_staff - active_staff,
    }, message="Dashboard retrieved successfully")


@router.get("/me")
def get_my_dashboard(staff: Staff = Depends(get_current_staff), db: Session = Depends(get_db)):
    """Self-service summary for the logged-in staff member."""
    today = date.today()
    balance = LeaveService().balance(db, staff.id, today.year)

    next_leave = db.scalar(
        select(LeaveApplication)
        .where(
            LeaveApplication.staff_id == staff.id,
            LeaveApplication.status == "APPROVED",
            LeaveApplication.deleted_at.is_(None),
            LeaveApplication.end_date >= today,
        )
        .order_by(LeaveApplication.start_date.asc())
        .limit(1)
    )
    pending_leave = db.scalar(
        select(func.count(LeaveApplication.id)).where(
            LeaveApplication.staff_id == staff.id,
            LeaveApplication.status == "PENDING",
            LeaveApplication.deleted_at.is_(None),
        )
    ) or 0

    request_counts = dict(
        db.execute(
            select(StaffRequest.status, func.count(StaffRequest.id))
            .where(StaffRequest.staff_id == staff.id, StaffRequest.deleted_at.is_(None))
            .group_by(StaffRequest.status)
        ).all()
    )

    open_tasks_filter = (
        Task.assigned_staff_id == staff.id,
        Task.deleted_at.is_(None),
        func.upper(Task.status).notin_(CLOSED_TASK_STATUSES),
    )
    open_tasks_count = db.scalar(select(func.count(Task.id)).where(*open_tasks_filter)) or 0
    open_tasks = db.scalars(
        select(Task).where(*open_tasks_filter).order_by(Task.created_at.desc()).limit(5)
    ).all()

    return success_response({
        "leaveBalance": balance,
        "nextLeave": LeaveApplicationRead.model_validate(next_leave) if next_leave else None,
        "pendingLeaveCount": pending_leave,
        "requests": {
            "pending": request_counts.get("PENDING", 0),
            "approved": request_counts.get("APPROVED", 0),
            "rejected": request_counts.get("REJECTED", 0),
        },
        "openTasksCount": open_tasks_count,
        "openTasks": [TaskRead.model_validate(task) for task in open_tasks],
    }, message="Dashboard retrieved successfully")

