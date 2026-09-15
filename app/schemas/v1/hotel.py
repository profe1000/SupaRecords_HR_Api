from typing import Optional

from pydantic import BaseModel, Field


class HotelBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=150)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None


class HotelCreate(HotelBase):
    pass


class HotelUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    description: Optional[str] = None


class HotelRead(HotelBase):
    id: int
