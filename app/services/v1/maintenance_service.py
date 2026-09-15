from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams, apply_sorting, paginate
from app.models import RoomMaintenanceLog
from app.schemas.v1.operations import RoomMaintenanceCreate, RoomMaintenanceUpdate


class MaintenanceService:
    def list_logs(self, db: Session, params: ListQueryParams, room_id: int | None = None, maintenance_type: str | None = None, status: str | None = None, priority: str | None = None):
        stmt = select(RoomMaintenanceLog).where(RoomMaintenanceLog.deleted_at.is_(None))
        if room_id is not None:
            stmt = stmt.where(RoomMaintenanceLog.room_id == room_id)
        if maintenance_type is not None:
            stmt = stmt.where(RoomMaintenanceLog.maintenance_type == maintenance_type)
        if status is not None:
            stmt = stmt.where(RoomMaintenanceLog.status == status)
        if priority is not None:
            stmt = stmt.where(RoomMaintenanceLog.priority == priority)
        return paginate(db, apply_sorting(stmt, RoomMaintenanceLog, params.sort_by, params.sort_order), params)

    def get_log(self, db: Session, log_id: int):
        log = db.get(RoomMaintenanceLog, log_id)
        if log is None or log.deleted_at is not None:
            raise HTTPException(status_code=404, detail="Maintenance log not found")
        return log

    def create_log(self, db: Session, payload: RoomMaintenanceCreate):
        log = RoomMaintenanceLog(**payload.model_dump())
        db.add(log); db.commit(); db.refresh(log)
        return log

    def update_log(self, db: Session, log_id: int, payload: RoomMaintenanceUpdate):
        log = self.get_log(db, log_id)
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(log, field, value)
        db.commit(); db.refresh(log)
        return log

    def delete_log(self, db: Session, log_id: int):
        log = self.get_log(db, log_id)
        log.deleted_at = datetime.now(timezone.utc)
        db.commit()
        return {"deleted": True, "id": log.id}