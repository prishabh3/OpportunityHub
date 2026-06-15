# OpportunityHub — System Architecture

## 1. Vision

OpportunityHub is an **Opportunity Intelligence Platform**: a continuously-updating aggregation
and recommendation engine for hackathons, internships, full-time jobs, research programs, and
competitions. The core value isn't the listing UI (that's table stakes) — it's the **ingestion
pipeline** (connectors that keep data fresh and deduplicated) and the **intelligence layer**
(matching, scoring, notifications, semantic search).

## 2. High-Level Components

```
                                   ┌─────────────────────────┐
                                   │        Vercel           │
                                   │  Next.js 15 Frontend     │
                                   │  (App Router, RSC)       │
                                   └────────────┬─────────────┘
                                                │ HTTPS / REST (JSON)
                                                ▼
                                   ┌─────────────────────────┐
                                   │       Railway           │
                                   │   FastAPI Backend        │
                                   │ (REST API, Auth verify,  │
                                   │  Recommendation API)     │
                                   └──┬──────────┬───────────┘
                       ┌──────────────┘          └─────────────────┐
                       ▼                                            ▼
          ┌─────────────────────────┐                ┌──────────────────────────┐
          │   PostgreSQL (Supabase) │                │        Redis              │
          │   + pgvector extension  │◄───────────────┤  - Celery broker/backend   │
          │   - core relational data│                │  - API response cache      │
          │   - vector embeddings   │                │  - rate limiting buckets   │
          │   - RLS for auth        │                └──────────┬─────────────────┘
          └────────────┬─────────────┘                          │
                       │                                          ▼
                       │                              ┌──────────────────────────┐
                       │                              │     Celery Workers        │
                       │                              │  - Connector tasks (beat) │
                       │                              │  - Notification tasks     │
                       │                              │  - Embedding tasks        │
                       │                              │  - Resume parsing tasks   │
                       │                              └──────────┬─────────────────┘
                       │                                          │
                       ▼                                          ▼
          ┌─────────────────────────┐                ┌──────────────────────────┐
          │      Meilisearch         │                │   External Sources        │
          │  - full text + facets    │                │  Google/Microsoft/Amazon/ │
          │  - synced from Postgres  │                │  Devpost/MLH/Unstop/...   │
          └─────────────────────────┘                └──────────────────────────┘

          ┌─────────────────────────┐
          │   Supabase Storage       │
          │  - resumes, banners      │
          └─────────────────────────┘

          ┌─────────────────────────┐
          │   Supabase Auth          │
          │  - email, Google, GitHub │
          │  - issues JWTs (JWKS)    │
          └─────────────────────────┘
```

## 3. Component Responsibilities

### 3.1 Frontend (Next.js 15 / React 19 / TypeScript)
- Server Components for data-heavy pages (opportunity feeds, detail pages) — SEO + performance.
- Client Components for interactive pieces (filters, bookmarks, dashboard widgets).
- TanStack Query for client-side cache of paginated/cursor APIs, optimistic bookmark updates.
- Zod schemas shared (via a `packages/shared-types` or codegen from OpenAPI) for form validation
  and API response typing.
- Supabase JS client for auth session management (cookies via `@supabase/ssr`).

### 3.2 Backend (FastAPI)
- Stateless REST API behind `/api/v1`.
- Verifies Supabase JWTs (JWKS) on every request — no session state in the API layer.
- Clean architecture layering (see folder structure doc):
  - `api/` — routers, request/response schemas (Pydantic)
  - `domain/` — entities, value objects, domain services
  - `application/` — use cases / services, DTOs
  - `infrastructure/` — SQLAlchemy repositories, external clients, Meilisearch/Redis adapters
- Dependency Injection via FastAPI `Depends` + a small DI container for repositories/services.

### 3.3 Database (PostgreSQL via Supabase + pgvector)
- Single source of truth for all relational data.
- `pgvector` columns store embeddings for opportunities and user profiles for semantic
  search/recommendations.
- Row-Level Security (RLS) enforces per-user access to bookmarks, profiles, notifications —
  defense in depth even though FastAPI also authorizes.

### 3.4 Search (Meilisearch)
- Denormalized `opportunities` documents synced via a Celery task on create/update.
- Powers fast filter+facet UI (difficulty, tags, country, remote, prize range) and free-text
  search. Semantic search (natural language queries) is handled by pgvector + an LLM query
  parser in the backend, falling back to Meilisearch for keyword matches.

### 3.5 Cache & Queue (Redis)
- Celery broker + result backend.
- API-level caching for expensive aggregate queries (trending, recommendation lists) with short
  TTLs (1–5 min).
- Token-bucket rate limiting per user/IP (via `slowapi` or custom middleware).

### 3.6 Background Workers (Celery)
- **Connector tasks**: scheduled via Celery Beat, one task per connector, isolated failure domains.
- **Pipeline tasks**: normalize → validate → deduplicate → upsert → enqueue embedding + search
  sync + notification fan-out.
- **Notification tasks**: digest builder, deadline checker (runs hourly), channel senders.
- **AI tasks**: resume parsing, embedding generation, recommendation refresh.

### 3.7 Auth (Supabase Auth)
- Email/password, Google OAuth, GitHub OAuth handled entirely by Supabase Auth.
- Frontend obtains session JWT; FastAPI validates signature against Supabase JWKS endpoint and
  extracts `sub` (user id) + custom claims (role: `user` | `admin`).

## 4. Cross-Cutting Concerns

| Concern | Approach |
|---|---|
| Logging | Structured JSON logs (`structlog`) with request-id correlation, shipped to Railway logs / optional Logtail |
| Error handling | Domain exceptions → mapped to HTTP problem-details responses via FastAPI exception handlers |
| Rate limiting | Redis token bucket per `user_id`/IP, tiered (anon vs authenticated vs admin) |
| Caching | Redis read-through cache for hot list endpoints; cache invalidation on connector upsert |
| Pagination | Cursor-based (opaque base64 cursor encoding `(sort_value, id)`) for all list endpoints |
| Testing | pytest + httpx for backend (unit + integration against testcontainers Postgres); Vitest + Playwright for frontend |
| Observability | OpenTelemetry traces from FastAPI + Celery → optional Grafana/Tempo later |
| Secrets | `.env` locally, Railway/Vercel project secrets in prod, never committed |

## 5. Deployment Topology

- **Frontend**: Vercel (Next.js 15, edge-cached static/RSC where possible).
- **Backend**: Railway (Dockerized FastAPI + Celery worker + Celery beat as separate services,
  sharing one codebase, different start commands).
- **Database**: Supabase Postgres (managed, pgvector enabled).
- **Redis**: Railway Redis plugin.
- **Meilisearch**: Railway Docker service (or Meilisearch Cloud).
- **Storage**: Supabase Storage buckets (`resumes`, `banners`).

Local dev mirrors this with `docker-compose.yml` (Postgres+pgvector, Redis, Meilisearch).
