from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.schemas.v1.staff import StaffAuthResponse, StaffCreateResponse, StaffLoginRequest, StaffRegister
from app.services.v1.staff_service import StaffService

router = APIRouter(prefix="/staffs-auth", tags=["staffs-auth"])
service = StaffService()


@router.post("/login", response_model=StaffAuthResponse)
def login(payload: StaffLoginRequest, db: Session = Depends(get_db)):
    return service.login(db, payload)


@router.post("/register", response_model=StaffCreateResponse)
def register(payload: StaffRegister, db: Session = Depends(get_db)):
    return service.register(
        db,
        payload.first_name,
        payload.last_name,
        payload.email,
        payload.password,
        payload.hotel_name,
    )


@router.post("/logout")
def logout() -> dict[str, bool]:
    return {"data": {"logged_out": True}}
