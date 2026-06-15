# OpportunityHub — Authentication & Authorization

## 1. Provider: Supabase Auth

Supabase Auth handles all credential management, OAuth flows, session/refresh tokens, and email
verification. Neither Next.js nor FastAPI implement their own auth — they consume Supabase.

Enabled methods:
- Email + password (with email verification)
- Google OAuth
- GitHub OAuth

## 2. Frontend Flow

- `@supabase/ssr` integrates Supabase auth with Next.js App Router (cookie-based sessions,
  works with Server Components).
- Middleware (`middleware.ts`) refreshes the session cookie on every request and redirects
  unauthenticated users away from `/dashboard`, `/profile`, `/bookmarks`, etc.
- Sign-in/sign-up pages call `supabase.auth.signInWithPassword`,
  `supabase.auth.signInWithOAuth({ provider: 'google' | 'github' })`,
  `supabase.auth.signUp`.
- On successful auth, Supabase issues a JWT (access token, ~1h expiry) + refresh token.
  `@supabase/ssr` handles silent refresh.

## 3. Backend Verification

FastAPI never talks to Supabase Auth's write APIs. It only **verifies** JWTs:

```python
# app/core/security.py
class SupabaseJWTVerifier:
    def __init__(self, jwks_url: str, audience: str):
        self._jwks_client = PyJWKClient(jwks_url)

    def verify(self, token: str) -> AuthenticatedUser:
        signing_key = self._jwks_client.get_signing_key_from_jwt(token)
        payload = jwt.decode(
            token, signing_key.key, algorithms=["ES256", "RS256"],
            audience=self._audience,
        )
        return AuthenticatedUser(
            id=payload["sub"],
            email=payload.get("email"),
            role=payload.get("app_metadata", {}).get("role", "user"),
        )
```

JWKS response is cached (PyJWKClient handles this) — no per-request network call after warmup.

### Dependencies

```python
async def get_current_user(
    authorization: str = Header(...),
    verifier: SupabaseJWTVerifier = Depends(get_jwt_verifier),
) -> AuthenticatedUser:
    token = authorization.removeprefix("Bearer ").strip()
    try:
        return verifier.verify(token)
    except (InvalidTokenError, ExpiredSignatureError) as e:
        raise UnauthorizedError() from e

async def get_current_user_optional(...) -> AuthenticatedUser | None:
    """For endpoints (e.g. /opportunities) that personalize when authed but allow anon."""

async def require_admin(
    user: AuthenticatedUser = Depends(get_current_user),
) -> AuthenticatedUser:
    if user.role != "admin":
        raise ForbiddenError()
    return user
```

## 4. Role Management

- `profiles.role` is the source of truth for app-level authorization (checked by
  `require_admin`).
- Supabase JWT `app_metadata.role` is kept in sync via a Postgres trigger
  (`profiles` update → `auth.users.raw_app_meta_data`) so the role is also embedded in the JWT
  for defense-in-depth at the RLS layer (`auth.jwt() ->> 'role'` used in admin-only RLS
  policies, if/when needed beyond the per-user policies already defined).
- Promoting a user to admin is an admin-only operation:
  `PATCH /api/v1/admin/users/{id} { "role": "admin" }`.

## 5. Row-Level Security as Defense in Depth

Even though FastAPI authorizes every request, Supabase RLS policies (see
`02-database-schema.sql`) ensure that **if** a client ever talks to Postgres directly (e.g.
Supabase Realtime subscriptions for the notification bell), it's still scoped to `auth.uid()`.
The FastAPI backend connects with a service-role key (bypasses RLS) since it performs its own
authorization — RLS is the safety net for direct client access paths only.

## 6. Token Flow Summary

```
┌────────┐  signInWithOAuth   ┌──────────────┐
│ Browser│ ─────────────────▶ │ Supabase Auth│
│        │ ◀───────────────── │ (Google/GH)  │
└───┬────┘   session + JWT     └──────────────┘
   │
   │  fetch('/api/v1/...', { headers: { Authorization: `Bearer ${jwt}` }})
   ▼
┌──────────────┐   verify via JWKS   ┌───────────────┐
│ FastAPI       │ ──────────────────▶│ Supabase JWKS │
│ (stateless)   │ ◀──────────────────│ endpoint       │
└──────────────┘    public keys      └───────────────┘
```

## 7. Service-to-Service Auth

Celery workers and the FastAPI app share the same Supabase service-role key (env var, never
exposed to frontend) for direct DB access — they don't go through the REST API.

## 8. Security Notes

- CORS: only the deployed frontend origin(s) + localhost (dev) allowed on the FastAPI app.
- All write endpoints validate `user_id` ownership server-side (never trust a client-supplied
  `user_id` in the body — always derive from the verified JWT `sub`).
- Resume uploads: validated MIME type + size limit (5MB), stored under a per-user prefix in a
  private Supabase Storage bucket with signed-URL access only.
- Rate limiting (see API design doc) applies per-`user_id` post-auth, per-IP pre-auth.
