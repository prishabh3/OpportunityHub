from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.validators import sanitize_list, sanitize_text, validate_timezone

RemoteType = Literal["remote", "hybrid", "onsite", "unspecified"]


class ProfileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    full_name: str | None = None
    preferred_role: str | None = None
    preferred_companies: list[str] = Field(default_factory=list)
    preferred_countries: list[str] = Field(default_factory=list)
    preferred_remote: RemoteType | None = None
    expected_graduation: date | None = None
    weekly_digest_enabled: bool = True
    timezone: str = "UTC"
    skills: list[str] = Field(default_factory=list)


class ProfileUpdate(BaseModel):
    """Partial update. Only fields explicitly provided are applied."""

    model_config = ConfigDict(extra="forbid")

    full_name: str | None = None
    preferred_role: str | None = None
    preferred_companies: list[str] | None = None
    preferred_countries: list[str] | None = None
    preferred_remote: RemoteType | None = None
    expected_graduation: date | None = None
    weekly_digest_enabled: bool | None = None
    timezone: str | None = None
    skills: list[str] | None = None

    @field_validator("full_name", "preferred_role", mode="before")
    @classmethod
    def _sanitize_text_field(cls, v: object) -> object:
        if isinstance(v, str):
            return sanitize_text(v, max_length=100)
        return v

    @field_validator("timezone", mode="before")
    @classmethod
    def _validate_timezone(cls, v: object) -> object:
        if isinstance(v, str) and v:
            validate_timezone(v)
            if len(v) > 50:
                raise ValueError("Timezone identifier exceeds 50 characters")
        return v

    @field_validator("preferred_companies", mode="before")
    @classmethod
    def _sanitize_companies(cls, v: object) -> object:
        if isinstance(v, list):
            return sanitize_list(v, max_items=50, max_item_length=100)
        return v

    @field_validator("preferred_countries", mode="before")
    @classmethod
    def _sanitize_countries(cls, v: object) -> object:
        if isinstance(v, list):
            return sanitize_list(v, max_items=20, max_item_length=100)
        return v

    @field_validator("skills", mode="before")
    @classmethod
    def _sanitize_skills(cls, v: object) -> object:
        if isinstance(v, list):
            return sanitize_list(v, max_items=50, max_item_length=100)
        return v
