from typing import Any, Dict

from fastapi import APIRouter, Depends

from app.core.pagination import ListQueryParams
from app.schemas.v1.common import PaginationMeta, success_response
from app.services.v1.hotel_service import HotelService

router = APIRouter(prefix="/hotels", tags=["hotels"])
service = HotelService()


@router.get("/")
async def list_hotels(params: ListQueryParams = Depends()) -> Dict[str, Any]:
    data = await service.list_hotels()
    meta = PaginationMeta(total=len(data), page=params.page, perPage=params.per_page, totalPages=1 if data else 0)
    return success_response(data, message="Hotels retrieved successfully", meta=meta)


@router.get("/{hotel_id}")
async def get_hotel(hotel_id: int) -> Dict[str, Any]:
    data = await service.get_hotel(hotel_id)
    return success_response(data, message="Hotel retrieved successfully")


@router.post("/")
async def create_hotel(payload: Dict[str, Any]) -> Dict[str, Any]:
    data = await service.create_hotel(payload)
    return {"data": data}


@router.put("/{hotel_id}")
async def update_hotel(hotel_id: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    data = await service.update_hotel(hotel_id, payload)
    return {"data": data}


@router.delete("/{hotel_id}")
async def delete_hotel(hotel_id: int) -> Dict[str, Any]:
    data = await service.delete_hotel(hotel_id)
    return {"data": data}
