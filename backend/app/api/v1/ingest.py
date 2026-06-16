from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.service import run_all
from app.core.security import verify_job_token
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["ingest"])


@router.post("/ingest/run", dependencies=[Depends(verify_job_token)])
async def run_ingest(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    source: str | None = None,
) -> dict[str, list[dict[str, object]]]:
    """Trigger connector ingestion. Protected by the `X-Ingest-Token` header
    (matching the `INGEST_TOKEN` env var). Intended for a scheduled cron."""
    results = await run_all(session, source)
    return {"results": [r.model_dump() for r in results]}
