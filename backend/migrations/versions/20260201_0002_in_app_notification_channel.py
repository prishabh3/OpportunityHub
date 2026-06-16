"""add in_app to notification_channel enum

Revision ID: 0002
Revises: 0001
Create Date: 2026-02-01 00:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002"
down_revision: str | Sequence[str] | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # In-app notifications use the notifications table with channel='in_app'.
    op.execute("ALTER TYPE notification_channel ADD VALUE IF NOT EXISTS 'in_app'")


def downgrade() -> None:
    # Postgres cannot drop an enum value; downgrade is a no-op.
    pass
