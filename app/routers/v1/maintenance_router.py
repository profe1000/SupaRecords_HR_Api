from typing import Any, Optional
from typing import Literal

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams
from app.dependencies import get_db
from app.schemas.v1.common import success_response
from app.schemas.v1.operations import RoomMaintenanceCreate, RoomMaintenanceUpdate
from app.services.v1.maintenance_service import MaintenanceService

router = APIRouter(prefix="/maintenance", tags=["maintenance"])
service = MaintenanceService()

def _data(record: Any): return {column.name: getattr(record, column.name) for column in record.__table__.columns}

@router.get("/")
def list_logs(
    room_id: int | None = None,
    maintenance_type: Optional[Literal["CLEANING", "REPAIRS", "REPLACE"]] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    params: ListQueryParams = Depends(),
    db: Session = Depends(get_db),
):
    items, meta = service.list_logs(db, params, room_id, maintenance_type=maintenance_type, status=status, priority=priority)
    return success_response([_data(item) for item in items], message="Maintenance logs retrieved successfully", meta=meta)
@router.post("/")
def create_log(payload: RoomMaintenanceCreate, db: Session = Depends(get_db)): return _data(service.create_log(db, payload))
@router.get("/{log_id}")
def get_log(log_id: int, db: Session = Depends(get_db)): return success_response(_data(service.get_log(db, log_id)), message="Maintenance log retrieved successfully")
@router.put("/{log_id}")
def update_log(log_id: int, payload: RoomMaintenanceUpdate, db: Session = Depends(get_db)): return _data(service.update_log(db, log_id, payload))
@router.delete("/{log_id}")
def delete_log(log_id: int, db: Session = Depends(get_db)): return service.delete_log(db, log_id)