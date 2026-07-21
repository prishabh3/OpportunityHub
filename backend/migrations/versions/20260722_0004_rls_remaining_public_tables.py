"""enable RLS on the remaining public tables

The initial schema enabled RLS on the user-owned tables and `opportunities`,
but left seven tables in the public schema unprotected. Supabase exposes the
public schema over PostgREST with the anon key, so those tables were readable
and writable by anyone holding the (public) anon key.

No policies are created: nothing reaches these tables through PostgREST. The
frontend uses Supabase for auth only, and the backend connects as the postgres
role via the session pooler, which bypasses RLS.

Revision ID: 0004
Revises: 0003
Create Date: 2026-07-22 00:00:00
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0004"
down_revision: str | Sequence[str] | None = "0003"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TABLES = (
    "skills",
    "user_skills",
    "sources",
    "connector_runs",
    "tags",
    "opportunity_tags",
    "deadline_reminders_sent",
)


def upgrade() -> None:
    for table in TABLES:
        op.execute(f"alter table {table} enable row level security")


def downgrade() -> None:
    for table in TABLES:
        op.execute(f"alter table {table} disable row level security")
