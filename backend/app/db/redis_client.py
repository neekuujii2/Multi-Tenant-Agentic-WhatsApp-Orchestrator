"""
Redis async client with connection pooling.
Provides a singleton pool reused across all requests.
Falls back gracefully if Redis is unavailable.
"""
import redis.asyncio as aioredis
from app.config import settings
from app.utils.logger import get_logger

log = get_logger(__name__)

_pool: aioredis.ConnectionPool | None = None
_redis: aioredis.Redis | None = None


async def connect_redis() -> None:
    """Initialize Redis connection pool."""
    global _pool, _redis
    _pool = aioredis.ConnectionPool.from_url(
        settings.redis_url,
        max_connections=20,
        decode_responses=True,
    )
    _redis = aioredis.Redis(connection_pool=_pool)
    await _redis.ping()
    log.info("redis_connected")


async def disconnect_redis() -> None:
    """Close Redis connection pool cleanly."""
    global _redis, _pool
    if _redis:
        await _redis.aclose()
    if _pool:
        await _pool.aclose()
    log.info("redis_disconnected")


def get_redis() -> aioredis.Redis:
    """Return the singleton Redis client."""
    return _redis
