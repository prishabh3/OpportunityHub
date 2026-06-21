from typing import Annotated

from fastapi import APIRouter, Depends, Request
from redis.asyncio import Redis

from app.application.services.traffic_service import record_ping
from app.core.cache import get_redis

router = APIRouter(prefix="/traffic", tags=["traffic"])


@router.post("/ping", status_code=204)
async def ping(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis)],
    visitor_id: str | None = None,
) -> None:
    """Called by the frontend on page load. visitor_id is a stable anonymous id
    generated client-side (stored in localStorage). Falls back to IP."""
    vid = visitor_id or (request.client.host if request.client else None) or "unknown"
    await record_ping(redis, vid)
