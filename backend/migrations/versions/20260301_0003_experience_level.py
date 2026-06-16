"""add experience_level to opportunities

Revision ID: 0003
Revises: 0002
Create Date: 2026-03-01 00:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | Sequence[str] | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        "create type experience_level as enum "
        "('intern', 'fresher', 'mid', 'senior', 'unspecified')"
    )
    op.execute(
        "alter table opportunities add column experience_level experience_level "
        "not null default 'unspecified'"
    )
    op.execute("create index idx_opportunities_experience on opportunities (experience_level)")


def downgrade() -> None:
    op.execute("drop index if exists idx_opportunities_experience")
    op.execute("alter table opportunities drop column if exists experience_level")
    op.execute("drop type if exists experience_level")
