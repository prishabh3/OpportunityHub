from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.session import Base

_uuid = UUID(as_uuid=False)

opportunity_type = ENUM(
    "hackathon",
    "internship",
    "full_time_job",
    "research_program",
    "competition",
    name="opportunity_type",
    create_type=False,
)
opportunity_status = ENUM(
    "upcoming", "active", "closed", "archived", name="opportunity_status", create_type=False
)
remote_type = ENUM(
    "remote", "hybrid", "onsite", "unspecified", name="remote_type", create_type=False
)
difficulty_level = ENUM(
    "beginner",
    "intermediate",
    "advanced",
    "unspecified",
    name="difficulty_level",
    create_type=False,
)
experience_level = ENUM(
    "intern", "fresher", "mid", "senior", "unspecified", name="experience_level", create_type=False
)


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[str] = mapped_column(
        _uuid, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    key: Mapped[str]
    display_name: Mapped[str]
    base_url: Mapped[str]
    opportunity_types: Mapped[list[str]] = mapped_column(ARRAY(opportunity_type))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    schedule_cron: Mapped[str] = mapped_column(server_default="0 * * * *")
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(
        _uuid, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str]
    category: Mapped[str] = mapped_column(server_default="general")


class OpportunityTag(Base):
    __tablename__ = "opportunity_tags"

    opportunity_id: Mapped[str] = mapped_column(
        _uuid, ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )
    tag_id: Mapped[str] = mapped_column(
        _uuid, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True
    )


class Opportunity(Base):
    __tablename__ = "opportunities"

    id: Mapped[str] = mapped_column(
        _uuid, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    source_id: Mapped[str] = mapped_column(_uuid, ForeignKey("sources.id"))
    external_id: Mapped[str]
    type: Mapped[str] = mapped_column(opportunity_type)
    status: Mapped[str] = mapped_column(opportunity_status, server_default="active")

    title: Mapped[str]
    organizer: Mapped[str]
    description: Mapped[str | None]
    banner_url: Mapped[str | None]

    location: Mapped[str | None]
    country: Mapped[str | None]
    remote_type: Mapped[str] = mapped_column(remote_type, server_default="unspecified")
    difficulty: Mapped[str] = mapped_column(difficulty_level, server_default="unspecified")
    experience_level: Mapped[str] = mapped_column(experience_level, server_default="unspecified")

    posted_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    deadline_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    starts_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    ends_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))

    apply_url: Mapped[str]
    source_url: Mapped[str | None]

    details: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
    content_hash: Mapped[str]

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    source: Mapped[Source] = relationship(lazy="joined")
    tags: Mapped[list[Tag]] = relationship(
        secondary="opportunity_tags", lazy="selectin", order_by="Tag.name"
    )
