import redis.asyncio as aioredis
from typing import Optional
from app.core.config import settings

_redis_client: Optional[aioredis.Redis] = None


async def get_redis_client() -> aioredis.Redis:
    """Returns a singleton async Redis client pool."""
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.redis_url,
            decode_responses=True,
            encoding="utf-8",
        )
    return _redis_client


async def close_redis_client() -> None:
    """Closes the Redis connection pool cleanly."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None
