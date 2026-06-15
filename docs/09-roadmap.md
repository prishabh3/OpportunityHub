# OpportunityHub — Implementation Roadmap

Each milestone produces working, demoable, production-quality code (no placeholders) for its
scope. Later milestones build on earlier ones.

## Milestone 0 — Foundations & Scaffolding
- Monorepo structure (`frontend/`, `backend/`, `infra/`, `docs/`).
- `docker-compose.yml`: Postgres (pgvector), Redis, Meilisearch.
- FastAPI app skeleton: config, logging, exception handlers, `/health`, `/health/ready`.
- Next.js 15 app skeleton: Tailwind, shadcn/ui installed, base layout, dark theme.
- Alembic configured; initial migration from `02-database-schema.sql`.
- CI: lint + typecheck + test for both apps on push.

## Milestone 1 — Auth & User Profiles
- Supabase project wired (auth providers: email, Google, GitHub).
- Frontend: sign-in/sign-up pages, OAuth callback, session middleware, route guards.
- Backend: JWT verification dependency, `/me` GET/PATCH, `profiles` repository/service.
- Profile page: skills, preferences (companies/countries/role), graduation date.
- RLS policies applied + tested.

## Milestone 2 — Opportunities Core (manual data first)
- `opportunities`, `tags`, `sources` tables seeded with hand-curated sample data
  (~50-100 real opportunities across all 5 types) so the product is usable before connectors
  exist.
- Backend: `/opportunities` list (cursor pagination, filters), `/opportunities/{id}`.
- Frontend: opportunity list page with filter bar (type/tags/country/remote/difficulty),
  opportunity detail page, responsive card grid, loading/empty states.
- Admin: minimal `/admin/opportunities` CRUD for manual curation.

## Milestone 3 — Connector Framework + First Connectors
- `BaseConnector`, pipeline (normalize/validate/dedupe/upsert), `connector_runs` logging.
- Celery + Celery Beat wired (Railway/local docker).
- Implement: Greenhouse generic connector (covers many companies), Devpost, MLH, Unstop,
  Y Combinator Jobs.
- Admin: sources list, connector run history, manual trigger, failed-run view.

## Milestone 4 — Search
- Meilisearch sync task (on opportunity create/update).
- `/search` endpoint: keyword search + filters.
- Frontend search page with debounced query, filter chips, result highlighting.

## Milestone 5 — Bookmarks, Folders, Calendar
- Bookmarks CRUD + folders + notes/tags.
- Bookmarks UI (list/grid, folder sidebar).
- ICS export endpoint (`/calendar/ics/{token}.ics`) + "Add to Calendar" buttons.
- Deadline calendar view (month grid) on frontend.

## Milestone 6 — Notifications
- `notification_preferences` UI (channels, events, Discord webhook, Telegram linking).
- Celery tasks: `check_upcoming_deadlines` (24h/7d), `deadline_changed` hook in pipeline.
- Email sender (Resend/SendGrid) with templates; in-app notification center
  (Supabase Realtime).
- Weekly digest task + email template.

## Milestone 7 — AI: Resume Analyzer + Recommendations
- Resume upload (Supabase Storage) + `analyze_resume` task (LLM extraction →
  `resume_analyses`, `user_skills`).
- Embedding pipeline for opportunities + profiles (pgvector).
- `compute_match_score` + `opportunity_matches`; `/opportunities/{id}/match`,
  `/recommendations`.
- Dashboard: personalized feed, match scores on cards, "missing skills" chips.

## Milestone 8 — Semantic Search & New-Match Notifications
- LLM query parser for `/search` natural-language queries.
- `evaluate_notifications` pipeline step (new_match / company_alert fan-out).
- `search_history` logging → feeds recommendation refinement.

## Milestone 9 — Admin Analytics & Polish
- Admin analytics overview (ingestion health, counts by source/type, active users).
- Rate limiting, response caching tuned with real traffic patterns.
- Accessibility pass, animations (Framer Motion) on key transitions, empty/error states
  everywhere.
- E2E test suite (Playwright) covering core flows: sign up → set profile → browse → bookmark →
  get recommendation → receive notification (mocked).

## Milestone 10 — Deployment & Hardening
- Vercel (frontend) + Railway (backend, worker, beat, redis, meilisearch) production deploy.
- Secrets management, environment parity check (staging vs prod).
- Observability: structured logs, basic uptime checks, error tracking (Sentry).
- Load test core list/search endpoints; tune indexes/cache TTLs.

---

## Suggested Starting Point

Milestones 0–2 are the critical path to a usable product and should be done first, in order.
From Milestone 3 onward, modules are largely independent and can be reprioritized based on
which "wow factor" matters most for a demo (connectors for breadth, AI for differentiation,
notifications for retention).
