from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.v1.common import success_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def get_dashboard(branch_id: int | None = None, db: Session = Depends(get_db)):
    return success_response({
        "numberOfStaff": 0,
        "activeStaff": 0,
        "inActiveStaff": 0,

    }, message="Dashboard retrieved successfully")