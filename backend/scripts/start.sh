#!/usr/bin/env sh
# Production entrypoint: apply migrations, optionally seed, then serve.
set -e

echo "Running database migrations..."
alembic upgrade head

if [ "${SEED_ON_START}" = "true" ]; then
  echo "Seeding sample opportunities..."
  python -m app.seed.opportunities || echo "Seed step failed (continuing)."
fi

echo "Starting API on port ${PORT:-8000}..."
# --proxy-headers + --forwarded-allow-ips='*': we run behind Render's TLS-terminating
# proxy, which forwards the real client over X-Forwarded-For/Proto. Without these,
# request.client.host is the proxy's IP — which would bucket every anonymous user
# into one rate-limit key and log the wrong address. '*' is safe here because Render
# is the sole ingress and always sets these headers.
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --proxy-headers \
  --forwarded-allow-ips='*'
