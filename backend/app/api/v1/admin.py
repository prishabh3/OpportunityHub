from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.admin import AdminAnalytics, ConnectorRunRead, SourceStat
from app.application.services.admin_service import AdminService
from app.connectors.service import run_all
from app.core.security import AuthenticatedUser, require_admin
from app.infrastructure.db.session import get_db_session

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/analytics", response_model=AdminAnalytics)
async def analytics(
    _: Annotated[AuthenticatedUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> AdminAnalytics:
    return await AdminService(session).analytics()


@router.get("/sources", response_model=list[SourceStat])
async def sources(
    _: Annotated[AuthenticatedUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[SourceStat]:
    return await AdminService(session).sources()


@router.get("/connector-runs", response_model=list[ConnectorRunRead])
async def connector_runs(
    _: Annotated[AuthenticatedUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[ConnectorRunRead]:
    return await AdminService(session).recent_runs()


@router.post("/ingest/run")
async def trigger_ingest(
    _: Annotated[AuthenticatedUser, Depends(require_admin)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, list[dict[str, object]]]:
    """Admin-triggered ingestion (a 'refresh now' button), in addition to the
    cron/token endpoint."""
    results = await run_all(session)
    return {"results": [r.model_dump() for r in results]}
