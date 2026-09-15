import redis
from app.core.config import get_settings

settings = get_settings()

_redis_client: redis.Redis | None = None


def get_redis() -> redis.Redis | None:
    global _redis_client
    if not settings.REDIS_ENABLED:
        return None
    if _redis_client is None:
        _redis_client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client
