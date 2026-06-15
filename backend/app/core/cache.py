from collections.abc import AsyncIterator
from functools import lru_cache

from redis.asyncio import ConnectionPool, Redis

from app.core.config import get_settings


@lru_cache
def get_redis_pool() -> ConnectionPool:
    settings = get_settings()
    return ConnectionPool.from_url(settings.redis_url, decode_responses=True)


async def get_redis() -> AsyncIterator[Redis]:
    """FastAPI dependency yielding a Redis connection from the shared pool."""

    client = Redis(connection_pool=get_redis_pool())
    try:
        yield client
    finally:
        await client.aclose()
