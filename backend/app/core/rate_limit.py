import time

from fastapi import Request, Response
from redis import RedisError
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import Settings
from app.core.exceptions import RateLimitedError, problem_response
from app.core.logging import get_logger
from app.core.security import extract_bearer_token, get_jwt_verifier

logger = get_logger(__name__)

WINDOW_SECONDS = 60


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Fixed-window rate limiting backed by Redis, tiered by auth status/role.

    Identifies the caller by user id (if a valid bearer token is present) or
    by client IP otherwise, and enforces a per-minute request budget.

    Note: this middleware returns the 429 response directly rather than raising
    ``RateLimitedError``. Exceptions raised inside ``BaseHTTPMiddleware`` run
    outside the app's ``ExceptionMiddleware``, so registered exception handlers
    would never see them and the client would get a generic 500.
    """

    def __init__(self, app: ASGIApp, settings: Settings, redis: Redis) -> None:
        super().__init__(app)
        self._settings = settings
        self._redis = redis

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)

        identity, limit = await self._identify(request)
        key = f"ratelimit:{identity}:{int(time.time()) // WINDOW_SECONDS}"

        try:
            current = await self._redis.incr(key)
            if current == 1:
                # Set the window TTL only when the key is first created. Plain
                # EXPIRE (no NX flag) for the widest Redis/Upstash compatibility.
                await self._redis.expire(key, WINDOW_SECONDS)
        except RedisError as exc:
            # Fail open: a Redis outage must not take the whole API down. We log
            # the actual error and let the request through.
            logger.warning(
                "rate_limit_redis_unavailable", path=request.url.path, error=repr(exc)
            )
            return await call_next(request)

        remaining = max(limit - current, 0)
        reset = WINDOW_SECONDS - (int(time.time()) % WINDOW_SECONDS)

        if current > limit:
            error = RateLimitedError(
                f"Rate limit of {limit} requests/minute exceeded",
                limit=limit,
                remaining=0,
                reset=reset,
            )
            throttled = problem_response(
                status_code=error.status_code,
                error_type=error.error_type,
                title=error.title,
                detail=error.detail,
                **error.extra,
            )
            throttled.headers["Retry-After"] = str(reset)
            self._set_rate_limit_headers(throttled, limit=limit, remaining=0, reset=reset)
            return throttled

        response = await call_next(request)
        self._set_rate_limit_headers(response, limit=limit, remaining=remaining, reset=reset)
        return response

    @staticmethod
    def _set_rate_limit_headers(
        response: Response, *, limit: int, remaining: int, reset: int
    ) -> None:
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset)

    async def _identify(self, request: Request) -> tuple[str, int]:
        authorization = request.headers.get("authorization")
        if authorization:
            try:
                token = extract_bearer_token(authorization)
                user = get_jwt_verifier().verify(token)
                limit = (
                    self._settings.rate_limit_admin_per_minute
                    if user.role == "admin"
                    else self._settings.rate_limit_authenticated_per_minute
                )
                return f"user:{user.id}", limit
            except Exception:
                pass  # fall through to IP-based limiting for invalid tokens

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}", self._settings.rate_limit_anonymous_per_minute
