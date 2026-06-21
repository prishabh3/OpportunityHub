"""Security-relevant HTTP response headers applied to every response.

These headers are a defence-in-depth layer — they do not replace application-level
controls but protect against a class of common browser-based attacks.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.types import ASGIApp

from app.core.config import get_settings

_HEADERS: dict[str, str] = {
    # Prevent MIME-type sniffing (drive-by download / XSS via content confusion).
    "X-Content-Type-Options": "nosniff",
    # Block framing by any other origin (clickjacking).  Modern browsers respect
    # CSP frame-ancestors; this header covers older ones.
    "X-Frame-Options": "DENY",
    # Only send the origin in the Referer header — never the full URL with path/query,
    # which can leak tokens or sensitive parameters.
    "Referrer-Policy": "strict-origin-when-cross-origin",
    # Disable hardware APIs that this API server will never use.
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=()",
    # Minimal CSP for a pure JSON API: no scripts, no styles, no frames.
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
}


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Injects security headers into every HTTP response."""

    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)
        settings = get_settings()
        self._hsts = settings.environment == "production"

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        response = await call_next(request)
        for header, value in _HEADERS.items():
            response.headers.setdefault(header, value)
        if self._hsts:
            # Only set HSTS in production — browsers cache this and cannot be reset
            # via HTTP, so setting it on a dev server breaks future HTTP access.
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=31536000; includeSubDomains; preload",
            )
        return response
