from app.schemas.v1.hotel import HotelBase, HotelCreate, HotelRead, HotelUpdate
from app.schemas.v1.rooms import RoomBase, RoomCreate, RoomRead, RoomUpdate
from app.schemas.v1.bookings import BookingBase, BookingCreate, BookingRead, BookingUpdate
from app.schemas.v1.payments import PaymentBase, PaymentCreate, PaymentRead, PaymentRefund
from app.schemas.v1.staff import StaffLogin, StaffRegister, StaffAuthResponse
from app.schemas.v1.gallery import GalleryItemBase, GalleryItemCreate, GalleryItemRead
from app.schemas.v1.misc import HealthResponse, MetaResponse

__all__ = [
    "HotelBase",
    "HotelCreate",
    "HotelRead",
    "HotelUpdate",
    "RoomBase",
    "RoomCreate",
    "RoomRead",
    "RoomUpdate",
    "BookingBase",
    "BookingCreate",
    "BookingRead",
    "BookingUpdate",
    "PaymentBase",
    "PaymentCreate",
    "PaymentRead",
    "PaymentRefund",
    "StaffLogin",
    "StaffRegister",
    "StaffAuthResponse",
    "GalleryItemBase",
    "GalleryItemCreate",
    "GalleryItemRead",
    "HealthResponse",
    "MetaResponse",
]
