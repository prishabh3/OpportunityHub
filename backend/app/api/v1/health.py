from typing import Annotated

from fastapi import APIRouter, Depends
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import get_redis
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["health"])


@router.get("/health")
async def health() -> dict[str, str]:
    """Liveness probe — no dependencies checked."""
    return {"status": "ok"}


@router.get("/health/ready")
async def health_ready(
    db: Annotated[AsyncSession, Depends(get_db_session)],
    redis: Annotated[Redis, Depends(get_redis)],
) -> dict[str, str]:
    """Readiness probe — verifies database and Redis connectivity."""

    checks = {"database": "ok", "redis": "ok"}

    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        checks["database"] = "error"

    try:
        await redis.ping()
    except Exception:
        checks["redis"] = "error"

    status_ = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return {"status": status_, **checks}
