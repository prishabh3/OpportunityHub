# OpportunityHub — Monorepo Folder Structure

```
opportunity-hub/
├── docs/                            # this design documentation
│   ├── 01-architecture.md
│   ├── 02-database-schema.sql
│   ├── 03-api-design.md
│   ├── 04-scraper-architecture.md
│   ├── 05-notification-architecture.md
│   ├── 06-recommendation-architecture.md
│   ├── 07-authentication.md
│   ├── 08-folder-structure.md
│   └── 09-roadmap.md
│
├── frontend/                        # Next.js 15 (App Router)
│   ├── src/
│   │   ├── app/                     # routes (App Router)
│   │   │   ├── (marketing)/         # landing page, public pages
│   │   │   ├── (auth)/              # sign-in, sign-up, oauth callback
│   │   │   ├── (dashboard)/         # authenticated app shell
│   │   │   │   ├── dashboard/
│   │   │   │   ├── opportunities/
│   │   │   │   │   ├── [id]/
│   │   │   │   │   └── page.tsx
│   │   │   │   ├── bookmarks/
│   │   │   │   ├── calendar/
│   │   │   │   ├── profile/
│   │   │   │   ├── notifications/
│   │   │   │   └── search/
│   │   │   ├── admin/               # admin panel routes
│   │   │   ├── api/                 # route handlers (webhooks, ICS proxy, etc.)
│   │   │   └── layout.tsx
│   │   │
│   │   ├── features/                # feature-first modules
│   │   │   ├── opportunities/
│   │   │   │   ├── components/      # OpportunityCard, FilterBar, ...
│   │   │   │   ├── hooks/            # useOpportunities, useOpportunity
│   │   │   │   ├── api.ts            # TanStack Query fns calling backend
│   │   │   │   └── types.ts
│   │   │   ├── bookmarks/
│   │   │   ├── dashboard/
│   │   │   ├── profile/
│   │   │   ├── notifications/
│   │   │   ├── search/
│   │   │   ├── calendar/
│   │   │   └── admin/
│   │   │
│   │   ├── components/              # shared UI (shadcn/ui-based)
│   │   │   ├── ui/                   # shadcn primitives (button, card, dialog, ...)
│   │   │   └── layout/               # navbar, sidebar, app-shell
│   │   │
│   │   ├── lib/
│   │   │   ├── supabase/             # client/server supabase instances
│   │   │   ├── api-client.ts         # typed fetch wrapper (base url, auth header, errors)
│   │   │   ├── query-client.ts       # TanStack Query client config
│   │   │   └── utils.ts
│   │   │
│   │   ├── hooks/                    # cross-feature hooks (useAuth, useDebounce)
│   │   ├── types/                    # shared/generated API types (from OpenAPI)
│   │   ├── styles/
│   │   └── middleware.ts             # supabase session refresh + route guards
│   │
│   ├── public/
│   ├── tests/                        # Vitest unit + Playwright e2e
│   ├── package.json
│   ├── tailwind.config.ts
│   ├── tsconfig.json
│   └── next.config.ts
│
├── backend/                          # FastAPI
│   ├── app/
│   │   ├── main.py                   # app factory, router registration, middleware
│   │   ├── core/
│   │   │   ├── config.py             # pydantic Settings (env-based)
│   │   │   ├── security.py           # JWT verification, AuthenticatedUser
│   │   │   ├── logging.py            # structlog setup
│   │   │   ├── exceptions.py         # domain exceptions + handlers
│   │   │   ├── rate_limit.py
│   │   │   └── cache.py              # redis cache helpers
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── router.py         # aggregates all routers under /api/v1
│   │   │       ├── opportunities.py
│   │   │       ├── search.py
│   │   │       ├── bookmarks.py
│   │   │       ├── profile.py
│   │   │       ├── recommendations.py
│   │   │       ├── notifications.py
│   │   │       ├── calendar.py
│   │   │       ├── dashboard.py
│   │   │       ├── admin.py
│   │   │       └── health.py
│   │   │
│   │   ├── domain/                   # entities, value objects, enums
│   │   │   ├── entities/
│   │   │   │   ├── opportunity.py
│   │   │   │   ├── profile.py
│   │   │   │   ├── bookmark.py
│   │   │   │   └── notification.py
│   │   │   └── enums.py
│   │   │
│   │   ├── application/              # use cases / services, DTOs
│   │   │   ├── dtos/
│   │   │   ├── services/
│   │   │   │   ├── opportunity_service.py
│   │   │   │   ├── search_service.py
│   │   │   │   ├── bookmark_service.py
│   │   │   │   ├── recommendation_service.py
│   │   │   │   ├── notification_service.py
│   │   │   │   └── resume_service.py
│   │   │   └── interfaces/            # repository protocols (ports)
│   │   │
│   │   ├── infrastructure/
│   │   │   ├── db/
│   │   │   │   ├── session.py         # SQLAlchemy engine/session
│   │   │   │   ├── models/            # SQLAlchemy ORM models
│   │   │   │   └── repositories/      # concrete repo implementations
│   │   │   ├── search/                # Meilisearch client/adapter
│   │   │   ├── cache/                 # Redis adapter
│   │   │   ├── storage/               # Supabase Storage adapter
│   │   │   └── ai/
│   │   │       ├── llm_client.py
│   │   │       └── embedding_client.py
│   │   │
│   │   ├── connectors/                # see 04-scraper-architecture.md
│   │   │   ├── base.py
│   │   │   ├── pipeline.py
│   │   │   ├── registry.py
│   │   │   ├── greenhouse.py
│   │   │   ├── lever.py
│   │   │   ├── devpost.py
│   │   │   ├── mlh.py
│   │   │   └── ...
│   │   │
│   │   └── tasks/                     # Celery tasks
│   │       ├── celery_app.py
│   │       ├── connector_tasks.py
│   │       ├── notification_tasks.py
│   │       ├── embedding_tasks.py
│   │       └── resume_tasks.py
│   │
│   ├── migrations/                    # Alembic
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── fixtures/                  # connector fixture payloads
│   ├── pyproject.toml
│   ├── alembic.ini
│   └── Dockerfile
│
├── infra/
│   ├── docker-compose.yml             # postgres+pgvector, redis, meilisearch (local dev)
│   ├── railway.json
│   └── seed/                          # seed scripts (sources, tags, skills)
│
├── .github/
│   └── workflows/
│       ├── frontend-ci.yml
│       └── backend-ci.yml
│
├── .env.example
└── README.md
```

## Notes

- **Feature-first** on the frontend: each feature owns its components/hooks/api calls; shared
  primitives live in `components/ui` (shadcn) and `lib`.
- **Clean architecture** on the backend: `api` (interface) → `application` (use cases) →
  `domain` (entities) ← `infrastructure` (implementations of `application/interfaces`). Routers
  depend on services via `Depends`, services depend on repository *protocols*, concrete
  repositories are wired in `core/config.py`/a small DI module.
- **Connectors** and **tasks** are siblings to `api`/`application` — they reuse
  `application/services` and `infrastructure/repositories` but are triggered by Celery, not
  HTTP.
