"""Per-request logging context.

Binds a request id and basic request metadata (method, path, client IP) to
structlog's contextvars so *every* log line emitted while handling a request —
including the security events (rate_limited, admin_access_denied, jwt_invalid)
and unhandled-exception logs — is automatically correlated to that request.

Also echoes the id back as the ``X-Request-ID`` response header so a client
report or an alert can be traced to exact log lines.
"""

from uuid import uuid4

import structlog
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

_REQUEST_ID_HEADER = "X-Request-ID"


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Bind request-scoped context to logs and emit a correlation id."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Honor an inbound request id from the proxy/client if present (so a
        # trace can span tiers), otherwise mint one.
        request_id = request.headers.get(_REQUEST_ID_HEADER) or uuid4().hex

        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(
            request_id=request_id,
            method=request.method,
            path=request.url.path,
            client_ip=request.client.host if request.client else "unknown",
        )
        try:
            response = await call_next(request)
        finally:
            structlog.contextvars.clear_contextvars()

        response.headers[_REQUEST_ID_HEADER] = request_id
        return response
