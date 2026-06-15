# OpportunityHub — Connector / Scraper Architecture

## 1. Goals

- Each source (Google Careers, Devpost, MLH, Unstop, ...) is an **isolated connector** — one
  connector's failure or rate-limiting never affects another.
- A shared **pipeline** (normalize → validate → deduplicate → upsert → side-effects) so
  connectors only implement *fetch* + *parse*.
- New sources are added by writing one class + a registry entry — no changes to core code.

## 2. Compliance Note (important)

Several listed sources (LinkedIn, Amazon Careers, etc.) have Terms of Service that restrict
automated scraping. The connector framework must support multiple acquisition strategies and
the registry should record which strategy is legally appropriate per source:

- **Official API** (preferred): Greenhouse/Lever/Workday job board APIs (many big tech careers
  sites are built on these), Devpost API, GitHub API for university hackathon repos.
- **RSS/Atom feeds**: many career sites and Kaggle/Devpost expose feeds.
- **Public JSON endpoints** used by the site's own frontend (still subject to ToS — use
  conservatively, low frequency, identify with a real User-Agent).
- **HTML scraping**: last resort, only for sources whose ToS/robots.txt permit it, with strict
  rate limits and caching.

`sources.key` maps to a connector class; `sources` also stores which strategy is used so the
admin panel can flag any source that needs legal review before enabling.

## 3. Core Abstractions (`backend/app/connectors/`)

```python
# base.py
class RawItem(BaseModel):
    """Unstructured data as returned by a connector's fetch step."""
    external_id: str
    payload: dict[str, Any]

class NormalizedOpportunity(BaseModel):
    """Fully normalized, matches the `opportunities` table shape."""
    external_id: str
    type: OpportunityType
    title: str
    organizer: str
    description: str | None
    location: str | None
    country: str | None
    remote_type: RemoteType
    difficulty: DifficultyLevel
    posted_at: datetime | None
    deadline_at: datetime | None
    starts_at: datetime | None
    ends_at: datetime | None
    apply_url: str
    source_url: str | None
    banner_url: str | None
    details: dict[str, Any]
    tags: list[str]

class BaseConnector(ABC):
    source_key: str
    opportunity_types: list[OpportunityType]

    @abstractmethod
    async def fetch(self) -> AsyncIterator[RawItem]:
        """Pull raw data from the source (API call, RSS parse, HTML fetch)."""

    @abstractmethod
    def normalize(self, item: RawItem) -> NormalizedOpportunity:
        """Map raw payload -> NormalizedOpportunity."""

    def content_hash(self, item: NormalizedOpportunity) -> str:
        """sha256 of (title, organizer, apply_url, deadline_at) — detects real changes
        vs. re-ingestion of unchanged data."""
```

## 4. Pipeline (`backend/app/connectors/pipeline.py`)

```
fetch() ──▶ normalize() ──▶ validate (pydantic) ──▶ deduplicate ──▶ upsert ──▶ side effects
```

1. **Fetch** — connector-specific, yields `RawItem`s (paginated internally).
2. **Normalize** — connector-specific, maps to `NormalizedOpportunity`.
3. **Validate** — Pydantic model validation; invalid items are logged to
   `connector_runs.log.invalid_items` and skipped (don't fail the whole run).
4. **Deduplicate** — primary key is `(source_id, external_id)` (DB unique constraint handles
   exact re-runs). Cross-source duplicate detection (same internship posted on LinkedIn *and*
   the company site) uses a secondary fuzzy match: `pg_trgm` similarity on
   `(title, organizer, apply_url)` above a threshold flags possible duplicates for an admin
   review queue (`opportunities.details.possible_duplicate_of`), not auto-merged.
5. **Upsert** — `INSERT ... ON CONFLICT (source_id, external_id) DO UPDATE`. Compares
   `content_hash`; if unchanged, only `updated_at`/`status` touched (cheap). If changed,
   full update + flag for re-embedding.
6. **Side effects** (enqueued as separate Celery tasks, not inline):
   - `embed_opportunity.delay(opportunity_id)` — generate/update pgvector embedding.
   - `sync_to_meilisearch.delay(opportunity_id)`.
   - `evaluate_notifications.delay(opportunity_id)` — match against user preferences/profiles
     for `new_match` / `company_alert` notifications (new items only).
   - if `deadline_at` changed on an existing record → `notify_deadline_changed.delay(...)`.

## 5. Scheduling

- Celery Beat reads `sources` table (cached, refreshed every 5 min) and schedules one task per
  active source using its `schedule_cron`.
- Each connector run creates a `connector_runs` row (`status=running`), updates counts as it
  processes, and finalizes `status` (`success` / `partial` / `failed`) + `finished_at`.
- Per-connector concurrency limit of 1 (no overlapping runs) via Celery's
  `ONCE`/lock pattern (Redis lock keyed on `source.key`).
- Exponential backoff retry (max 3) on transient errors (timeouts, 5xx); permanent errors
  (4xx, parse errors) logged and the run marked `partial`/`failed` without retry storms.

## 6. Connector Registry (`backend/app/connectors/registry.py`)

```python
CONNECTOR_REGISTRY: dict[str, type[BaseConnector]] = {
    "google_careers": GoogleCareersConnector,
    "microsoft_careers": MicrosoftCareersConnector,
    "devpost": DevpostConnector,
    "mlh": MLHConnector,
    "unstop": UnstopConnector,
    "yc_jobs": YCJobsConnector,
    "greenhouse_generic": GreenhouseConnector,  # parameterized by board token, covers many cos.
    "lever_generic": LeverConnector,            # parameterized by company slug
    # ... additional connectors registered the same way
}
```

- `GreenhouseConnector` / `LeverConnector` are **parameterized connectors** — a single
  implementation reused for every company whose careers page is a Greenhouse/Lever board
  (covers a large fraction of the "Internships/Full-time" company list via their public
  job-board JSON APIs). Each company is a row in `sources` with `details->>'board_token'`.

## 7. Adding a New Connector (checklist)

1. Add a row to `sources` (key, display_name, base_url, opportunity_types, schedule_cron,
   acquisition strategy in `details`).
2. Implement `fetch()` + `normalize()` in `backend/app/connectors/<key>.py`.
3. Register in `CONNECTOR_REGISTRY`.
4. Write a unit test with a recorded fixture (HTML/JSON sample) asserting `normalize()` output.
5. Run against staging once manually via `POST /admin/connector-runs/{source_id}/trigger`
   before enabling the schedule.

## 8. Initial Connector Set (Milestone 3)

Prioritized for reliability (official APIs / structured feeds first):

| Connector | Type(s) | Strategy |
|---|---|---|
| Greenhouse (generic, many companies) | internship, full_time_job | Public board API |
| Lever (generic, many companies) | internship, full_time_job | Public API |
| Devpost | hackathon | Public API |
| MLH | hackathon | Public events API/feed |
| Unstop | hackathon, competition | Public API/JSON endpoints |
| YC Jobs (Work at a Startup) | internship, full_time_job | Public API |
| Google Summer of Code | research_program | Official org list (JSON) |
| Outreachy | research_program | Public API |
