from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.application.dtos.opportunity import OpportunitySummary
from app.core.validators import sanitize_list, sanitize_text, validate_uuid


class BookmarkCreate(BaseModel):
    opportunity_id: str
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("opportunity_id", mode="before")
    @classmethod
    def _validate_opportunity_id(cls, v: object) -> object:
        if isinstance(v, str):
            validate_uuid(v)
        return v

    @field_validator("notes", mode="before")
    @classmethod
    def _sanitize_notes(cls, v: object) -> object:
        if isinstance(v, str):
            return sanitize_text(v, max_length=2000)
        return v

    @field_validator("tags", mode="before")
    @classmethod
    def _sanitize_tags(cls, v: object) -> object:
        if isinstance(v, list):
            cleaned = sanitize_list(v, max_items=10, max_item_length=50)
            return cleaned if cleaned is not None else []
        return v


class BookmarkRead(BaseModel):
    id: str
    opportunity_id: str
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    opportunity: OpportunitySummary
