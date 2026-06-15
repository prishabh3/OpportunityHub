# OpportunityHub — Notification Architecture

## 1. Channels

| Channel | Delivery mechanism |
|---|---|
| Email | Transactional email provider (Resend or SendGrid) via Celery task |
| Push | Web Push (VAPID) — subscription stored in `notification_preferences.push_subscription` |
| Discord | User-configured incoming webhook URL (`notification_preferences.discord_webhook_url`) |
| Telegram | Bot API, `chat_id` from `notification_preferences.telegram_chat_id` (user links via `/start <token>` bot command) |

All notifications are first written to the `notifications` table (status=`pending`), then a
channel-specific sender task delivers and updates `status`/`sent_at`. This gives an in-app
notification center "for free" and a retry-able audit trail.

## 2. Event Types & Triggers

| Event | Trigger | Producer |
|---|---|---|
| `new_match` | New opportunity ingested whose tags/company/role match a user's profile/preferences above a threshold | `evaluate_notifications` task (per new opportunity, fan-out to matching users) |
| `company_alert` | New opportunity from a user's `preferred_companies` list | same task, higher priority |
| `deadline_24h` | `deadline_at` within 24h and user has bookmarked or matches | Hourly Celery Beat task `check_upcoming_deadlines` |
| `deadline_7d` | `deadline_at` within 7 days | same task |
| `deadline_changed` | Connector upsert detects `deadline_at` diff on existing opportunity | Pipeline upsert step |
| `weekly_digest` | Scheduled weekly (per user timezone) | Celery Beat task `send_weekly_digest` |

## 3. Fan-out Strategy

Naively evaluating every user against every new opportunity doesn't scale past a few thousand
users. Approach:

1. **Coarse pre-filter in SQL**: for `new_match`/`company_alert`, query
   `profiles`/`notification_preferences` joined with `opportunity_tags`/`details` using
   indexed columns (preferred_companies @> array, tag overlap) to get a candidate user list —
   this is cheap and bounds the set to users plausibly interested.
2. **Fine-grained scoring**: for the candidate set, compute/lookup `opportunity_matches`
   (cosine similarity via pgvector + rule bonuses). Only score >= threshold (configurable,
   default 70) triggers a notification.
3. **Batching**: notifications for a user created within a short window (e.g. 10 min) are
   coalesced into a single email ("3 new opportunities match your profile") by the email sender
   task rather than sending one email per opportunity.

## 4. Deadline Intelligence

- `check_upcoming_deadlines` (hourly):
  ```sql
  select * from opportunities
  where status = 'active'
    and deadline_at between now() + interval '23 hours' and now() + interval '24 hours'
  ```
  (similarly for 7-day window), joined against users who bookmarked the opportunity OR have a
  cached `opportunity_matches` row above threshold.
- Idempotency via `deadline_reminders_sent` table (composite PK `(user_id, opportunity_id,
  event)`) — the task inserts before sending; `ON CONFLICT DO NOTHING` + skip if already exists.
- `deadline_changed`: pipeline compares old vs new `deadline_at`; if different, immediately
  enqueues `deadline_changed` notification for users with that item bookmarked (regardless of
  threshold — this is high-signal).

## 5. Weekly Digest

- `send_weekly_digest` runs hourly but only processes users whose local time matches their
  configured digest time (default Monday 9am in `profiles.timezone`).
- Digest content: top N recommended opportunities (from `opportunity_matches`), upcoming
  deadlines in next 7 days (from bookmarks), and "new this week" counts per category.
- Rendered via a Jinja2 email template; same data also available via
  `GET /api/v1/dashboard` for in-app parity.

## 6. Delivery Tasks

```python
@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def send_email_notification(self, notification_id: str): ...

@celery_app.task(bind=True, max_retries=3)
def send_discord_notification(self, notification_id: str): ...

@celery_app.task(bind=True, max_retries=3)
def send_telegram_notification(self, notification_id: str): ...

@celery_app.task
def send_push_notification(notification_id: str): ...
```

Each task: loads the `notifications` row + user's `notification_preferences`, renders the
message for that channel, sends, updates `status`/`sent_at` (or `failed` + error in `log`).
Failures retry with exponential backoff; after max retries, `status='failed'` and surfaced in
the admin "Failed jobs" view.

## 7. In-App Notification Center

- `GET /api/v1/notifications` (cursor-paginated, filter `unread=true`) backs a bell-icon
  dropdown + dedicated page.
- Realtime updates via Supabase Realtime (Postgres logical replication on `notifications`
  table) — frontend subscribes to `notifications` rows for `user_id = auth.uid()`.
