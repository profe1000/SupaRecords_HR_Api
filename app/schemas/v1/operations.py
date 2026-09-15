from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class RoomMaintenanceCreate(BaseModel):
    room_id: int
    assigned_staff_id: Optional[int] = None
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = None
    maintenance_type: Literal["CLEANING", "REPAIRS", "REPLACE"] = "REPAIRS"
    status: str = "OPEN"
    priority: str = "MEDIUM"


class RoomMaintenanceUpdate(BaseModel):
    assigned_staff_id: Optional[int] = None
    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = None
    maintenance_type: Optional[Literal["CLEANING", "REPAIRS", "REPLACE"]] = None
    status: Optional[str] = None
    priority: Optional[str] = None

