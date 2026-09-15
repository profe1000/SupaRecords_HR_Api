from typing import Any, Dict


class MiscService:
    async def health_check(self) -> Dict[str, Any]:
        return {"status": "ok"}

    async def app_meta(self) -> Dict[str, Any]:
        return {"service": "hotel-management-api", "version": "v1"}
