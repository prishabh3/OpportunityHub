# OpportunityHub

**OpportunityHub** is an Opportunity Intelligence Platform for engineering students and software
engineers: a continuously-updating aggregation and recommendation engine for hackathons,
internships, full-time jobs, research programs, and competitions.

The core value isn't the listing UI — it's the **ingestion pipeline** (per-source connectors that
keep data fresh and deduplicated) and the **intelligence layer** (resume-aware matching, deadline
intelligence, semantic search, notifications).

## Design docs

Full architecture, schema, and roadmap live in [`docs/`](docs/):

| Doc | Covers |
| --- | --- |
| [01-architecture.md](docs/01-architecture.md) | System architecture, component responsibilities, deployment topology |
| [02-database-schema.sql](docs/02-database-schema.sql) | PostgreSQL/Supabase schema (tables, enums, indexes, RLS) |
| [03-api-design.md](docs/03-api-design.md) | REST API design, pagination, error format, rate limits |
| [04-scraper-architecture.md](docs/04-scraper-architecture.md) | Connector framework, pipeline, scheduling |
| [05-notification-architecture.md](docs/05-notification-architecture.md) | Notification channels, events, fan-out |
| [06-recommendation-architecture.md](docs/06-recommendation-architecture.md) | Resume analyzer, match scoring, embeddings, semantic search |
| [07-authentication.md](docs/07-authentication.md) | Supabase Auth flow, JWT verification, RLS |
| [08-folder-structure.md](docs/08-folder-structure.md) | Monorepo layout |
| [09-roadmap.md](docs/09-roadmap.md) | Milestones M0–M10 |

## Stack

- **Frontend**: Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion,
  TanStack Query, React Hook Form + Zod.
- **Backend**: FastAPI, SQLAlchemy 2.0 (async) + asyncpg, Alembic, Celery, Redis, structlog.
- **Data**: PostgreSQL (Supabase) + pgvector, Meilisearch.
- **Auth**: Supabase Auth (email, Google, GitHub) — backend verifies JWTs via JWKS, never issues
  tokens.

## Local development

### 1. Start infra (Postgres + pgvector, Redis, Meilisearch)

```bash
cd infra
docker compose up -d
```

This also applies [`init-db/01-auth-schema.sql`](infra/init-db/01-auth-schema.sql), a minimal
local stand-in for Supabase's managed `auth` schema (`auth.users`, `auth.uid()`) so migrations
referencing it apply on plain Postgres.

### 2. Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env   # adjust DATABASE_URL port etc. if needed
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

Health checks: `GET /api/v1/health` (liveness), `GET /api/v1/health/ready` (DB + Redis).

Lint / type-check / test:

```bash
.venv/bin/ruff check .
.venv/bin/mypy app
.venv/bin/pytest -q
```

### 3. Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.local.example .env.local   # fill in Supabase project URL/anon key
npm run dev
```

Lint / type-check / build:

```bash
npm run lint
npm run typecheck
npm run build
```

## Roadmap

Implementation proceeds milestone by milestone (see
[09-roadmap.md](docs/09-roadmap.md)):

- **M0 — Foundations & Scaffolding** ✅ monorepo, docker-compose infra, FastAPI skeleton with
  health checks, Next.js skeleton with dark theme, initial Alembic migration, CI.
- **M1 — Auth & User Profiles**
- **M2 — Opportunities Core** (manual seed data, list/detail, filters)
- **M3 — Connector Framework + First Connectors**
- **M4 — Search**
- **M5 — Bookmarks, Folders, Calendar**
- **M6 — Notifications**
- **M7 — AI: Resume Analyzer + Recommendations**
- **M8 — Semantic Search & New-Match Notifications**
- **M9 — Admin Analytics & Polish**
- **M10 — Deployment & Hardening**
