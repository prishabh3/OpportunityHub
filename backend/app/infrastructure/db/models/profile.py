from datetime import date, datetime

from sqlalchemy import Date, ForeignKey, SmallInteger, String, text
from sqlalchemy.dialects.postgresql import ARRAY, ENUM, TIMESTAMP, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.infrastructure.db.session import Base

# UUID columns map to Python ``str`` (as_uuid=False) but keep the native
# Postgres ``uuid`` type so comparisons/casts are correct.
_uuid = UUID(as_uuid=False)

_remote_type = ENUM(
    "remote", "hybrid", "onsite", "unspecified", name="remote_type", create_type=False
)
_user_role = ENUM("user", "admin", name="user_role", create_type=False)


class Profile(Base):
    """Maps the user-facing columns of the ``profiles`` table.

    Columns managed elsewhere (embedding, search vector, resume metadata) are
    intentionally not mapped here.
    """

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(_uuid, primary_key=True)
    full_name: Mapped[str | None]
    role: Mapped[str] = mapped_column(_user_role, server_default="user")

    expected_graduation: Mapped[date | None] = mapped_column(Date)
    preferred_role: Mapped[str | None]
    preferred_countries: Mapped[list[str]] = mapped_column(
        ARRAY(String), server_default=text("'{}'")
    )
    preferred_companies: Mapped[list[str]] = mapped_column(
        ARRAY(String), server_default=text("'{}'")
    )
    preferred_remote: Mapped[str | None] = mapped_column(_remote_type)

    weekly_digest_enabled: Mapped[bool] = mapped_column(server_default=text("true"))
    timezone: Mapped[str] = mapped_column(server_default="UTC")

    created_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )
    updated_at: Mapped[datetime] = mapped_column(
        TIMESTAMP(timezone=True), server_default=text("now()")
    )


class Skill(Base):
    __tablename__ = "skills"

    id: Mapped[str] = mapped_column(
        _uuid, primary_key=True, server_default=text("uuid_generate_v4()")
    )
    name: Mapped[str]
    category: Mapped[str | None]


class UserSkill(Base):
    __tablename__ = "user_skills"

    user_id: Mapped[str] = mapped_column(
        _uuid, ForeignKey("profiles.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id: Mapped[str] = mapped_column(
        _uuid, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    proficiency: Mapped[int | None] = mapped_column(SmallInteger)
