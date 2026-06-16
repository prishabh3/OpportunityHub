from datetime import datetime

from sqlalchemy import ForeignKey, String, text
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.db.models.opportunity import Opportunity
from app.infrastructure.db.session import Base

_uuid = UUID(as_uuid=False)


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[str] = mapped_column(
        _uuid, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id: Mapped[str] = mapped_column(_uuid, ForeignKey("profiles.id", ondelete="CASCADE"))
    opportunity_id: Mapped[str] = mapped_column(
        _uuid, ForeignKey("opportunities.id", ondelete="CASCADE")
    )
    folder_id: Mapped[str | None] = mapped_column(_uuid)
    notes: Mapped[str | None]
    tags: Mapped[list[str]] = mapped_column(ARRAY(String), server_default=text("'{}'"))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )

    opportunity: Mapped[Opportunity] = relationship(lazy="joined")
