from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, Header
from jwt import PyJWKClient

from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError


@dataclass(frozen=True, slots=True)
class AuthenticatedUser:
    id: str
    email: str | None
    role: str


class SupabaseJWTVerifier:
    """Verifies Supabase-issued JWTs against the project's JWKS endpoint."""

    def __init__(self, jwks_url: str, audience: str) -> None:
        self._jwks_client = PyJWKClient(jwks_url, cache_keys=True)
        self._audience = audience

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
            )
        except jwt.PyJWTError as exc:
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
    )


def extract_bearer_token(authorization: str) -> str:
    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise UnauthorizedError("Expected 'Authorization: Bearer <token>' header")
    return token


async def get_current_user(
    authorization: Annotated[str, Header()],
    verifier: Annotated[SupabaseJWTVerifier, Depends(get_jwt_verifier)],
) -> AuthenticatedUser:
    token = extract_bearer_token(authorization)
    return verifier.verify(token)


async def get_current_user_optional(
    authorization: Annotated[str | None, Header()] = None,
    verifier: Annotated[SupabaseJWTVerifier, Depends(get_jwt_verifier)] = None,  # type: ignore[assignment]
) -> AuthenticatedUser | None:
    if not authorization:
        return None
    token = extract_bearer_token(authorization)
    return verifier.verify(token)


async def require_admin(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
) -> AuthenticatedUser:
    if user.role != "admin":
        raise ForbiddenError("Admin role required")
    return user
