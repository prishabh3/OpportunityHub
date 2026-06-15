from functools import lru_cache

from pydantic import AnyHttpUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration, loaded from environment variables / .env."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # General
    environment: str = Field(default="development")
    debug: bool = Field(default=False)
    api_v1_prefix: str = Field(default="/api/v1")

    # CORS
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])

    # Database
    database_url: str = Field(
        default="postgresql+asyncpg://postgres:postgres@localhost:5432/opportunityhub"
    )

    # Redis
    redis_url: str = Field(default="redis://localhost:6379/0")

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

    # Rate limiting
    rate_limit_anonymous_per_minute: int = Field(default=60)
    rate_limit_authenticated_per_minute: int = Field(default=300)
    rate_limit_admin_per_minute: int = Field(default=1000)

    @property
    def supabase_jwks_url(self) -> str:
        return f"{str(self.supabase_url).rstrip('/')}/auth/v1/.well-known/jwks.json"


@lru_cache
def get_settings() -> Settings:
    return Settings()
