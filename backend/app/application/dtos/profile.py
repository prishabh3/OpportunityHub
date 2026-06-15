from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

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
