"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-01-01 00:00:00

Creates the full OpportunityHub schema (enums, tables, indexes, triggers, and
RLS policies) as designed in docs/02-database-schema.sql.

Each statement is executed individually (rather than as one multi-statement
string) because asyncpg's extended query protocol does not support multiple
commands per `execute`.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0001"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


UPGRADE_STATEMENTS: list[str] = [
    '-- =====================================================================\n-- Extensions\n-- =====================================================================\ncreate extension if not exists vector;',
    'create extension if not exists pg_trgm;',
    'create extension if not exists citext;',
    'create extension if not exists "uuid-ossp";',
    "-- =====================================================================\n-- ENUMS\n-- =====================================================================\n\ncreate type opportunity_type as enum (\n  'hackathon',\n  'internship',\n  'full_time_job',\n  'research_program',\n  'competition'\n);",
    "create type opportunity_status as enum (\n  'upcoming',\n  'active',\n  'closed',\n  'archived'\n);",
    "create type remote_type as enum ('remote', 'hybrid', 'onsite', 'unspecified');",
    "create type difficulty_level as enum ('beginner', 'intermediate', 'advanced', 'unspecified');",
    "create type user_role as enum ('user', 'admin');",
    "create type notification_channel as enum ('email', 'push', 'discord', 'telegram');",
    "create type notification_event as enum (\n  'new_match',\n  'deadline_24h',\n  'deadline_7d',\n  'deadline_changed',\n  'weekly_digest',\n  'company_alert'\n);",
    "create type connector_run_status as enum ('success', 'partial', 'failed', 'running');",
    "-- =====================================================================\n-- PROFILES (extends Supabase auth.users)\n-- =====================================================================\n\ncreate table profiles (\n  id uuid primary key references auth.users (id) on delete cascade,\n  full_name text,\n  avatar_url text,\n  role user_role not null default 'user',\n\n  expected_graduation date,\n  preferred_role text,\n  preferred_countries text[] default '{}',\n  preferred_companies text[] default '{}',\n  preferred_remote remote_type,\n\n  resume_file_path text,\n  resume_parsed_at timestamptz,\n  profile_embedding vector(1536),\n\n  weekly_digest_enabled boolean not null default true,\n  timezone text not null default 'UTC',\n\n  created_at timestamptz not null default now(),\n  updated_at timestamptz not null default now()\n);",
    'create index idx_profiles_role on profiles (role);',
    'create table skills (\n  id uuid primary key default uuid_generate_v4(),\n  name citext unique not null,\n  category text\n);',
    'create table user_skills (\n  user_id uuid not null references profiles (id) on delete cascade,\n  skill_id uuid not null references skills (id) on delete cascade,\n  proficiency smallint check (proficiency between 1 and 5),\n  primary key (user_id, skill_id)\n);',
    "-- =====================================================================\n-- DATA SOURCES & CONNECTORS\n-- =====================================================================\n\ncreate table sources (\n  id uuid primary key default uuid_generate_v4(),\n  key text unique not null,\n  display_name text not null,\n  base_url text not null,\n  opportunity_types opportunity_type[] not null,\n  is_active boolean not null default true,\n  schedule_cron text not null default '0 * * * *',\n  created_at timestamptz not null default now()\n);",
    "create table connector_runs (\n  id uuid primary key default uuid_generate_v4(),\n  source_id uuid not null references sources (id) on delete cascade,\n  status connector_run_status not null default 'running',\n  started_at timestamptz not null default now(),\n  finished_at timestamptz,\n  items_found integer not null default 0,\n  items_created integer not null default 0,\n  items_updated integer not null default 0,\n  items_failed integer not null default 0,\n  error_message text,\n  log jsonb default '{}'::jsonb\n);",
    'create index idx_connector_runs_source on connector_runs (source_id, started_at desc);',
    "-- =====================================================================\n-- OPPORTUNITIES\n-- =====================================================================\n\ncreate table opportunities (\n  id uuid primary key default uuid_generate_v4(),\n  source_id uuid not null references sources (id) on delete restrict,\n  external_id text not null,\n  type opportunity_type not null,\n  status opportunity_status not null default 'active',\n\n  title text not null,\n  organizer text not null,\n  description text,\n  banner_url text,\n\n  location text,\n  country text,\n  remote_type remote_type not null default 'unspecified',\n  difficulty difficulty_level not null default 'unspecified',\n\n  posted_at timestamptz,\n  deadline_at timestamptz,\n  starts_at timestamptz,\n  ends_at timestamptz,\n\n  apply_url text not null,\n  source_url text,\n\n  details jsonb not null default '{}'::jsonb,\n\n  embedding vector(1536),\n  search_vector tsvector,\n\n  content_hash text not null,\n\n  created_at timestamptz not null default now(),\n  updated_at timestamptz not null default now(),\n\n  constraint uq_opportunity_source_external unique (source_id, external_id)\n);",
    'create index idx_opportunities_type_status on opportunities (type, status);',
    'create index idx_opportunities_deadline on opportunities (deadline_at);',
    'create index idx_opportunities_country on opportunities (country);',
    'create index idx_opportunities_organizer on opportunities (organizer);',
    'create index idx_opportunities_search_vector on opportunities using gin (search_vector);',
    'create index idx_opportunities_embedding on opportunities using hnsw (embedding vector_cosine_ops);',
    'create index idx_opportunities_details on opportunities using gin (details);',
    "create trigger trg_opportunities_search_vector\n  before insert or update on opportunities\n  for each row execute function tsvector_update_trigger(\n    search_vector, 'pg_catalog.english', title, organizer, description\n  );",
    "create table tags (\n  id uuid primary key default uuid_generate_v4(),\n  name citext unique not null,\n  category text not null default 'general'\n);",
    'create table opportunity_tags (\n  opportunity_id uuid not null references opportunities (id) on delete cascade,\n  tag_id uuid not null references tags (id) on delete cascade,\n  primary key (opportunity_id, tag_id)\n);',
    'create index idx_opportunity_tags_tag on opportunity_tags (tag_id);',
    '-- =====================================================================\n-- BOOKMARKS\n-- =====================================================================\n\ncreate table bookmark_folders (\n  id uuid primary key default uuid_generate_v4(),\n  user_id uuid not null references profiles (id) on delete cascade,\n  name text not null,\n  created_at timestamptz not null default now(),\n  unique (user_id, name)\n);',
    "create table bookmarks (\n  id uuid primary key default uuid_generate_v4(),\n  user_id uuid not null references profiles (id) on delete cascade,\n  opportunity_id uuid not null references opportunities (id) on delete cascade,\n  folder_id uuid references bookmark_folders (id) on delete set null,\n  notes text,\n  tags text[] default '{}',\n  created_at timestamptz not null default now(),\n  unique (user_id, opportunity_id)\n);",
    'create index idx_bookmarks_user on bookmarks (user_id);',
    "-- =====================================================================\n-- NOTIFICATIONS\n-- =====================================================================\n\ncreate table notification_preferences (\n  user_id uuid primary key references profiles (id) on delete cascade,\n  channels notification_channel[] not null default '{email}',\n  events notification_event[] not null default\n    '{new_match, deadline_24h, deadline_7d, weekly_digest}',\n  discord_webhook_url text,\n  telegram_chat_id text,\n  push_subscription jsonb\n);",
    "create table notifications (\n  id uuid primary key default uuid_generate_v4(),\n  user_id uuid not null references profiles (id) on delete cascade,\n  opportunity_id uuid references opportunities (id) on delete cascade,\n  event notification_event not null,\n  channel notification_channel not null,\n  title text not null,\n  body text not null,\n  status text not null default 'pending',\n  sent_at timestamptz,\n  read_at timestamptz,\n  created_at timestamptz not null default now()\n);",
    'create index idx_notifications_user_unread on notifications (user_id, read_at);',
    'create index idx_notifications_status on notifications (status);',
    'create table deadline_reminders_sent (\n  user_id uuid not null references profiles (id) on delete cascade,\n  opportunity_id uuid not null references opportunities (id) on delete cascade,\n  event notification_event not null,\n  sent_at timestamptz not null default now(),\n  primary key (user_id, opportunity_id, event)\n);',
    "-- =====================================================================\n-- RESUME ANALYSIS\n-- =====================================================================\n\ncreate table resume_analyses (\n  id uuid primary key default uuid_generate_v4(),\n  user_id uuid not null references profiles (id) on delete cascade,\n  file_path text not null,\n  extracted_skills text[] default '{}',\n  extracted_projects jsonb default '[]'::jsonb,\n  extracted_experience jsonb default '[]'::jsonb,\n  extracted_education jsonb default '[]'::jsonb,\n  raw_text text,\n  created_at timestamptz not null default now()\n);",
    'create index idx_resume_analyses_user on resume_analyses (user_id, created_at desc);',
    "create table opportunity_matches (\n  user_id uuid not null references profiles (id) on delete cascade,\n  opportunity_id uuid not null references opportunities (id) on delete cascade,\n  match_score numeric(5, 2) not null,\n  missing_skills text[] default '{}',\n  reasoning text,\n  computed_at timestamptz not null default now(),\n  primary key (user_id, opportunity_id)\n);",
    'create index idx_opportunity_matches_user_score on opportunity_matches (user_id, match_score desc);',
    "-- =====================================================================\n-- SEARCH HISTORY\n-- =====================================================================\n\ncreate table search_history (\n  id uuid primary key default uuid_generate_v4(),\n  user_id uuid references profiles (id) on delete cascade,\n  query text not null,\n  parsed_filters jsonb default '{}'::jsonb,\n  created_at timestamptz not null default now()\n);",
    'create index idx_search_history_user on search_history (user_id, created_at desc);',
    '-- =====================================================================\n-- CALENDAR SYNC\n-- =====================================================================\n\ncreate table calendar_sync_tokens (\n  user_id uuid primary key references profiles (id) on delete cascade,\n  ics_token text not null unique,\n  google_refresh_token text,\n  created_at timestamptz not null default now()\n);',
    '-- =====================================================================\n-- ROW LEVEL SECURITY\n-- =====================================================================\n\nalter table profiles enable row level security;',
    'alter table bookmarks enable row level security;',
    'alter table bookmark_folders enable row level security;',
    'alter table notification_preferences enable row level security;',
    'alter table notifications enable row level security;',
    'alter table resume_analyses enable row level security;',
    'alter table opportunity_matches enable row level security;',
    'alter table search_history enable row level security;',
    'alter table calendar_sync_tokens enable row level security;',
    'alter table opportunities enable row level security;',
    'create policy "opportunities_public_read" on opportunities\n  for select using (true);',
    'create policy "own_profile" on profiles\n  for all using (auth.uid() = id) with check (auth.uid() = id);',
    'create policy "own_bookmarks" on bookmarks\n  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
    'create policy "own_bookmark_folders" on bookmark_folders\n  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
    'create policy "own_notification_prefs" on notification_preferences\n  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
    'create policy "own_notifications" on notifications\n  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
    'create policy "own_resume_analyses" on resume_analyses\n  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
    'create policy "own_matches" on opportunity_matches\n  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
    'create policy "own_search_history" on search_history\n  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
    'create policy "own_calendar_sync" on calendar_sync_tokens\n  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);',
    '-- =====================================================================\n-- updated_at trigger helper\n-- =====================================================================\n\ncreate or replace function set_updated_at()\nreturns trigger as $$\nbegin\n  new.updated_at = now();\n  return new;\nend;\n$$ language plpgsql;',
    'create trigger trg_profiles_updated_at before update on profiles\n  for each row execute function set_updated_at();',
    'create trigger trg_opportunities_updated_at before update on opportunities\n  for each row execute function set_updated_at();',
]

DOWNGRADE_STATEMENTS: list[str] = [
    'drop table if exists calendar_sync_tokens;',
    'drop table if exists search_history;',
    'drop table if exists opportunity_matches;',
    'drop table if exists resume_analyses;',
    'drop table if exists deadline_reminders_sent;',
    'drop table if exists notifications;',
    'drop table if exists notification_preferences;',
    'drop table if exists bookmarks;',
    'drop table if exists bookmark_folders;',
    'drop table if exists opportunity_tags;',
    'drop table if exists tags;',
    'drop table if exists opportunities;',
    'drop table if exists connector_runs;',
    'drop table if exists sources;',
    'drop table if exists user_skills;',
    'drop table if exists skills;',
    'drop table if exists profiles;',
    'drop function if exists set_updated_at();',
    'drop type if exists connector_run_status;',
    'drop type if exists notification_event;',
    'drop type if exists notification_channel;',
    'drop type if exists user_role;',
    'drop type if exists difficulty_level;',
    'drop type if exists remote_type;',
    'drop type if exists opportunity_status;',
    'drop type if exists opportunity_type;',
]


def upgrade() -> None:
    for statement in UPGRADE_STATEMENTS:
        op.execute(statement)


def downgrade() -> None:
    for statement in DOWNGRADE_STATEMENTS:
        op.execute(statement)
