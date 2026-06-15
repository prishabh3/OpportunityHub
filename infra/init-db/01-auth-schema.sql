-- Minimal stand-in for Supabase's managed `auth` schema, so that local
-- migrations referencing `auth.users` / `auth.uid()` apply cleanly outside
-- of Supabase. Not used in production (Supabase provides the real thing).

create schema if not exists auth;

create table if not exists auth.users (
  id uuid primary key default gen_random_uuid(),
  email text unique
);

create or replace function auth.uid() returns uuid as $$
  select nullif(current_setting('request.jwt.claim.sub', true), '')::uuid
$$ language sql stable;
