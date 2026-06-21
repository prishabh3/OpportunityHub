from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis

from app.api.v1.router import api_router
from app.core.cache import get_redis_pool
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging, get_logger
from app.core.rate_limit import RateLimitMiddleware
from app.core.request_context import RequestContextMiddleware
from app.core.security_headers import SecurityHeadersMiddleware

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    configure_logging(debug=settings.debug)
    logger.info("startup", environment=settings.environment)
    yield
    logger.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="OpportunityHub API",
        version="0.1.0",
        lifespan=lifespan,
        debug=settings.debug,
    )

    # CORS — restrict to explicit origin list, methods, and the three headers this
    # API actually uses.  Wildcards (*) would allow any third-party site to make
    # credentialed cross-origin requests, defeating CORS as a security boundary.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Ingest-Token"],
        expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
    )

    redis = Redis(connection_pool=get_redis_pool())
    app.add_middleware(RateLimitMiddleware, settings=settings, redis=redis)

    # Security headers added after rate limiting so they're applied to 429s too.
    app.add_middleware(SecurityHeadersMiddleware)

    # Request context is added last → outermost → runs first, so the request_id
    # and request metadata are bound before any other middleware (rate limiting,
    # security headers) or handler emits a log line.
    app.add_middleware(RequestContextMiddleware)

    register_exception_handlers(app)

    app.include_router(api_router, prefix=settings.api_v1_prefix)

    return app


app = create_app()
