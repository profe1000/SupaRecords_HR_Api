from decimal import Decimal
from typing import Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class RoomImageInput(BaseModel):
    """Client only supplies the url and ordering; id/room_type_id/room_id are derived server-side."""

    image_url: str
    display_order: int = 0


class RoomImageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    image_url: str
    room_type_id: Optional[int] = None
    room_id: Optional[int] = None
    display_order: int = 0


class RoomTypeBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    branch_id: int
    name: str = Field(..., min_length=1, max_length=120)
    description: Optional[str] = None
    base_price: Decimal = Field(default=0, ge=0)
    discounted_price: Decimal = Field(default=0, ge=0)
    website_price: Decimal = Field(default=0, ge=0)
    cooperate_price: Decimal = Field(default=0, ge=0)
    max_adults: int = Field(default=1, ge=1)
    max_children: int = Field(default=0, ge=0)
    room_size: Optional[Decimal] = Field(default=None, ge=0)
    bed_type: Optional[str] = Field(default=None, max_length=100)
    total_beds: Optional[int] = Field(default=None, ge=1)
    feature_image: Optional[str] = Field(default=None, max_length=500, validation_alias=AliasChoices("feature_image", "featureImage"))
    feature_video_url: Optional[str] = Field(default=None, max_length=500, validation_alias=AliasChoices("feature_video_url", "featureVideoUrl"))
    staff_id: Optional[int] = None


class RoomTypeCreate(RoomTypeBase):
    images: list[RoomImageInput] = Field(default_factory=list)


class RoomTypeUpdate(BaseModel):
    branch_id: Optional[int] = None
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    description: Optional[str] = None
    base_price: Optional[Decimal] = Field(default=None, ge=0)
    discounted_price: Optional[Decimal] = Field(default=None, ge=0)
    website_price: Optional[Decimal] = Field(default=None, ge=0)
    cooperate_price: Optional[Decimal] = Field(default=None, ge=0)
    max_adults: Optional[int] = Field(default=None, ge=1)
    max_children: Optional[int] = Field(default=None, ge=0)
    room_size: Optional[Decimal] = Field(default=None, ge=0)
    bed_type: Optional[str] = Field(default=None, max_length=100)
    total_beds: Optional[int] = Field(default=None, ge=1)
    feature_image: Optional[str] = Field(default=None, max_length=500, validation_alias=AliasChoices("feature_image", "featureImage"))
    feature_video_url: Optional[str] = Field(default=None, max_length=500, validation_alias=AliasChoices("feature_video_url", "featureVideoUrl"))
    images: Optional[list[RoomImageInput]] = None
    staff_id: Optional[int] = None


class RoomTypeRead(RoomTypeBase):
    id: int
    images: list[RoomImageRead] = Field(default_factory=list)


class RoomBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    branch_id: int
    room_type_id: int
    room_number: str = Field(..., min_length=1, max_length=50)
    floor: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=50)
    cleaning_status: Optional[str] = Field(default=None, max_length=50)
    maintenance_note: Optional[str] = None
    is_active: bool = True
    staff_id: Optional[int] = None


class RoomCreate(RoomBase):
    images: list[RoomImageInput] = Field(default_factory=list)


class RoomUpdate(BaseModel):
    branch_id: Optional[int] = None
    room_type_id: Optional[int] = None
    room_number: Optional[str] = Field(default=None, min_length=1, max_length=50)
    floor: Optional[str] = Field(default=None, max_length=20)
    status: Optional[str] = Field(default=None, max_length=50)
    cleaning_status: Optional[str] = Field(default=None, max_length=50)
    maintenance_note: Optional[str] = None
    is_active: Optional[bool] = None
    images: Optional[list[RoomImageInput]] = None
    staff_id: Optional[int] = None


class RoomRead(RoomBase):
    id: int
    images: list[RoomImageRead] = Field(default_factory=list)
    room_type: Optional[RoomTypeRead] = None
