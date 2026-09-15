from fastapi import APIRouter, Depends
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Staff
from app.schemas.v1.common import success_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def get_dashboard(branch_id: int | None = None, db: Session = Depends(get_db)):
    stmt = select(
        func.count(Staff.id),
        func.sum(
            case(
                (func.upper(func.coalesce(Staff.status, "")) == "ACTIVE", 1),
                else_=0,
            )
        ),
    ).where(Staff.deleted_at.is_(None))
    if branch_id is not None:
        stmt = stmt.where(Staff.branch_id == branch_id)

    number_of_staff, active_staff = db.execute(stmt).one()
    number_of_staff = number_of_staff or 0
    active_staff = active_staff or 0

    return success_response({
        "numberOfStaff": number_of_staff,
        "activeStaff": active_staff,
        "inActiveStaff": number_of_staff - active_staff,
    }, message="Dashboard retrieved successfully")