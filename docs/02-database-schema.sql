-- =====================================================================
-- OpportunityHub — Database Schema (PostgreSQL 15+ / Supabase)
-- Requires: pgvector, pg_trgm, citext extensions
-- =====================================================================

create extension if not exists vector;
create extension if not exists pg_trgm;
create extension if not exists citext;
create extension if not exists "uuid-ossp";

-- =====================================================================
-- ENUMS
-- =====================================================================

create type opportunity_type as enum (
  'hackathon',
  'internship',
  'full_time_job',
  'research_program',
  'competition'
);

create type opportunity_status as enum (
  'upcoming',   -- announced, applications not open yet
  'active',     -- accepting applications
  'closed',     -- deadline passed / filled
  'archived'    -- no longer surfaced, kept for history
);

create type remote_type as enum ('remote', 'hybrid', 'onsite', 'unspecified');

create type difficulty_level as enum ('beginner', 'intermediate', 'advanced', 'unspecified');

create type user_role as enum ('user', 'admin');

create type notification_channel as enum ('email', 'push', 'discord', 'telegram');

create type notification_event as enum (
  'new_match',           -- new opportunity matches user profile
  'deadline_24h',
  'deadline_7d',
  'deadline_changed',
  'weekly_digest',
  'company_alert'        -- e.g. "Google posted SDE internship"
);

create type connector_run_status as enum ('success', 'partial', 'failed', 'running');

-- =====================================================================
-- PROFILES (extends Supabase auth.users)
-- =====================================================================

create table profiles (
  id uuid primary key references auth.users (id) on delete cascade,
  full_name text,
  avatar_url text,
  role user_role not null default 'user',

  -- preferences
  expected_graduation date,
  preferred_role text,                 -- e.g. "Backend Engineer Intern"
  preferred_countries text[] default '{}',
  preferred_companies text[] default '{}',
  preferred_remote remote_type,

  -- resume / embedding for recommendations
  resume_file_path text,               -- Supabase Storage path
  resume_parsed_at timestamptz,
  profile_embedding vector(1536),      -- derived from skills + resume + bookmarks

  -- digest preferences
  weekly_digest_enabled boolean not null default true,
  timezone text not null default 'UTC',

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index idx_profiles_role on profiles (role);

-- skills taxonomy (normalized, reused across users and opportunities)
create table skills (
  id uuid primary key default uuid_generate_v4(),
  name citext unique not null,
  category text                       -- e.g. 'language', 'framework', 'domain'
);

create table user_skills (
  user_id uuid not null references profiles (id) on delete cascade,
  skill_id uuid not null references skills (id) on delete cascade,
  proficiency smallint check (proficiency between 1 and 5),
  primary key (user_id, skill_id)
);

-- =====================================================================
-- DATA SOURCES & CONNECTORS
-- =====================================================================

create table sources (
  id uuid primary key default uuid_generate_v4(),
  key text unique not null,            -- e.g. 'google_careers', 'devpost'
  display_name text not null,          -- e.g. 'Google Careers'
  base_url text not null,
  opportunity_types opportunity_type[] not null,
  is_active boolean not null default true,
  schedule_cron text not null default '0 * * * *',  -- celery beat schedule
  created_at timestamptz not null default now()
);

create table connector_runs (
  id uuid primary key default uuid_generate_v4(),
  source_id uuid not null references sources (id) on delete cascade,
  status connector_run_status not null default 'running',
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  items_found integer not null default 0,
  items_created integer not null default 0,
  items_updated integer not null default 0,
  items_failed integer not null default 0,
  error_message text,
  log jsonb default '{}'::jsonb
);

create index idx_connector_runs_source on connector_runs (source_id, started_at desc);

-- =====================================================================
-- OPPORTUNITIES (core entity, hybrid relational + JSONB detail)
-- =====================================================================

create table opportunities (
  id uuid primary key default uuid_generate_v4(),
  source_id uuid not null references sources (id) on delete restrict,
  external_id text not null,           -- id/slug from the source, for dedup
  type opportunity_type not null,
  status opportunity_status not null default 'active',

  title text not null,
  organizer text not null,             -- company / org / university
  description text,
  banner_url text,

  -- common, queryable fields
  location text,
  country text,
  remote_type remote_type not null default 'unspecified',
  difficulty difficulty_level not null default 'unspecified',

  -- dates
  posted_at timestamptz,
  deadline_at timestamptz,
  starts_at timestamptz,               -- event start (hackathons/competitions)
  ends_at timestamptz,

  -- links
  apply_url text not null,
  source_url text,

  -- type-specific structured data, e.g.:
  --  hackathon: { prize_pool, mode, eligibility, themes, technologies }
  --  internship/job: { salary_min, salary_max, currency, requirements, seniority }
  --  research_program: { stipend, duration_weeks, mentorship }
  --  competition: { prize_pool, leaderboard_url }
  details jsonb not null default '{}'::jsonb,

  -- search / recommendation
  embedding vector(1536),
  search_vector tsvector,

  -- dedup hash of normalized (source_id, external_id) — also unique constraint below
  content_hash text not null,

  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),

  constraint uq_opportunity_source_external unique (source_id, external_id)
);

create index idx_opportunities_type_status on opportunities (type, status);
create index idx_opportunities_deadline on opportunities (deadline_at);
create index idx_opportunities_country on opportunities (country);
create index idx_opportunities_organizer on opportunities (organizer);
create index idx_opportunities_search_vector on opportunities using gin (search_vector);
create index idx_opportunities_embedding on opportunities using hnsw (embedding vector_cosine_ops);
create index idx_opportunities_details on opportunities using gin (details);

create trigger trg_opportunities_search_vector
  before insert or update on opportunities
  for each row execute function tsvector_update_trigger(
    search_vector, 'pg_catalog.english', title, organizer, description
  );

-- tags (filter facets: AI, Web, Mobile, Blockchain, Open Source, Cloud, Hardware, ...)
create table tags (
  id uuid primary key default uuid_generate_v4(),
  name citext unique not null,
  category text not null default 'general'  -- 'domain', 'technology', 'theme'
);

create table opportunity_tags (
  opportunity_id uuid not null references opportunities (id) on delete cascade,
  tag_id uuid not null references tags (id) on delete cascade,
  primary key (opportunity_id, tag_id)
);

create index idx_opportunity_tags_tag on opportunity_tags (tag_id);

-- =====================================================================
-- BOOKMARKS
-- =====================================================================

create table bookmark_folders (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references profiles (id) on delete cascade,
  name text not null,
  created_at timestamptz not null default now(),
  unique (user_id, name)
);

create table bookmarks (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references profiles (id) on delete cascade,
  opportunity_id uuid not null references opportunities (id) on delete cascade,
  folder_id uuid references bookmark_folders (id) on delete set null,
  notes text,
  tags text[] default '{}',
  created_at timestamptz not null default now(),
  unique (user_id, opportunity_id)
);

create index idx_bookmarks_user on bookmarks (user_id);

-- =====================================================================
-- NOTIFICATIONS
-- =====================================================================

create table notification_preferences (
  user_id uuid primary key references profiles (id) on delete cascade,
  channels notification_channel[] not null default '{email}',
  events notification_event[] not null default
    '{new_match, deadline_24h, deadline_7d, weekly_digest}',
  discord_webhook_url text,
  telegram_chat_id text,
  push_subscription jsonb
);

create table notifications (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references profiles (id) on delete cascade,
  opportunity_id uuid references opportunities (id) on delete cascade,
  event notification_event not null,
  channel notification_channel not null,
  title text not null,
  body text not null,
  status text not null default 'pending',  -- pending | sent | failed
  sent_at timestamptz,
  read_at timestamptz,
  created_at timestamptz not null default now()
);

create index idx_notifications_user_unread on notifications (user_id, read_at);
create index idx_notifications_status on notifications (status);

-- tracks which (user, opportunity, event) reminders were already fired,
-- so deadline checkers don't double-send
create table deadline_reminders_sent (
  user_id uuid not null references profiles (id) on delete cascade,
  opportunity_id uuid not null references opportunities (id) on delete cascade,
  event notification_event not null,
  sent_at timestamptz not null default now(),
  primary key (user_id, opportunity_id, event)
);

-- =====================================================================
-- RESUME ANALYSIS
-- =====================================================================

create table resume_analyses (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid not null references profiles (id) on delete cascade,
  file_path text not null,
  extracted_skills text[] default '{}',
  extracted_projects jsonb default '[]'::jsonb,
  extracted_experience jsonb default '[]'::jsonb,
  extracted_education jsonb default '[]'::jsonb,
  raw_text text,
  created_at timestamptz not null default now()
);

create index idx_resume_analyses_user on resume_analyses (user_id, created_at desc);

-- per-opportunity match results (cached, refreshed periodically / on demand)
create table opportunity_matches (
  user_id uuid not null references profiles (id) on delete cascade,
  opportunity_id uuid not null references opportunities (id) on delete cascade,
  match_score numeric(5, 2) not null,     -- 0-100
  missing_skills text[] default '{}',
  reasoning text,
  computed_at timestamptz not null default now(),
  primary key (user_id, opportunity_id)
);

create index idx_opportunity_matches_user_score on opportunity_matches (user_id, match_score desc);

-- =====================================================================
-- SEARCH HISTORY (feeds recommendation engine)
-- =====================================================================

create table search_history (
  id uuid primary key default uuid_generate_v4(),
  user_id uuid references profiles (id) on delete cascade,
  query text not null,
  parsed_filters jsonb default '{}'::jsonb,
  created_at timestamptz not null default now()
);

create index idx_search_history_user on search_history (user_id, created_at desc);

-- =====================================================================
-- CALENDAR SYNC
-- =====================================================================

create table calendar_sync_tokens (
  user_id uuid primary key references profiles (id) on delete cascade,
  ics_token text not null unique,        -- secret token for /calendar/{token}.ics
  google_refresh_token text,             -- encrypted at rest
  created_at timestamptz not null default now()
);

-- =====================================================================
-- ROW LEVEL SECURITY
-- =====================================================================

alter table profiles enable row level security;
alter table bookmarks enable row level security;
alter table bookmark_folders enable row level security;
alter table notification_preferences enable row level security;
alter table notifications enable row level security;
alter table resume_analyses enable row level security;
alter table opportunity_matches enable row level security;
alter table search_history enable row level security;
alter table calendar_sync_tokens enable row level security;

-- Reference, connector and derived tables: RLS on with no policies, so they are
-- unreachable over PostgREST (anon/authenticated). The backend reaches them as
-- the postgres role, which bypasses RLS.
alter table skills enable row level security;
alter table user_skills enable row level security;
alter table sources enable row level security;
alter table connector_runs enable row level security;
alter table tags enable row level security;
alter table opportunity_tags enable row level security;
alter table deadline_reminders_sent enable row level security;

-- opportunities is public read; writes go through the backend only
alter table opportunities enable row level security;
create policy "opportunities_public_read" on opportunities
  for select using (true);

create policy "own_profile" on profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

create policy "own_bookmarks" on bookmarks
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_bookmark_folders" on bookmark_folders
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_notification_prefs" on notification_preferences
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_notifications" on notifications
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_resume_analyses" on resume_analyses
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_matches" on opportunity_matches
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_search_history" on search_history
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

create policy "own_calendar_sync" on calendar_sync_tokens
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- =====================================================================
-- updated_at trigger helper
-- =====================================================================

create or replace function set_updated_at()
returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger trg_profiles_updated_at before update on profiles
  for each row execute function set_updated_at();

create trigger trg_opportunities_updated_at before update on opportunities
  for each row execute function set_updated_at();
