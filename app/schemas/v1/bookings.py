from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from app.schemas.v1.guest import GuestRead
from app.schemas.v1.payments import PaymentInBookingRead
from app.schemas.v1.rooms import RoomTypeRead


class BookingRoomBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_id: int | None = None
    price_per_night: Decimal = Field(default=0, ge=0)
    check_in_date: Optional[date] = Field(
        default=None,
        validation_alias=AliasChoices("check_in_date", "checkInDate", "start_date", "startDate"),
    )
    check_out_date: Optional[date] = Field(
        default=None,
        validation_alias=AliasChoices("check_out_date", "checkOutDate", "end_date", "endDate"),
    )
    start_date: Optional[date] = Field(
        default=None,
        validation_alias=AliasChoices("start_date", "startDate"),
    )
    end_date: Optional[date] = Field(
        default=None,
        validation_alias=AliasChoices("end_date", "endDate"),
    )
    adult_count: int = Field(default=1, ge=1)
    children_count: int = Field(default=0, ge=0)
    discount: Decimal = Field(default=0, ge=0)
    tax: Decimal = Field(default=0, ge=0)
    reserved: Optional[str] = Field(default="NotReserved", max_length=50)
    temp_reserved_until: Optional[date] = None

    @field_validator("check_in_date", "check_out_date", "start_date", "end_date", "temp_reserved_until", mode="before")
    @classmethod
    def normalize_empty_date_strings(cls, value):
        if value == "":
            return None
        return value


class BookingRoomCreate(BookingRoomBase):
    pass


class BookingRoomUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    room_id: Optional[int] = None
    price_per_night: Optional[Decimal] = Field(default=None, ge=0)
    check_in_date: Optional[date] = Field(default=None, validation_alias=AliasChoices("check_in_date", "checkInDate", "start_date", "startDate"))
    check_out_date: Optional[date] = Field(default=None, validation_alias=AliasChoices("check_out_date", "checkOutDate", "end_date", "endDate"))
    start_date: Optional[date] = Field(default=None, validation_alias=AliasChoices("start_date", "startDate"))
    end_date: Optional[date] = Field(default=None, validation_alias=AliasChoices("end_date", "endDate"))
    adult_count: Optional[int] = Field(default=None, ge=1)
    children_count: Optional[int] = Field(default=None, ge=0)
    discount: Optional[Decimal] = Field(default=None, ge=0)
    tax: Optional[Decimal] = Field(default=None, ge=0)
    reserved: Optional[str] = Field(default="NotReserved", max_length=50)
    temp_reserved_until: Optional[date] = None

    @field_validator("check_in_date", "check_out_date", "start_date", "end_date", "temp_reserved_until", mode="before")
    @classmethod
    def normalize_empty_date_strings(cls, value):
        if value == "":
            return None
        return value


class BookingRoomRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: Optional[int] = None
    booking_id: Optional[int] = None
    room_id: Optional[int] = None
    price_per_night: Decimal = Decimal("0")
    check_in_date: Optional[date] = None
    check_out_date: Optional[date] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    reserved: Optional[str] = None
    temp_reserved_until: Optional[date] = None
    adult_count: int = 1
    children_count: int = 0
    number_of_nights: int = 0
    total_price: Decimal = Decimal("0")


class BookingBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    guest_id: Optional[int] = None
    branch_id: Optional[int] = None
    discount: Decimal = Field(default=0, ge=0)
    tax: Decimal = Field(default=0, ge=0)
    service_charge: Decimal = Field(default=0, ge=0)
    total_rooms: int = Field(default=1, ge=1)
    booking_status: Optional[Literal["Pending", "Booked", "Refunded", "Cancelled"]] = Field(default="Pending", max_length=50)
    payment_status: Optional[Literal["Unpaid", "PartialPaid", "CompletelyPaid"]] = Field(default="Unpaid", max_length=50)
    special_request: Optional[str] = None
    booking_source: Optional[str] = Field(default="website", max_length=50)
    staff_id: Optional[int] = None
    booking_room_params: list[BookingRoomCreate] = Field(default_factory=list, validation_alias=AliasChoices("booking_room_params", "bookingRoomParams"))


class BookingCreate(BookingBase):
    pass


class BookingUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    guest_id: Optional[int] = None
    branch_id: Optional[int] = None
    discount: Optional[Decimal] = Field(default=None, ge=0)
    tax: Optional[Decimal] = Field(default=None, ge=0)
    service_charge: Optional[Decimal] = Field(default=None, ge=0)
    total_rooms: Optional[int] = Field(default=None, ge=1)
    booking_status: Optional[Literal["Pending", "Booked", "Refunded", "Cancelled"]] = Field(default=None, max_length=50)
    payment_status: Optional[Literal["Unpaid", "PartialPaid", "CompletelyPaid"]] = Field(default=None, max_length=50)
    special_request: Optional[str] = None
    booking_source: Optional[str] = Field(default=None, max_length=50)
    staff_id: Optional[int] = None
    booking_room_params: Optional[list[BookingRoomCreate]] = Field(default=None, validation_alias=AliasChoices("booking_room_params", "bookingRoomParams"))


class BookingMetadataRead(BaseModel):
    number_of_booking_session: int = 0
    number_of_rooms_booked: int = 0
    amount_paid: Decimal = Decimal("0")
    amount_on_credit: Decimal = Decimal("0")
    distribution_by_payment_method: list[dict] = Field(default_factory=list)


class BookingRead(BaseModel):
    model_config = ConfigDict(from_attributes=True, populate_by_name=True)

    id: int
    guest_id: Optional[int] = None
    guest: Optional[GuestRead] = None
    branch_id: Optional[int] = None
    booking_reference: str
    booking_status: Optional[str] = None
    payment_status: Optional[str] = None
    total_rooms: int = 1
    subtotal: Decimal = Decimal("0")
    discount: Decimal = Decimal("0")
    tax: Decimal = Decimal("0")
    service_charge: Decimal = Decimal("0")
    grand_total: Decimal = Decimal("0")
    special_request: Optional[str] = None
    booking_source: Optional[str] = None
    payment_made: Decimal = Decimal("0")
    booking_rooms: list[BookingRoomRead] = Field(default_factory=list)
    payments: list[PaymentInBookingRead] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None


class BookingListMetadataRead(BaseModel):
    count: int = 0
    number_of_booking_session: int = 0
    number_of_rooms_booked: int = 0
    amount_paid: Decimal = Decimal("0")
    amount_on_credit: Decimal = Decimal("0")
    distribution_by_payment_method: list[dict] = Field(default_factory=list)


class BookingListResponse(BaseModel):
    data: list[BookingRead] = Field(default_factory=list)
    metadata: BookingListMetadataRead = Field(default_factory=BookingListMetadataRead)


class BookingGetResponse(BaseModel):
    data: BookingRead
    metadata: BookingMetadataRead = Field(default_factory=BookingMetadataRead)


class AvailableRoomTypeRead(BaseModel):
    room_type_id: int
    room_type_name: str
    room_type: RoomTypeRead | None = None
    available_rooms: int
    available_room_ids: list[int] = Field(default_factory=list)
    total_rooms: int
    start_date: date
    end_date: date
