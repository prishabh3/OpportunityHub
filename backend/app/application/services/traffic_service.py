"""Lightweight in-house traffic tracking backed by Redis.

- active visitors: a sorted set keyed by visitor id, scored by last-seen epoch;
  "live" = seen in the last ACTIVE_WINDOW seconds.
- total page views: a counter.
- unique visitors: a HyperLogLog (approximate distinct count).
"""

import time

from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.logging import get_logger

logger = get_logger(__name__)

_ACTIVE_KEY = "traffic:active"
_VIEWS_KEY = "traffic:pageviews"
_VISITORS_KEY = "traffic:visitors"
ACTIVE_WINDOW = 300  # seconds a visitor counts as "live"


async def record_ping(redis: Redis, visitor_id: str) -> None:
    now = int(time.time())
    try:
        async with redis.pipeline(transaction=False) as pipe:
            pipe.zadd(_ACTIVE_KEY, {visitor_id: now})
            pipe.incr(_VIEWS_KEY)
            pipe.pfadd(_VISITORS_KEY, visitor_id)
            await pipe.execute()
    except RedisError:
        logger.warning("traffic_ping_failed")  # fail open — tracking is best-effort


async def get_stats(redis: Redis) -> dict[str, int]:
    now = int(time.time())
    try:
        await redis.zremrangebyscore(_ACTIVE_KEY, 0, now - ACTIVE_WINDOW)
        active = await redis.zcard(_ACTIVE_KEY)
        views = int(await redis.get(_VIEWS_KEY) or 0)
        visitors = await redis.pfcount(_VISITORS_KEY)
    except RedisError:
        return {"active_now": 0, "pageviews": 0, "unique_visitors": 0}
    return {"active_now": active, "pageviews": views, "unique_visitors": visitors}
