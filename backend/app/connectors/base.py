"""Connector framework: each connector fetches from a source and yields
NormalizedOpportunity items; the pipeline handles validate/dedupe/upsert."""

import hashlib
import json
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.application.dtos.opportunity import (
    DifficultyLevel,
    OpportunityStatus,
    OpportunityType,
    RemoteType,
)


class SourceMeta(BaseModel):
    key: str
    display_name: str
    base_url: str
    opportunity_types: list[OpportunityType]


class NormalizedOpportunity(BaseModel):
    external_id: str
    type: OpportunityType
    status: OpportunityStatus = "active"
    title: str
    organizer: str
    description: str | None = None
    banner_url: str | None = None
    location: str | None = None
    country: str | None = None
    remote_type: RemoteType = "unspecified"
    difficulty: DifficultyLevel = "unspecified"
    deadline_at: datetime | None = None
    starts_at: datetime | None = None
    ends_at: datetime | None = None
    apply_url: str
    source_url: str | None = None
    tags: list[str] = Field(default_factory=list)
    details: dict[str, Any] = Field(default_factory=dict)

    def content_hash(self) -> str:
        """Stable hash of the meaningful fields, used to detect changes on
        re-ingest (and skip untouched rows)."""
        payload = {
            "title": self.title,
            "organizer": self.organizer,
            "status": self.status,
            "description": self.description,
            "location": self.location,
            "country": self.country,
            "remote_type": self.remote_type,
            "deadline_at": self.deadline_at.isoformat() if self.deadline_at else None,
            "starts_at": self.starts_at.isoformat() if self.starts_at else None,
            "apply_url": self.apply_url,
            "tags": sorted(self.tags),
        }
        raw = json.dumps(payload, sort_keys=True)
        return hashlib.sha256(raw.encode()).hexdigest()

    def is_valid(self) -> bool:
        return bool(self.external_id and self.title and self.apply_url and self.organizer)


class BaseConnector(ABC):
    meta: SourceMeta

    @abstractmethod
    async def fetch(self) -> list[NormalizedOpportunity]:
        """Fetch from the source and return normalized opportunities."""
