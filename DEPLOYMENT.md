# Deploying OpportunityHub (free tier)

Stack: **Vercel** (frontend) · **Render** (backend, Docker) · **Supabase** (Postgres + Auth) · **Upstash** (Redis).

The backend container runs migrations on boot (`scripts/start.sh`) and seeds sample
data when `SEED_ON_START=true`.

---

## 1. Database — Supabase (already provisioned)

The backend will use your Supabase Postgres directly. Grab the connection string:

- Supabase → **Project Settings → Database → Connection string → "Session pooler"**
- It looks like:
  `postgresql://postgres.ivhwuoeukukieuwvsszq:[PASSWORD]@aws-0-<region>.pooler.supabase.com:5432/postgres`
- Convert the scheme for asyncpg — replace `postgresql://` with `postgresql+asyncpg://`.
- Use the **Session pooler** (port 5432), not the Transaction pooler (6543).

> This is `DATABASE_URL` for Render. Keep the password private.

## 2. Redis — Upstash

- [upstash.com](https://upstash.com) → create a free **Redis** database.
- Copy the **`rediss://...`** connection URL (TLS). This is `REDIS_URL`.

## 3. Backend — Render

Option A (Blueprint): Render → **New → Blueprint** → pick this repo → it reads `render.yaml`.
Option B (manual): **New → Web Service** → this repo → Runtime **Docker**, Root `backend`, Health check `/api/v1/health`, Plan **Free**.

Set environment variables:

| Key | Value |
| --- | --- |
| `ENVIRONMENT` | `production` |
| `DATABASE_URL` | Supabase session-pooler URL (`postgresql+asyncpg://...`) |
| `REDIS_URL` | Upstash `rediss://...` URL |
| `SUPABASE_URL` | `https://ivhwuoeukukieuwvsszq.supabase.co` |
| `SUPABASE_JWT_AUDIENCE` | `authenticated` |
| `CORS_ORIGINS` | `["https://<your-vercel-app>.vercel.app"]` (update after step 4) |
| `SEED_ON_START` | `true` (set back to `false` after the first successful deploy) |

Deploy → note the service URL, e.g. `https://opportunityhub-api.onrender.com`.

## 4. Frontend — Vercel

- [vercel.com](https://vercel.com) → **Add New → Project** → import this repo.
- **Root Directory**: `frontend`.
- Environment variables:

| Key | Value |
| --- | --- |
| `NEXT_PUBLIC_SUPABASE_URL` | `https://ivhwuoeukukieuwvsszq.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | your Supabase publishable/anon key |
| `NEXT_PUBLIC_API_BASE_URL` | the Render backend URL from step 3 |

Deploy → note the domain, e.g. `https://opportunityhub.vercel.app`.

## 5. Wire the domains together

- **Render** → set `CORS_ORIGINS` to `["https://<your-vercel-app>.vercel.app"]` → redeploy.
- **Supabase → Authentication → URL Configuration**:
  - **Site URL**: `https://<your-vercel-app>.vercel.app`
  - **Redirect URLs**: add `https://<your-vercel-app>.vercel.app/auth/callback`

Done. Visit the Vercel URL — sign up, browse opportunities, edit your profile.

> Render free web services sleep after ~15 min idle; the first request then takes
> ~50s to wake. Set `SEED_ON_START=false` after the initial deploy so restarts are quick.
