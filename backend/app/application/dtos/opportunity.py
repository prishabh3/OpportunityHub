from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

OpportunityType = Literal[
    "hackathon", "internship", "full_time_job", "research_program", "competition"
]
OpportunityStatus = Literal["upcoming", "active", "closed", "archived"]
RemoteType = Literal["remote", "hybrid", "onsite", "unspecified"]
DifficultyLevel = Literal["beginner", "intermediate", "advanced", "unspecified"]


class SourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    display_name: str


class OpportunitySummary(BaseModel):
    """List-item view of an opportunity."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    type: OpportunityType
    status: OpportunityStatus
    title: str
    organizer: str
    location: str | None = None
    country: str | None = None
    remote_type: RemoteType
    difficulty: DifficultyLevel
    deadline_at: datetime | None = None
    starts_at: datetime | None = None
    apply_url: str
    banner_url: str | None = None
    tags: list[str] = []


class OpportunityDetail(OpportunitySummary):
    """Full view, including description, timestamps, source, and extra details."""

    description: str | None = None
    source_url: str | None = None
    posted_at: datetime | None = None
    ends_at: datetime | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    source: SourceRead


class OpportunityFilters(BaseModel):
    type: OpportunityType | None = None
    types: list[OpportunityType] | None = None  # category expansion (any-of)
    status: OpportunityStatus | None = None
    country: str | None = None
    remote_type: RemoteType | None = None
    difficulty: DifficultyLevel | None = None
    q: str | None = None
    tag: str | None = None
