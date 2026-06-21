# Production Security Hardening

Status of every production-security control, mapped to OWASP ASVS. Controls
marked **code** live in this repo; **platform** controls are configured in the
Render / Vercel / Supabase / Upstash dashboards and are recorded here so they
can be audited and re-applied.

## Transport security (ASVS V1.9, V9)

| Control | Where | Status |
|---|---|---|
| HTTPS enforced (frontend) | Vercel — automatic TLS on all deployments | ✅ platform |
| HTTPS enforced (API) | Render — TLS terminated at edge, HTTP 301→HTTPS | ✅ platform |
| Valid TLS certificates | Vercel + Render managed certs (auto-renew) | ✅ platform |
| HSTS (API) | `SecurityHeadersMiddleware`, production only, `max-age=31536000; includeSubDomains; preload` | ✅ code |
| HSTS (frontend) | `next.config.ts` headers, `max-age=63072000; includeSubDomains; preload` | ✅ code |
| Real client IP behind proxy | `uvicorn --proxy-headers --forwarded-allow-ips='*'` in `scripts/start.sh` (so rate-limit/log keying uses X-Forwarded-For, not the Render proxy IP) | ✅ code |

## Security response headers (ASVS V14.4)

Set on **both** tiers — API via `app/core/security_headers.py`, frontend via `next.config.ts`:

- `Content-Security-Policy` — API: `default-src 'none'; frame-ancestors 'none'`. Frontend: scoped allowlist (`default-src 'self'`, `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'none'`).
- `X-Frame-Options: DENY` · `X-Content-Type-Options: nosniff` · `Referrer-Policy: strict-origin-when-cross-origin` · `Permissions-Policy: camera=(), microphone=(), geolocation=(), payment=()`
- `X-Powered-By` removed (`poweredByHeader: false`).

**Follow-up:** the frontend CSP still needs `'unsafe-inline'`/`'unsafe-eval'` for the Next.js runtime. Upgrade to a per-request nonce + `strict-dynamic` when there's bandwidth.

## Infrastructure (ASVS V1.1, V1.2, V14.1)

| Control | Status |
|---|---|
| Database not publicly accessible | ✅ Supabase Postgres reached only via the **Session Pooler** connection string (credentialed); no public 5432 exposure. |
| Redis protected | ✅ Upstash `rediss://` — TLS + token auth, not open to the internet. |
| Secrets stored securely | ✅ `render.yaml` marks `DATABASE_URL`/`REDIS_URL`/`CORS_ORIGINS` as `sync: false` (dashboard-only). No secret is committed; `.env*` are gitignored. Rotation = update env var + redeploy. |
| CORS restrictive | ✅ `allow_origins` = explicit list from `CORS_ORIGINS` (no `*`), methods/headers allowlisted, credentials enabled. **Verify `CORS_ORIGINS` on Render contains only the production Vercel domain.** |
| Sensitive endpoints require auth | ✅ All user routes use `get_current_user`; admin routes `require_admin`; cron routes `verify_job_token` (timing-safe). See `docs` / access-control audit. |
| Internal services protected | ✅ Ingestion/notification cron endpoints require the `X-Ingest-Token` shared secret. |

## Structured logging (ASVS V7.1, V7.2)

JSON logs via structlog (`app/core/logging.py`). `RequestContextMiddleware` binds
`request_id`, `method`, `path`, `client_ip` to **every** log line and returns the
id as the `X-Request-ID` header for end-to-end correlation.

Security-relevant events (all queryable by the `event` field):

| Event | Level | Meaning |
|---|---|---|
| `jwt_expired`, `jwt_invalid` | warning | Authentication attempt with a bad/expired token |
| `security_event` | warning | Any 401 / 403 / 429 response (authz failure / throttle) |
| `admin_access_denied` | warning | Non-admin tried an admin route (privilege-escalation attempt) |
| `admin_access_granted` | info | Successful admin access (audit trail) |
| `rate_limited` | warning | Global or per-route limit exceeded (incl. `scope`, `identity`, `path`) |
| `unhandled_exception` | error | Uncaught server error — full stack trace (never leaked to client) |
| `app_error` | error | Handled 5xx domain error |
| `rate_limit_redis_unavailable` | warning | Limiter failed open due to Redis outage |

> **Auth events that are NOT here:** login, signup, failed-login, password-reset,
> and OTP happen client→Supabase Auth directly and never reach this backend.
> Their logs/metrics live in **Supabase → Auth → Logs**, and their rate
> limiting / CAPTCHA / lockout are configured in the Supabase dashboard.

## Monitoring & alerting

Wire a log drain (Render → Logtail/Datadog/etc.) and alert on these structured events:

| Alert | Condition |
|---|---|
| Repeated failed logins / credential stuffing | Supabase Auth: failed sign-ins > N / 5 min per IP or email *(configure in Supabase; enable CAPTCHA + leaked-password protection)* |
| Brute-force on the API | `event=jwt_invalid` spike, or `event=security_event status_code=401` > N / min per `client_ip` |
| Privilege-escalation attempts | any `event=admin_access_denied` (alert immediately; should be rare) |
| Unusual traffic spike / scraping / DoS | `event=rate_limited` rate climbing, or one `identity` with sustained hits |
| Suspicious API usage | `event=security_event status_code=403` clusters |
| Unexpected server errors | `event=unhandled_exception` rate > baseline (page on sustained 5xx) |
| Limiter degraded | any `event=rate_limit_redis_unavailable` (Redis health) |

### Supabase dashboard checklist (auth abuse — not in code)
- **Auth → Rate Limits:** confirm per-IP/email caps for sign-in, sign-up, OTP, password-reset, email-verify.
- **Auth → Bot & Abuse Protection:** enable CAPTCHA (hCaptcha / Turnstile).
- **Auth → Passwords:** enable leaked-password (HIBP) protection; min length ≥ 8.
- Admin role is granted only via `app_metadata.role` (not user-editable) — never via `user_metadata`.
