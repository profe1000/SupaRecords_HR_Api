from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models import Booking, BookingRoom, Guest, Room
from app.schemas.v1.common import success_response

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/")
def get_dashboard(branch_id: int | None = None, db: Session = Depends(get_db)):
    today = date.today()
    thirty_days_ago = today - timedelta(days=30)
    recent_bookings = select(func.date(BookingRoom.created_at).label("date"), func.count(BookingRoom.id).label("count")).join(Booking).where(
        BookingRoom.created_at >= thirty_days_ago,
        Booking.deleted_at.is_(None),
    ).group_by(func.date(BookingRoom.created_at)).order_by(func.date(BookingRoom.created_at))
    occupied = select(func.count(BookingRoom.id)).join(Booking).where(
        BookingRoom.start_date <= today,
        BookingRoom.end_date >= today,
        Booking.booking_status.in_(["Booked", "Pending"]),
    )
    total_rooms = select(func.count(Room.id)).where(Room.deleted_at.is_(None))
    if branch_id is not None:
        recent_bookings = recent_bookings.where(Booking.branch_id == branch_id)
        occupied = occupied.where(Booking.branch_id == branch_id)
        total_rooms = total_rooms.where(Room.branch_id == branch_id)

    recent_checkins = select(BookingRoom, Booking, Room).join(Booking).join(Room).where(
        BookingRoom.check_in_date.is_not(None),
        BookingRoom.check_in_date <= today,
    ).order_by(BookingRoom.check_in_date.desc()).limit(10)
    if branch_id is not None:
        recent_checkins = recent_checkins.where(Booking.branch_id == branch_id)

    top_customers = select(
        Guest.id, Guest.first_name, Guest.last_name, Guest.email,
        func.count(Booking.id).label("bookings"), func.coalesce(func.sum(Booking.grand_total), 0).label("amount"),
    ).join(Booking).where(Booking.created_at >= thirty_days_ago, Booking.deleted_at.is_(None)).group_by(Guest.id).order_by(func.sum(Booking.grand_total).desc()).limit(10)
    if branch_id is not None:
        top_customers = top_customers.where(Booking.branch_id == branch_id)

    occupied_count = db.scalar(occupied) or 0
    room_count = db.scalar(total_rooms) or 0
    checkins = [
        {"booking_id": booking.id, "booking_reference": booking.booking_reference, "check_in_date": record.check_in_date, "room": {"id": room.id, "room_number": room.room_number, "floor": room.floor}}
        for record, booking, room in db.execute(recent_checkins).all()
    ]
    customers = [
        {"guest_id": guest_id, "first_name": first_name, "last_name": last_name, "email": email, "bookings": bookings, "amount": amount}
        for guest_id, first_name, last_name, email, bookings, amount in db.execute(top_customers).all()
    ]
    # build a dict of date -> count from the grouped query
    rows = db.execute(recent_bookings).all()
    day_counts: dict[str, int] = {}
    for row in rows:
        row_date = row.date
        # normalize row_date to ISO string
        if hasattr(row_date, "isoformat"):
            key = row_date.isoformat()
        else:
            key = str(row_date)
        day_counts[key] = int(row.count or 0)

    # produce list for the last 30 days (inclusive of today)
    days_list = []
    span = (today - thirty_days_ago).days
    for i in range(span + 1):
        d = thirty_days_ago + timedelta(days=i)
        key = d.isoformat()
        days_list.append({"date": key, "num": day_counts.get(key, 0)})

    return success_response({
        "rooms_booked_last_30_days": days_list,
        "rooms_occupied_presently": occupied_count,
        "rooms_not_occupied_presently": max(room_count - occupied_count, 0),
        "recent_check_ins": checkins,
        "top_customers_last_30_days": customers,
    }, message="Dashboard retrieved successfully")