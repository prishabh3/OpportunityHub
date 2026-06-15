FROM python:3.12-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

COPY pyproject.toml ./
COPY app ./app
COPY migrations ./migrations
COPY alembic.ini ./
COPY scripts ./scripts

RUN pip install . && chmod +x scripts/start.sh

EXPOSE 8000

# Honors $PORT (set by the host), runs migrations, then serves.
CMD ["./scripts/start.sh"]
