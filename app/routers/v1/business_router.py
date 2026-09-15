from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.pagination import ListQueryParams
from app.dependencies import get_db
from app.schemas.v1.business import BusinessCreate, BusinessRead, BusinessUpdate
from app.schemas.v1.common import success_response
from app.services.v1.business_service import BusinessService


router = APIRouter(prefix="/businesses", tags=["businesses"])
service = BusinessService()


@router.get("/")
def list_businesses(
    params: ListQueryParams = Depends(),
    db: Session = Depends(get_db),
):
    items, meta = service.list(db, params)
    data = [BusinessRead.model_validate(item) for item in items]
    return success_response(data, message="Businesses retrieved successfully", meta=meta)


@router.get("/{business_id}")
def get_business(business_id: int, db: Session = Depends(get_db)):
    business = service.get(db, business_id)
    data = BusinessRead.model_validate(business)
    return success_response(data, message="Business retrieved successfully")


@router.post("/", response_model=BusinessRead)
def create_business(payload: BusinessCreate, db: Session = Depends(get_db)):
    return service.create(db, payload)


@router.put("/{business_id}", response_model=BusinessRead)
def update_business(
    business_id: int,
    payload: BusinessUpdate,
    db: Session = Depends(get_db),
):
    return service.update(db, business_id, payload)


@router.delete("/{business_id}")
def delete_business(business_id: int, db: Session = Depends(get_db)):
    return {"data": service.delete(db, business_id)}