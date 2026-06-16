import hmac
from typing import Annotated

from fastapi import APIRouter, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.service import run_all
from app.core.config import get_settings
from app.core.exceptions import ForbiddenError, UnauthorizedError
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["ingest"])


@router.post("/ingest/run")
async def run_ingest(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    x_ingest_token: Annotated[str | None, Header()] = None,
    source: str | None = None,
) -> dict[str, list[dict[str, object]]]:
    """Trigger connector ingestion. Protected by a shared `X-Ingest-Token`
    header (set the matching `INGEST_TOKEN` env var). Intended for a scheduled
    cron (e.g. GitHub Actions) or manual runs."""
    settings = get_settings()
    if not settings.ingest_token:
        raise ForbiddenError("Ingestion is not configured")
    if not x_ingest_token or not hmac.compare_digest(x_ingest_token, settings.ingest_token):
        raise UnauthorizedError("Invalid ingest token")

    results = await run_all(session, source)
    return {"results": [r.model_dump() for r in results]}
