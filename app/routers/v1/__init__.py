from fastapi import APIRouter

from .hotel_router import router as hotel_router
from .rooms_router import router as rooms_router
from .bookings_router import router as bookings_router
from .payments_router import router as payments_router
from .staffs_auth_router import router as staffs_auth_router
from .gallery_router import router as gallery_router
from .misc_router import router as misc_router
from .admin_router import router as admin_router
from .branch_router import router as branch_router
from .staff_router import router as staff_router
from .guest_router import router as guest_router
from .credits_router import router as credits_router
from .expenses_router import router as expenses_router
from .laundry_router import router as laundry_router
from .maintenance_router import router as maintenance_router
from .dashboard_router import router as dashboard_router
from .vendors_router import router as vendors_router

router = APIRouter(prefix="/v1")
router.include_router(hotel_router)
router.include_router(rooms_router)
router.include_router(bookings_router)
router.include_router(payments_router)
router.include_router(staffs_auth_router)
router.include_router(gallery_router)
router.include_router(misc_router)
router.include_router(admin_router)
router.include_router(branch_router)
router.include_router(staff_router)
router.include_router(guest_router)
router.include_router(credits_router)
router.include_router(maintenance_router)
router.include_router(expenses_router)
router.include_router(laundry_router)
router.include_router(dashboard_router)
router.include_router(vendors_router)

__all__ = ["router"]
