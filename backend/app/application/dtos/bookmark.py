from datetime import datetime

from pydantic import BaseModel, Field

from app.application.dtos.opportunity import OpportunitySummary


class BookmarkCreate(BaseModel):
    opportunity_id: str
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)


class BookmarkRead(BaseModel):
    id: str
    opportunity_id: str
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    opportunity: OpportunitySummary
