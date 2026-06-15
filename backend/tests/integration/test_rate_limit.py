import pytest
from httpx import ASGITransport, AsyncClient
from redis.asyncio import Redis

from app.core.cache import get_redis_pool
from app.core.config import get_settings
from app.main import app


@pytest.fixture(autouse=True)
async def _clear_rate_limit_keys() -> None:
    redis = Redis(connection_pool=get_redis_pool())
    async for key in redis.scan_iter("ratelimit:*"):
        await redis.delete(key)


async def test_rate_limit_returns_429_problem_json() -> None:
    """A throttled request must return a proper 429 (not a generic 500).

    Regression test: exceptions raised inside BaseHTTPMiddleware bypass the
    app's exception handlers, so the middleware must build the 429 response
    itself.
    """
    limit = get_settings().rate_limit_anonymous_per_minute

    transport = ASGITransport(app=app, client=("203.0.113.7", 12345))
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        last = None
        # One extra request beyond the limit to trip the throttle.
        for _ in range(limit + 1):
            last = await client.get("/api/v1/does-not-exist")

    assert last is not None
    assert last.status_code == 429
    assert last.headers["content-type"].startswith("application/problem+json")
    assert "Retry-After" in last.headers
    assert last.headers["X-RateLimit-Remaining"] == "0"

    body = last.json()
    assert body["status"] == 429
    assert body["type"].endswith("/rate-limited")
