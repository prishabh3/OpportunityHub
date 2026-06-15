# OpportunityHub — API Design

Base URL: `/api/v1`. JSON in/out. Auth via `Authorization: Bearer <supabase_jwt>`.

## 1. Conventions

### 1.1 Cursor Pagination

All list endpoints use cursor pagination:

```
GET /api/v1/opportunities?limit=20&cursor=eyJ2IjoiMjAyNS0wMS0wMVQwMDowMDowMFoiLCJpZCI6IjEyMyJ9
```

Response envelope:

```json
{
  "data": [ ... ],
  "page": {
    "next_cursor": "eyJ2Ijoi...",
    "has_more": true,
    "limit": 20
  }
}
```

The cursor is a base64-encoded JSON object `{"v": <sort_value>, "id": <uuid>}` — opaque to
clients. Sorting defaults to `deadline_at ASC NULLS LAST, id ASC` for opportunity feeds.

### 1.2 Error Format (RFC 9457 Problem Details)

```json
{
  "type": "https://opportunityhub.dev/errors/validation",
  "title": "Validation failed",
  "status": 422,
  "detail": "deadline_at must be a valid ISO 8601 datetime",
  "errors": [{"field": "deadline_at", "message": "invalid format"}]
}
```

### 1.3 Rate Limits

| Tier | Limit |
|---|---|
| Anonymous | 60 req/min per IP |
| Authenticated | 300 req/min per user |
| Admin | 1000 req/min |

Returned headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`.

## 2. Opportunities

```
GET    /api/v1/opportunities
GET    /api/v1/opportunities/{id}
GET    /api/v1/opportunities/trending
GET    /api/v1/opportunities/recent
```

### List filters (`GET /opportunities`)

| Param | Type | Notes |
|---|---|---|
| `type` | enum[] | hackathon, internship, full_time_job, research_program, competition |
| `status` | enum[] | default `active` |
| `tags` | string[] | e.g. `ai,blockchain` (matches `opportunity_tags`) |
| `country` | string[] | |
| `remote_type` | enum[] | remote, hybrid, onsite |
| `difficulty` | enum[] | |
| `organizer` | string | partial match |
| `deadline_before` / `deadline_after` | ISO date | |
| `prize_min` | number | reads `details.prize_pool` |
| `q` | string | full-text query (Meilisearch) |
| `sort` | enum | `deadline_asc` (default), `newest`, `prize_desc`, `trending` |
| `limit`, `cursor` | | pagination |

`GET /opportunities/{id}` returns the full record including `details`.

### Admin write endpoints (service-role / admin JWT only)

```
POST   /api/v1/opportunities            (manual add)
PATCH  /api/v1/opportunities/{id}
DELETE /api/v1/opportunities/{id}        (soft delete -> status=archived)
```

## 3. Search

```
GET /api/v1/search?q=AI internships in Europe&limit=20&cursor=...
```

Flow: query → LLM-based filter extraction (type, tags, country, remote, prize range) → combined
Meilisearch keyword search + pgvector semantic similarity → merged/re-ranked results. Falls back
to plain Meilisearch if the LLM parser is unavailable. Logs to `search_history` for authenticated
users.

## 4. Auth & Profile

Auth itself (signup/login/OAuth) is handled client-side via Supabase Auth SDK — the backend never
issues tokens. The backend only verifies the incoming Supabase JWT.

```
GET    /api/v1/me                      -> current profile
PATCH  /api/v1/me                      -> update profile (skills, prefs, etc.)
POST   /api/v1/me/resume               -> upload resume (multipart -> Supabase Storage)
GET    /api/v1/me/resume/analysis      -> latest parsed resume + extracted skills
POST   /api/v1/me/resume/analyze       -> trigger (re)analysis (Celery task, returns task id)
GET    /api/v1/tasks/{task_id}         -> poll async task status
```

## 5. Bookmarks

```
GET    /api/v1/bookmarks?folder_id=&tags=
POST   /api/v1/bookmarks                 { opportunity_id, folder_id?, notes?, tags? }
PATCH  /api/v1/bookmarks/{id}            { folder_id?, notes?, tags? }
DELETE /api/v1/bookmarks/{id}

GET    /api/v1/bookmark-folders
POST   /api/v1/bookmark-folders          { name }
PATCH  /api/v1/bookmark-folders/{id}
DELETE /api/v1/bookmark-folders/{id}
```

## 6. Calendar

```
GET  /api/v1/calendar/ics/{token}.ics    -> public ICS feed (token from calendar_sync_tokens)
POST /api/v1/calendar/google/connect     -> OAuth flow init for Google Calendar sync
POST /api/v1/calendar/regenerate-token
```

## 7. Recommendations & Matching

```
GET  /api/v1/recommendations?limit=20&cursor=...
      -> personalized feed, ranked by opportunity_matches.match_score

GET  /api/v1/opportunities/{id}/match
      -> { match_score, missing_skills, reasoning, probability_estimate }

POST /api/v1/recommendations/refresh   -> enqueue recompute (Celery), returns task id
```

## 8. Notifications

```
GET    /api/v1/notifications?unread=true&cursor=...
PATCH  /api/v1/notifications/{id}/read
POST   /api/v1/notifications/read-all

GET    /api/v1/notification-preferences
PATCH  /api/v1/notification-preferences
       { channels, events, discord_webhook_url?, telegram_chat_id?, push_subscription? }
```

## 9. Dashboard

```
GET /api/v1/dashboard
    -> {
         personalized_feed: Opportunity[],
         upcoming_deadlines: Opportunity[],
         recommended: Opportunity[],
         recently_added: Opportunity[],
         trending: Opportunity[],
         bookmarks_preview: Bookmark[]
       }
```
Backed by Redis cache (per-user, 2 min TTL) composed from the same repositories used by the
individual endpoints above.

## 10. Admin

```
GET  /api/v1/admin/sources
PATCH /api/v1/admin/sources/{id}        { is_active, schedule_cron }
GET  /api/v1/admin/connector-runs?source_id=&status=&cursor=
POST /api/v1/admin/connector-runs/{source_id}/trigger   -> manual run

GET  /api/v1/admin/opportunities         (includes archived/draft)
GET  /api/v1/admin/users?cursor=
PATCH /api/v1/admin/users/{id}           { role }

GET  /api/v1/admin/analytics/overview
     -> counts by type/source, ingestion success rate, active users, top searched terms
```

All `/admin/*` routes require `profiles.role = 'admin'`, enforced by a FastAPI dependency
(`require_admin`) on top of JWT verification.

## 11. Health & Ops

```
GET /api/v1/health        -> liveness (no deps)
GET /api/v1/health/ready  -> readiness (db, redis, meilisearch checks)
```
