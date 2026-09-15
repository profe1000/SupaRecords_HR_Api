from typing import Optional

from pydantic import BaseModel, Field


class GalleryItemBase(BaseModel):
    hotel_id: int
    image_url: str
    caption: Optional[str] = Field(default=None, max_length=300)


class GalleryItemCreate(GalleryItemBase):
    pass


class GalleryItemRead(GalleryItemBase):
    id: int
