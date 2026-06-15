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
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
