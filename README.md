# OpportunityHub

OpportunityHub collects hackathons, internships, jobs, research programs, and competitions from many different websites into one place, so students and early-career engineers don't have to check a dozen sites by hand. A set of background "connectors" fetch listings from sources like company job boards and Unstop on a schedule, clean them up into one common shape, and store them without creating duplicates. Signed-in users fill out a short profile (skills, preferred countries, remote vs. on-site), and the app ranks opportunities by how well each one fits them. Users can bookmark listings and get in-app reminders when a bookmarked deadline is close. There's also full-text search, and an admin panel showing traffic, users, and how each connector's last run went. The interesting part isn't the listing UI — it's the ingestion pipeline that keeps data fresh and deduplicated, and the scoring layer that turns a raw list into a ranked one.

---

## Tech stack

| Layer | Technology | Role |
| --- | --- | --- |
| Frontend framework | Next.js 16 (App Router) + React 19 | Pages, routing, server-side session handling |
| Language (frontend) | TypeScript | Type safety across the UI |
| Styling | Tailwind CSS v4, shadcn/ui, Framer Motion | Components, theming (light/dark), animation |
| Data fetching | TanStack Query | Client-side caching of API responses |
| Forms | React Hook Form + Zod | Form state and input validation |
| Backend framework | FastAPI | REST API, dependency injection, OpenAPI docs |
| Language (backend) | Python 3.12 | Application and pipeline code |
| ORM / DB access | SQLAlchemy 2.0 (async) + asyncpg | Typed queries over Postgres, async driver |
| Migrations | Alembic | Versioned schema changes |
| Database | PostgreSQL (Supabase in prod) + pgvector | Primary datastore; vector column reserved for embeddings |
| Full-text search | PostgreSQL `tsvector` / `websearch_to_tsquery` | The `/search` endpoint |
| Search engine (infra) | Meilisearch | Runs in local infra and is a dependency; not yet wired to the search endpoint |
| Cache / counters | Redis (Upstash in prod) | Rate-limit buckets and live traffic counters |
| Auth | Supabase Auth (email, Google, GitHub, TOTP MFA) | Issues JWTs; backend only verifies them |
| Logging | structlog | Structured JSON logs with request context |
| Background jobs | GitHub Actions cron | Triggers ingestion + deadline reminders every 6h |
| Hosting | Vercel (frontend), Render (backend, Docker), Supabase, Upstash | Free-tier production stack |

> Note: `celery` is a declared dependency but there is no always-on worker in production — scheduled work runs via GitHub Actions hitting token-protected endpoints (see [Key design decisions](#key-design-decisions)).

---

## Architecture

```
                              ┌────────────────────────────────┐
                              │            Browser              │
                              └────────────────────────────────┘
                                   │                     │
                     (1) auth via Supabase JS      (2) API calls with
                         (email / OAuth / MFA)         Bearer <JWT>
                                   │                     │
              ┌────────────────────▼──────┐             │
              │   Supabase Auth (hosted)   │             │
              │  - issues + signs JWTs     │             │
              │  - JWKS public keys        │             │
              └────────────┬───────────────┘             │
                           │ JWKS                         │
                verify signature (ES256/RS256)            │
                           │                              │
        ┌──────────────────▼──────────────────────────────▼─────────────────┐
        │                     Next.js frontend (Vercel)                       │
        │  - proxy.ts: refresh session cookie, gate protected routes, MFA     │
        │  - api-client.ts: attaches JWT, normalizes RFC 9457 errors          │
        └───────────────────────────────┬─────────────────────────────────────┘
                                         │ HTTPS (CORS-restricted)
                                         ▼
        ┌─────────────────────────────────────────────────────────────────────┐
        │                      FastAPI backend (Render)                        │
        │                                                                       │
        │  Middleware (outer→inner):                                            │
        │    RequestContext → SecurityHeaders → RateLimit(global) → CORS        │
        │                                                                       │
        │  Routers: /health /me /opportunities /search /bookmarks              │
        │           /recommendations /notifications /ingest /admin /traffic    │
        │                                                                       │
        │  Layers:  api  →  application/services  →  infrastructure/repos       │
        │                                                                       │
        │  Connectors: devpost, unstop, greenhouse, lever, curated_* ──┐        │
        └───────────────┬───────────────────────┬─────────────────────┼────────┘
                        │                        │                     │
                        ▼                        ▼                     ▼
              ┌──────────────────┐    ┌──────────────────┐   ┌──────────────────┐
              │  PostgreSQL      │    │      Redis       │   │  External sites  │
              │  (Supabase)      │    │    (Upstash)     │   │ Greenhouse/Lever │
              │  + pgvector      │    │ rate limits +    │   │ Unstop/Devpost   │
              │  + tsvector FTS  │    │ traffic counters │   │ (HTTP fetch)     │
              └──────────────────┘    └──────────────────┘   └──────────────────┘
                        ▲
                        │ POST /ingest/run  (X-Ingest-Token)
              ┌─────────┴──────────┐
              │  GitHub Actions     │  cron every 6h → ingest + deadline reminders
              └────────────────────┘
```

The system has three independent runtimes plus two data stores. The **Next.js frontend** talks to **Supabase Auth** directly for anything involving credentials — sign-up, sign-in, OAuth, MFA — and never sends passwords to our own backend. Supabase hands the browser a signed JWT. Every call to the **FastAPI backend** carries that JWT in an `Authorization: Bearer` header; the backend verifies the signature against Supabase's public keys (JWKS) but never issues or stores tokens itself. The backend reads and writes **PostgreSQL** for all durable data and uses **Redis** for two ephemeral jobs: rate-limit counters and live-visitor tracking. Separately, **GitHub Actions** acts as the scheduler: every six hours it calls two token-protected backend endpoints that run the connectors (which fetch from external job boards) and generate deadline reminders.

---

## How the pieces fit together

**A page load (anonymous user browsing opportunities).** The browser requests `/opportunities` from Next.js. `proxy.ts` runs first on every request — it refreshes the Supabase session cookie and, for anonymous users on public routes, does nothing else. The page's React components call `apiClient.get("/api/v1/opportunities", …)`. `api-client.ts` looks for a Supabase session; finding none, it sends the request without an `Authorization` header. FastAPI's middleware stack runs outermost-first: request context (assigns a request ID), security headers, then the global rate limiter (which buckets anonymous callers by client IP). The `list_opportunities` handler builds an `OpportunityFilters` object, hands it to `OpportunityService`, which calls `OpportunityRepository.list_page` — a keyset-paginated query ordered by `(created_at desc, id desc)`. The rows come back, get mapped to `OpportunitySummary` DTOs, and are returned as a `Page` with a `next_cursor`.

**A signed-in action (bookmarking).** After the user signs in, Supabase stores a session; `api-client.ts` now attaches the JWT to every request. `POST /bookmarks` passes through the global rate limiter *and* a stricter per-route write limiter, then `get_current_user` verifies the JWT and extracts the user id and role. `BookmarkService.add` ensures the user's `profiles` row exists, checks for an existing bookmark, and inserts one — catching a unique-constraint violation to stay idempotent under concurrent clicks.

**Getting fresh data in (ingestion).** GitHub Actions calls `POST /api/v1/ingest/run` with the shared `X-Ingest-Token`. `run_all` iterates the connector registry. Each connector's `fetch()` hits an external source over HTTP and returns `NormalizedOpportunity` objects — one common shape regardless of source. The pipeline computes a `content_hash` per item and compares against existing rows keyed by `(source_id, external_id)`: new items are inserted, changed items updated, unchanged items skipped. Every run writes a `connector_runs` row so the admin panel can show what happened. Each connector commits independently, so one failing source doesn't abort the rest.

**Turning the list into a ranking (recommendations).** `GET /recommendations` loads the user's profile, pulls a recent pool of up to 300 active opportunities, and scores each one against the profile: skill-tag overlap (up to 60 points), country match (20), and remote-preference match (20). Results are sorted by score, with recency breaking ties.

---

## Quick start

You need Docker, Python 3.12, and Node 20+.

### 1. Start local infrastructure

```bash
cd infra
docker compose up -d
```

This starts Postgres (with pgvector), Redis, and Meilisearch. It also runs [`infra/init-db/01-auth-schema.sql`](infra/init-db/01-auth-schema.sql), a minimal local stand-in for Supabase's managed `auth` schema (`auth.users`, `auth.uid()`) so migrations that reference it apply on plain Postgres.

> **Easy to forget — the ports are remapped.** To avoid clashing with any Postgres/Redis you already run, docker-compose exposes **Postgres on host port `5433`** (not 5432) and **Redis on `6380`** (not 6379). The `DATABASE_URL` in `.env.example` still says `5432` — change it to `5433` for local Docker, or your connections will silently hit the wrong server.

### 2. Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv
.venv/bin/pip install -e ".[dev]"
cp .env.example .env      # then edit DATABASE_URL port → 5433 (see note above)
.venv/bin/alembic upgrade head
.venv/bin/uvicorn app.main:app --reload
```

The API is now at `http://localhost:8000`. Interactive docs: `http://localhost:8000/docs`. Health checks: `GET /api/v1/health` (liveness), `GET /api/v1/health/ready` (verifies DB + Redis).

**Seed sample data (optional but recommended):**

```bash
.venv/bin/python -m app.seed.opportunities
```

This inserts a curated set of sample opportunities under a `curated` source. It's idempotent — re-running only inserts rows whose `(source, external_id)` isn't already present.

**Or pull live data** by running the connectors once (requires network access):

```bash
# set INGEST_TOKEN in .env first, then:
curl -X POST http://localhost:8000/api/v1/ingest/run -H "X-Ingest-Token: <your-token>"
```

### 3. Frontend (Next.js)

```bash
cd frontend
npm install
cp .env.local.example .env.local   # fill in the three values below
npm run dev
```

`.env.local` needs a real Supabase project (auth is not stubbed locally):

| Variable | Value |
| --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://<project>.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase anon/publishable key |
| `NEXT_PUBLIC_API_BASE_URL` | `http://localhost:8000` |

The app runs at `http://localhost:3000`.

### 4. Create an admin user (easy to forget)

Admin access is gated on the JWT's `app_metadata.role == "admin"` — **not** the `profiles.role` column. To make yourself an admin: sign up normally, then in the **Supabase dashboard → Authentication → Users → (your user) → edit `app_metadata`** set:

```json
{ "role": "admin" }
```

Sign out and back in so a fresh JWT is minted with the new claim. `/admin` will now load.

---

## Feature walkthrough — signup to a ranked, bookmarked opportunity

1. **Sign up.** Go to `/sign-up`. Enter email + password (or click *Continue with Google/GitHub*). Supabase sends a confirmation email; the link returns to `/auth/callback`, which exchanges the `code` for a session cookie.
2. **(Optional) Turn on MFA.** In `/profile`, enroll a TOTP factor. Once enrolled, `proxy.ts` requires an `aal2` challenge (`/mfa-challenge`) before any protected page loads.
3. **Fill out your profile.** In `/profile`, set skills (e.g. `Python`, `React`), preferred countries, and remote preference. `PATCH /me` saves them. These three fields are exactly what the recommender scores against.
4. **Browse.** `/opportunities` shows the paginated list. Filter by category (hackathons vs. jobs), type, country (Anywhere / India / Global toggle), remote type, difficulty, and experience level.
5. **See your matches.** `/dashboard` calls `GET /recommendations` and shows opportunities ranked by fit, each with its `match_score` and the specific `matched_skills` that earned it.
6. **Search.** `/search` runs ranked full-text search across title, organizer, and description.
7. **Bookmark.** Click the bookmark button on any card (`POST /bookmarks`). It appears under `/bookmarks`.
8. **Get reminded.** When a bookmarked opportunity's deadline is within 7 days (or 24 hours), the scheduled reminder job creates an in-app notification — visible via the navbar bell (`GET /notifications`).

---

## API reference

Base path: `/api/v1`. Auth column: **None** = public, **Bearer** = valid Supabase JWT required, **Admin** = JWT with `app_metadata.role=admin`, **Token** = `X-Ingest-Token` header. Errors use RFC 9457 `application/problem+json`.

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| GET | `/health` | None | Liveness probe (no dependencies checked) |
| GET | `/health/ready` | None | Readiness — checks Postgres + Redis, returns `degraded` if either is down |
| GET | `/me` | Bearer | Current user's profile (created on first access) |
| PATCH | `/me` | Bearer | Partial profile update |
| GET | `/opportunities` | None | Filterable, cursor-paginated list |
| GET | `/opportunities/{id}` | None | Single opportunity detail |
| GET | `/search?q=` | None | Ranked full-text search (rate-limited, 30/min) |
| GET | `/recommendations?limit=` | Bearer | Opportunities ranked by profile fit |
| GET | `/bookmarks` | Bearer | User's bookmarks (paginated) |
| GET | `/bookmarks/ids` | Bearer | Bookmarked opportunity ids (for toggle state) |
| POST | `/bookmarks` | Bearer | Add a bookmark (write-limited, idempotent) |
| DELETE | `/bookmarks/{opportunity_id}` | Bearer | Remove a bookmark |
| GET | `/notifications` | Bearer | Notifications (paginated) |
| GET | `/notifications/unread-count` | Bearer | `{ "count": n }` |
| POST | `/notifications/read-all` | Bearer | Mark all as read |
| POST | `/notifications/{id}/read` | Bearer | Mark one as read |
| POST | `/notifications/run` | Token | Cron: generate deadline reminders |
| POST | `/ingest/run?source=` | Token | Cron: run all connectors (or one, via `source`) |
| POST | `/traffic/ping?visitor_id=` | None | Record a visit (rate-limited, 20/min) |
| GET | `/admin/analytics` | Admin | Totals: opportunities (by type), users, bookmarks, notifications |
| GET | `/admin/sources` | Admin | Per-source opportunity counts |
| GET | `/admin/connector-runs` | Admin | Recent connector runs and their stats |
| POST | `/admin/ingest/run` | Admin | "Refresh now" — run connectors from the UI |
| GET | `/admin/traffic` | Admin | Live visitors, page views, unique visitors |
| GET | `/admin/users` | Admin | Recent users |

**Example — `PATCH /me`:**

```json
{
  "full_name": "Ada Lovelace",
  "skills": ["Python", "React", "PostgreSQL"],
  "preferred_countries": ["India", "United States"],
  "preferred_remote": "remote",
  "expected_graduation": "2027-06-01"
}
```

**Example — `POST /bookmarks`:**

```json
{
  "opportunity_id": "6f1c2d34-5b6a-4c8d-9e0f-1a2b3c4d5e6f",
  "notes": "Apply after finals",
  "tags": ["priority"]
}
```

**Example — `GET /opportunities` with filters:**

```
GET /api/v1/opportunities?category=jobs&country=India&experience_level=intern&limit=20
```

Response shape (`Page[OpportunitySummary]`):

```json
{
  "data": [ { "id": "…", "type": "internship", "title": "…", "tags": ["Python"], "…": "…" } ],
  "page": { "next_cursor": "MjAyNi0wNy0wOVQ…", "has_more": true, "limit": 20 }
}
```

Pass `next_cursor` back as `?cursor=…` to fetch the next page.

---

## Database layout

One PostgreSQL database (Supabase in production). Redis holds only ephemeral counters, not durable rows. Key tables:

| Table | Stores |
| --- | --- |
| `profiles` | One row per user (PK = Supabase `auth.users.id`). Preferences, role, timezone, digest opt-in. Reserved columns for `profile_embedding vector(1536)` and resume metadata (unused until AI is enabled). |
| `skills`, `user_skills` | Normalized skill catalog and the many-to-many link to profiles. |
| `sources` | One row per connector (key, display name, base URL, which opportunity types it produces). |
| `connector_runs` | Audit log of every ingestion run: status, counts (found/created/updated/failed), timing, error message. |
| `opportunities` | The core listing table. Type/status enums, org/location fields, four timestamps (posted/deadline/starts/ends), `apply_url`, JSONB `details`, `content_hash`, a maintained `search_vector`, and a reserved `embedding vector(1536)`. Unique on `(source_id, external_id)`. |
| `tags`, `opportunity_tags` | Skill/topic tags and their many-to-many link to opportunities. |
| `bookmarks`, `bookmark_folders` | A user's saved opportunities (unique on `(user_id, opportunity_id)`) and optional folders. |
| `notifications` | In-app (and future email/push) messages: event type, channel, title/body, read/sent timestamps. |
| `deadline_reminders_sent` | Idempotency ledger. PK `(user_id, opportunity_id, event)` ensures each reminder is created at most once. |
| `notification_preferences` | Per-user channel/event opt-ins (schema present; UI/delivery are later milestones). |
| `resume_analyses`, `opportunity_matches`, `search_history`, `calendar_sync_tokens` | Schema reserved for later milestones (resume parsing, persisted match scores, search logging, ICS/Google Calendar). |

**Row-Level Security** is enabled on every table in the `public` schema. Opportunities are world-readable (`using (true)`); personal tables use `auth.uid() = user_id` policies so a user can only touch their own rows; and reference/connector tables (`skills`, `sources`, `tags`, etc.) have RLS on with **no** policies, making them unreachable via the public anon key while the backend still reaches them as the `postgres` role. Two triggers maintain data automatically: `search_vector` is rebuilt from `title/organizer/description` on insert/update, and `updated_at` is bumped on update.

**Redis keys:** `ratelimit:*` (global fixed-window buckets), `slidingrl:*` (per-route sliding-window logs), and `traffic:active` / `traffic:pageviews` / `traffic:visitors` (a sorted set, a counter, and a HyperLogLog).

---

## Key design decisions

**Backend never issues tokens.** Supabase Auth is the sole identity provider. The backend verifies JWTs against the project's JWKS endpoint and only accepts asymmetric algorithms (`ES256`, `RS256`) — allowing `HS256` would open a key-confusion attack where an attacker signs a token with the public key. The user's role comes from the JWT's `app_metadata`, so authorization needs no extra DB lookup.

**Deduplicated, idempotent ingestion.** Each `NormalizedOpportunity` has a `content_hash` (SHA-256 over the meaningful fields). On re-ingest, the pipeline looks up existing rows by `(source_id, external_id)` and inserts new / updates changed / skips unchanged. This means a connector can run every six hours and only touch rows that actually changed.

**Reminders that never double-fire.** `generate_deadline_reminders` finds bookmarked opportunities with a deadline in the next 7 days and writes a `deadline_reminders_sent` row (PK `user_id + opportunity_id + event`) alongside each notification. The next run sees the ledger row and skips — so re-running the cron is safe.

**Keyset (cursor) pagination, not `OFFSET`.** Lists are ordered by `(created_at desc, id desc)` and the cursor encodes that pair (base64 of `created_at|id`, length-capped to reject junk). The query fetches `limit + 1` rows to decide `has_more`. This stays fast on large tables and doesn't skip/duplicate rows when data is inserted mid-scroll, unlike offset paging.

**Two layers of rate limiting, both fail-open.** A global middleware applies a coarse fixed-window budget per identity, tiered by role (anon 60/min, authed 300/min, admin 1000/min). On top, a `RateLimiter` dependency applies tight sliding-window limits to specific expensive/abusable routes (search 30, writes 40, ping 20). Both are backed by Redis and **fail open** — a Redis outage must not take the API down. (The middleware builds its own 429 response because exceptions raised inside `BaseHTTPMiddleware` bypass FastAPI's exception handlers.)

**Idempotent bookmarking.** `POST /bookmarks` first checks for an existing row, but also catches the `(user_id, opportunity_id)` unique-constraint `IntegrityError` and returns the existing bookmark — so a double-click or race can't 500.

**Heuristic recommendations (no LLM yet).** Scoring is transparent and cheap: skill overlap capped at 5 matched tags (60 pts), country match with alias/"global" normalization (20 pts), remote-preference match (20 pts). The `embedding` columns and pgvector index exist for a future semantic version, gated behind `AI_FEATURES_ENABLED`.

**Robust DB-URL handling.** `config.py` normalizes any pasted Postgres URL: forces the `postgresql+asyncpg://` driver and URL-encodes the user/password so special characters in the password don't corrupt host parsing — a real gotcha with Supabase pooler passwords.

**GitHub Actions as the scheduler.** Rather than run an always-on Celery worker (costly on free tiers), a cron workflow hits `POST /ingest/run` and `POST /notifications/run` every six hours, authenticated with a shared `X-Ingest-Token` (compared with `hmac.compare_digest`).

---

## Testing

Backend tests live in [`backend/tests/`](backend/tests/) and require a live Postgres and Redis (use the docker-compose infra).

```bash
cd backend
.venv/bin/ruff check .        # lint
.venv/bin/mypy app            # strict type-checking
.venv/bin/pytest -q           # tests
```

What's covered:

- **`tests/unit/test_health.py`** — liveness endpoint returns `{"status": "ok"}`.
- **`tests/integration/test_health_ready.py`** — readiness endpoint reports `ok` for DB and Redis (fails if either is unreachable).
- **`tests/integration/test_rate_limit.py`** — exceeding the anonymous budget returns a real `429` in `problem+json` with `Retry-After` and `X-RateLimit-*` headers (a regression test for the middleware-bypasses-handlers issue).

Frontend checks:

```bash
cd frontend
npm run lint
npm run typecheck
npm run build
```

CI ([`.github/workflows/`](.github/workflows/)) runs the backend lint/type/migrate/test pipeline against service containers and the frontend lint/typecheck/build on every relevant push and PR.

---

## Project structure

```
.
├── backend/                        FastAPI service (clean-architecture layering)
│   ├── app/
│   │   ├── main.py                 App factory: middleware stack + router wiring
│   │   ├── api/v1/                 HTTP layer — one module per resource
│   │   │   ├── router.py           Aggregates all routers under /api/v1
│   │   │   ├── opportunities.py    List/detail with filters + cursor paging
│   │   │   ├── bookmarks.py        CRUD + write rate limiter
│   │   │   ├── search.py           Full-text search (rate-limited)
│   │   │   ├── recommendations.py  Ranked matches for the current user
│   │   │   ├── notifications.py    In-app notifications + cron reminder trigger
│   │   │   ├── ingest.py           Token-protected connector trigger
│   │   │   ├── admin.py            Analytics, sources, runs, traffic, users
│   │   │   ├── traffic.py          Anonymous visitor ping
│   │   │   └── health.py           Liveness + readiness
│   │   ├── application/            Use-case layer
│   │   │   ├── services/           Business logic (Opportunity/Bookmark/… services)
│   │   │   └── dtos/               Pydantic request/response + pagination models
│   │   ├── connectors/             Ingestion framework
│   │   │   ├── base.py             BaseConnector + NormalizedOpportunity + content_hash
│   │   │   ├── pipeline.py         Upsert/dedupe engine, writes connector_runs
│   │   │   ├── registry.py         Maps source key → connector class
│   │   │   ├── service.py          run_all() orchestration
│   │   │   ├── greenhouse.py / lever.py / unstop.py / devpost.py   Live-source connectors
│   │   │   ├── curated_*.py        Hand-maintained listings
│   │   │   └── jobs_common.py      Shared helpers (skill tagging, country/experience inference)
│   │   ├── core/                   Cross-cutting concerns
│   │   │   ├── config.py           Settings (env parsing, DB-URL normalization)
│   │   │   ├── security.py         JWT verification, role/admin/job-token guards
│   │   │   ├── rate_limit.py       Global middleware + per-route sliding limiter
│   │   │   ├── exceptions.py       RFC 9457 problem+json error handling
│   │   │   ├── pagination.py       Cursor encode/decode
│   │   │   ├── validators.py       Input sanitization (URLs, text, UUIDs, LIKE-escaping)
│   │   │   ├── request_context.py  Request ID + structured log binding
│   │   │   ├── security_headers.py HSTS + hardening headers
│   │   │   └── cache.py            Redis connection pool
│   │   ├── infrastructure/db/      SQLAlchemy models, repositories, session
│   │   └── seed/opportunities.py   Idempotent sample-data seeder
│   ├── migrations/                 Alembic (0001 schema, 0002 in_app channel, 0003 experience_level)
│   ├── tests/                      unit + integration
│   ├── scripts/start.sh            Prod entrypoint: migrate → optional seed → uvicorn
│   └── Dockerfile
│
├── frontend/                       Next.js 16 App Router
│   └── src/
│       ├── app/                    Routes: (auth), dashboard, opportunities, bookmarks,
│       │                           profile, search, admin, mfa-challenge, auth/callback
│       ├── features/               Feature modules (api.ts + components per domain)
│       ├── components/             UI kit (shadcn), layout, providers
│       ├── lib/
│       │   ├── api-client.ts       Typed fetch wrapper; attaches JWT, parses errors
│       │   ├── supabase/           Browser + server clients, session proxy
│       │   └── env.ts              Zod-validated public env vars
│       └── proxy.ts                Next middleware: session refresh + route/MFA gating
│
├── infra/
│   ├── docker-compose.yml          Local Postgres+pgvector / Redis / Meilisearch
│   └── init-db/01-auth-schema.sql  Local stand-in for Supabase's auth schema
│
├── docs/                           Design docs (architecture, schema, API, roadmap …)
├── render.yaml                     Render Blueprint for the backend service
├── DEPLOYMENT.md                   Step-by-step free-tier deploy guide
└── README.md
```

Deeper design docs live in [`docs/`](docs/) (architecture, full SQL schema, API design, scraper/notification/recommendation architecture, auth, roadmap).

---

## Common issues

| Symptom | Cause | Fix |
| --- | --- | --- |
| Backend can't connect to Postgres locally; `alembic upgrade` hangs or connection refused | docker-compose maps Postgres to host port **5433**, but `.env.example` says `5432` | Set `DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5433/opportunityhub` |
| Migration fails: `schema "auth" does not exist` or `function auth.uid() does not exist` | Migrations reference Supabase's managed `auth` schema | Ensure `infra/init-db/01-auth-schema.sql` ran (it's applied automatically by docker-compose on first boot; on an existing volume, apply it manually with `psql`) |
| `/admin` returns 403 even though you're logged in | Admin is gated on the JWT `app_metadata.role`, not `profiles.role` | Set `{"role":"admin"}` in `app_metadata` in the Supabase dashboard, then sign out/in for a fresh token |
| API calls to backend fail with a CORS error in the browser | The frontend origin isn't in `CORS_ORIGINS` | Add `http://localhost:3000` (local) or your Vercel domain (prod) to `CORS_ORIGINS` — it accepts a JSON array or comma-separated list |
| Logs show `rate_limit_redis_unavailable` and limits don't apply | Backend can't reach Redis (wrong `REDIS_URL`, or `redis://` vs. `rediss://` for Upstash TLS) | Fix `REDIS_URL`. Rate limiting fails **open** by design, so the API keeps serving — but limits are effectively off until Redis connects |
| Frontend crashes on boot with "Invalid environment configuration" | `env.ts` validates public vars with Zod at startup | Set all three `NEXT_PUBLIC_*` vars in `.env.local` (URL fields must be valid URLs) |
| Empty opportunities list after a fresh setup | No data ingested yet | Run `python -m app.seed.opportunities`, or trigger `POST /ingest/run` with a valid `X-Ingest-Token` |
| `POST /ingest/run` returns 403 "Scheduled jobs are not configured" | `INGEST_TOKEN` is unset in the backend env | Set `INGEST_TOKEN` in `.env` and send the same value in the `X-Ingest-Token` header |
| First request to the deployed backend takes ~50s | Render free web services sleep after ~15 min idle | Expected on free tier; the service cold-starts. Keep `SEED_ON_START=false` after first deploy so restarts are quick |
| mypy error `Function "…​.list" is not valid as a type` at import | A repository/service method named `list` shadows the builtin used in later annotations | Name paginated methods `list_page` (the established convention across all repositories/services) |
