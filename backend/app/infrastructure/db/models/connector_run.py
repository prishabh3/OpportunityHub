from datetime import datetime
from typing import Any

from sqlalchemy import ForeignKey, Integer, text
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

_uuid = UUID(as_uuid=False)

connector_run_status = ENUM(
    "success", "partial", "failed", "running", name="connector_run_status", create_type=False
)


class ConnectorRun(Base):
    __tablename__ = "connector_runs"

    id: Mapped[str] = mapped_column(
        _uuid, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    source_id: Mapped[str] = mapped_column(_uuid, ForeignKey("sources.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(connector_run_status, server_default="running")
    started_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    finished_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    items_found: Mapped[int] = mapped_column(Integer, server_default="0")
    items_created: Mapped[int] = mapped_column(Integer, server_default="0")
    items_updated: Mapped[int] = mapped_column(Integer, server_default="0")
    items_failed: Mapped[int] = mapped_column(Integer, server_default="0")
    error_message: Mapped[str | None]
    log: Mapped[dict[str, Any]] = mapped_column(JSONB, server_default=text("'{}'::jsonb"))
