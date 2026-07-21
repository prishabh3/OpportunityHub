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
# Client IP is resolved in the application (app/core/client_ip.py) from the
# TRUSTED_PROXY_HOPS-th entry of X-Forwarded-For, counted from the right.
#
# We deliberately do NOT pass --forwarded-allow-ips='*'. That makes uvicorn trust
# any sender of X-Forwarded-For and take its *leftmost* entry, which is fully
# client-supplied: anyone could set request.client.host to an arbitrary value,
# rotate it per request to bypass IP rate limiting entirely, and forge the
# client_ip in the security logs.
exec uvicorn app.main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}"
