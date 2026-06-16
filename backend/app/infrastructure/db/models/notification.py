from datetime import datetime

from sqlalchemy import ForeignKey, text
from sqlalchemy.dialects.postgresql import ENUM, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

_uuid = UUID(as_uuid=False)

notification_event = ENUM(
    "new_match",
    "deadline_24h",
    "deadline_7d",
    "deadline_changed",
    "weekly_digest",
    "company_alert",
    name="notification_event",
    create_type=False,
)
notification_channel = ENUM(
    "email", "push", "discord", "telegram", "in_app", name="notification_channel", create_type=False
)


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(
        _uuid, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    user_id: Mapped[str] = mapped_column(_uuid, ForeignKey("profiles.id", ondelete="CASCADE"))
    opportunity_id: Mapped[str | None] = mapped_column(
        _uuid, ForeignKey("opportunities.id", ondelete="CASCADE")
    )
    event: Mapped[str] = mapped_column(notification_event)
    channel: Mapped[str] = mapped_column(notification_channel)
    title: Mapped[str]
    body: Mapped[str]
    status: Mapped[str] = mapped_column(server_default="pending")
    sent_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    read_at: Mapped[datetime | None] = mapped_column(TIMESTAMP(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )


class DeadlineReminderSent(Base):
    __tablename__ = "deadline_reminders_sent"

    user_id: Mapped[str] = mapped_column(
        _uuid, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    opportunity_id: Mapped[str] = mapped_column(
        _uuid, ForeignKey("opportunities.id", ondelete="CASCADE"), primary_key=True
    )
    event: Mapped[str] = mapped_column(notification_event, primary_key=True)
    sent_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
