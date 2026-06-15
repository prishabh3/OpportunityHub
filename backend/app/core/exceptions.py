from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

PROBLEM_BASE_URL = "https://opportunityhub.dev/errors"


class AppError(Exception):
    """Base class for domain/application errors, mapped to RFC 9457 responses."""

    status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_type: str = "internal-error"
    title: str = "Internal Server Error"

    def __init__(self, detail: str | None = None, **extra: Any) -> None:
        self.detail = detail or self.title
        self.extra = extra
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    error_type = "not-found"
    title = "Resource not found"


class UnauthorizedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_type = "unauthorized"
    title = "Authentication required"


class ForbiddenError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    error_type = "forbidden"
    title = "You do not have permission to perform this action"


class ConflictError(AppError):
    status_code = status.HTTP_409_CONFLICT
    error_type = "conflict"
    title = "Resource conflict"


class RateLimitedError(AppError):
    status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_type = "rate-limited"
    title = "Too many requests"


def problem_response(
    *, status_code: int, error_type: str, title: str, detail: str, **extra: Any
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "type": f"{PROBLEM_BASE_URL}/{error_type}",
            "title": title,
            "status": status_code,
            "detail": detail,
            **extra,
        },
        media_type="application/problem+json",
    )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        return problem_response(
            status_code=exc.status_code,
            error_type=exc.error_type,
            title=exc.title,
            detail=exc.detail,
            **exc.extra,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        errors = [
            {"field": ".".join(str(loc) for loc in err["loc"]), "message": err["msg"]}
            for err in exc.errors()
        ]
        return problem_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            error_type="validation",
            title="Validation failed",
            detail="One or more fields failed validation",
            errors=errors,
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(_: Request, exc: Exception) -> JSONResponse:
        return problem_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            error_type="internal-error",
            title="Internal Server Error",
            detail="An unexpected error occurred",
        )
