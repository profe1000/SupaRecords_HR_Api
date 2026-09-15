from fastapi import APIRouter

from .business_router import router as business_router
from .staffs_auth_router import router as staffs_auth_router
from .admin_router import router as admin_router
from .staff_router import router as staff_router
from .task_router import router as task_router
from .dashboard_router import router as dashboard_router

router = APIRouter(prefix="/v1")
router.include_router(business_router)
router.include_router(staffs_auth_router)
router.include_router(admin_router)
router.include_router(staff_router)
router.include_router(task_router)
router.include_router(dashboard_router)

__all__ = ["router"]
