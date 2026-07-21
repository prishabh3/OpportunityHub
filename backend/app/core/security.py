import hmac
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, Header
from jwt import PyJWKClient

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    email: str | None
    role: str


class SupabaseJWTVerifier:
    """Verifies Supabase-issued JWTs against the project's JWKS endpoint."""

    def __init__(self, jwks_url: str, audience: str, issuer: str) -> None:
        self._jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        self._audience = audience
        self._issuer = issuer

    def verify(self, token: str) -> AuthenticatedUser:
        try:
            signing_key = self._jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                # Only asymmetric algorithms: keys come from the JWKS endpoint,
                # which never publishes symmetric (HS*) secrets. Allowing HS256
                # here would open a key-confusion attack against the public key.
                algorithms=["ES256", "RS256"],
                audience=self._audience,
                issuer=self._issuer,
                # Reject tokens that omit the claims we authorize on, rather
                # than treating an absent claim as "nothing to check".
                options={"require": ["exp", "sub", "aud", "iss"]},
            )
        except jwt.ExpiredSignatureError as exc:
            logger.warning("jwt_expired")
            raise UnauthorizedError("Token has expired") from exc
        except jwt.PyJWTError as exc:
            logger.warning("jwt_invalid", error=repr(exc))
            raise UnauthorizedError("Invalid or expired token") from exc

        app_metadata = payload.get("app_metadata", {})
        return AuthenticatedUser(
            id=payload["sub"],
            email=payload.get("email"),
            role=app_metadata.get("role", "user"),
        )


@lru_cache
def get_jwt_verifier() -> SupabaseJWTVerifier:
    settings = get_settings()
    return SupabaseJWTVerifier(
        jwks_url=settings.supabase_jwks_url,
        audience=settings.supabase_jwt_audience,
        issuer=settings.supabase_jwt_issuer,
    )


def extract_bearer_token(authorization: str) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Expected 'Authorization: Bearer <token>' header")
    return token


async def get_current_user(
    verifier: Annotated[SupabaseJWTVerifier, Depends(get_jwt_verifier)],
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser:
    if not authorization:
        raise UnauthorizedError("Authentication required")
    token = extract_bearer_token(authorization)
    return verifier.verify(token)


async def get_current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
) -> AuthenticatedUser | None:
    """Best-effort auth: returns None for missing or invalid tokens instead of
    raising, so public endpoints can serve both anonymous and logged-in users."""
    if not authorization:
        return None
    try:
        token = extract_bearer_token(authorization)
        return get_jwt_verifier().verify(token)
    except (UnauthorizedError, ForbiddenError):
        return None


async def require_admin(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    if user.role != "admin":
        logger.warning("admin_access_denied", user_id=user.id)
        raise ForbiddenError("Admin role required")
    logger.info("admin_access_granted", user_id=user.id)
    return user


def verify_job_token(x_ingest_token: Annotated[str | None, Header()] = None) -> None:
    """Shared-secret guard for cron-triggered jobs (ingest, notifications)."""
    settings = get_settings()
    if not settings.ingest_token:
        raise ForbiddenError("Scheduled jobs are not configured")
    if not x_ingest_token or not hmac.compare_digest(x_ingest_token, settings.ingest_token):
        raise UnauthorizedError("Invalid job token")
