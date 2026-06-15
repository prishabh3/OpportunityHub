from httpx import ASGITransport, AsyncClient

from app.main import app


async def test_health_readiness() -> None:
    """Requires a live Postgres and Redis, as configured via DATABASE_URL/REDIS_URL."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    body = response.json()
    assert body == {"status": "ok", "database": "ok", "redis": "ok"}
