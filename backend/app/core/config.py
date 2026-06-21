import json
from functools import lru_cache
from typing import Annotated
from urllib.parse import quote

from pydantic import AnyHttpUrl, Field, field_validator
from pydantic_settings import BaseSettings, NoDecode, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    api_v1_prefix: str = Field(default="/api/v1")

    # CORS — accepts a JSON array (["https://a.com"]), a comma-separated list,
    # or a single origin. `NoDecode` disables pydantic-settings' automatic JSON
    # parsing so the validator below can handle all of these forms.
    cors_origins: Annotated[list[str], NoDecode] = Field(
        default_factory=lambda: ["http://localhost:3000"]
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value: object) -> list[str]:
        if value is None or value == "":
            return ["http://localhost:3000"]
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("["):
                parsed = json.loads(text)
                return [str(origin) for origin in parsed]
            return [origin.strip() for origin in text.split(",") if origin.strip()]
        return value  # type: ignore[return-value]

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/opportunityhub"
    )

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url(cls, value: object) -> object:
        """Make a pasted Postgres URL robust:
        1. force the async driver (``postgresql+asyncpg://``) so it doesn't fall
           back to psycopg2;
        2. URL-encode the user/password so special characters in the password
           (``@ : / # ...``) don't corrupt host parsing.
        """
        if not isinstance(value, str):
            return value

        url = value.strip()
        for prefix in ("postgresql://", "postgres://"):
            if url.startswith(prefix):
                url = "postgresql+asyncpg://" + url[len(prefix) :]
                break

        scheme = "postgresql+asyncpg://"
        if not url.startswith(scheme):
            return url

        rest = url[len(scheme) :]
        if "@" in rest:
            userinfo, _, hostpart = rest.rpartition("@")  # host has no '@'
            if userinfo:
                user, sep, password = userinfo.partition(":")  # user has no ':'
                encoded = quote(user, safe="")
                if sep:
                    encoded += ":" + quote(password, safe="")
                rest = f"{encoded}@{hostpart}"
        return scheme + rest

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

    # Ingestion — shared secret for the /ingest/run endpoint (cron/manual trigger).
    ingest_token: str | None = Field(default=None)

    # Supabase Auth
    supabase_url: AnyHttpUrl = Field(default="https://placeholder.supabase.co")  # type: ignore[assignment]
    supabase_jwt_audience: str = Field(default="authenticated")

    # Meilisearch
    meilisearch_url: str = Field(default="http://localhost:7700")
    meilisearch_api_key: str = Field(default="masterKey")

    # AI / Embeddings
    ai_features_enabled: bool = Field(default=False)
    llm_api_key: str | None = Field(default=None)
    embedding_model: str = Field(default="text-embedding-3-small")

    # Rate limiting — global per-identity budget (fixed window, RateLimitMiddleware)
    rate_limit_anonymous_per_minute: int = Field(default=60)
    rate_limit_authenticated_per_minute: int = Field(default=300)
    rate_limit_admin_per_minute: int = Field(default=1000)

    # Rate limiting — stricter per-route budgets (sliding window, RateLimiter dependency).
    # These layer *under* the global budget to protect specific expensive/abusable
    # routes from scraping, spam, and DoS regardless of the global tier.
    rate_limit_search_per_minute: int = Field(default=30)
    rate_limit_write_per_minute: int = Field(default=40)
    rate_limit_ping_per_minute: int = Field(default=20)

    @property
    def supabase_jwks_url(self) -> str:
        return f"{str(self.supabase_url).rstrip('/')}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
