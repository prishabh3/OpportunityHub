import time
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, Request, Response
from redis import RedisError
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.cache import get_redis
from app.core.client_ip import get_client_ip
from app.core.config import Settings
from app.core.exceptions import RateLimitedError, problem_response
from app.core.logging import get_logger
from app.core.security import extract_bearer_token, get_jwt_verifier

logger = get_logger(__name__)

WINDOW_SECONDS = 60

# Liveness probe — no dependencies touched, so it stays outside the budget.
_LIVENESS_PATH = "/api/v1/health"


def resolve_identity(request: Request) -> str:
    """Identify the caller for rate-limiting: by verified user id when a valid
    bearer token is present, otherwise by client IP. Shared by the global
    middleware and the per-route limiter so both bucket the same caller
    consistently (a logged-in abuser can't dodge limits by their IP rotating)."""
    authorization = request.headers.get("authorization")
    if authorization:
        try:
            user = get_jwt_verifier().verify(extract_bearer_token(authorization))
            return f"user:{user.id}"
        except Exception:
            pass  # fall through to IP for invalid/expired tokens
    return f"ip:{get_client_ip(request)}"


class RateLimiter:
    """Per-route sliding-window rate limiter (Redis sorted-set log).

    Use as a FastAPI dependency on sensitive routes::

        @router.get("/search", dependencies=[Depends(RateLimiter(times=30, scope="search"))])

    Unlike the global :class:`RateLimitMiddleware` (a coarse fixed-window budget),
    this uses a true sliding window — no boundary-burst weakness — and applies a
    tight, route-specific budget. It raises :class:`RateLimitedError`, which the
    app's exception handler renders as RFC 9457 problem+json (dependencies run
    inside the app, so handlers see the exception — unlike middleware).

    Fails open on Redis errors: an outage must not take the route down.
    """

    def __init__(self, *, times: int, scope: str, window_seconds: int = WINDOW_SECONDS) -> None:
        self._times = times
        self._scope = scope
        self._window = window_seconds

    async def __call__(
        self, request: Request, redis: Annotated[Redis, Depends(get_redis)]
    ) -> None:
        identity = resolve_identity(request)
        key = f"slidingrl:{self._scope}:{identity}"
        now_ms = int(time.time() * 1000)
        window_ms = self._window * 1000

        try:
            async with redis.pipeline(transaction=True) as pipe:
                # Drop entries older than the window, record this request, count
                # what remains, and refresh the TTL — atomically.
                pipe.zremrangebyscore(key, 0, now_ms - window_ms)
                pipe.zadd(key, {f"{now_ms}-{uuid4().hex}": now_ms})
                pipe.zcard(key)
                pipe.expire(key, self._window)
                results = await pipe.execute()
            count = int(results[2])
        except RedisError as exc:
            logger.warning(
                "rate_limit_redis_unavailable", scope=self._scope, error=repr(exc)
            )
            return  # fail open

        if count > self._times:
            logger.warning(
                "rate_limited",
                scope=self._scope,
                identity=identity,
                path=request.url.path,
                count=count,
                limit=self._times,
            )
            raise RateLimitedError(
                f"Rate limit of {self._times} requests per {self._window}s exceeded",
                limit=self._times,
                remaining=0,
                reset=self._window,
            )


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
        # Exempt only the dependency-free liveness probe (Render calls it
        # continuously). /health/ready is NOT exempt: it queries Postgres and
        # pings Redis, so leaving it unmetered gives an unauthenticated caller a
        # cheap way to amplify load onto both backing stores.
        if request.url.path.rstrip("/") == _LIVENESS_PATH:
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
            logger.warning("rate_limit_redis_unavailable", path=request.url.path, error=repr(exc))
            return await call_next(request)

        remaining = max(limit - current, 0)
        reset = WINDOW_SECONDS - (int(time.time()) % WINDOW_SECONDS)

        if current > limit:
            logger.warning(
                "rate_limited",
                scope="global",
                identity=identity,
                path=request.url.path,
                count=current,
                limit=limit,
            )
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

        return f"ip:{get_client_ip(request)}", self._settings.rate_limit_anonymous_per_minute
