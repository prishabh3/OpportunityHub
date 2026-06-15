from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.opportunity import (
    DifficultyLevel,
    OpportunityDetail,
    OpportunityFilters,
    OpportunityStatus,
    OpportunitySummary,
    OpportunityType,
    RemoteType,
)
from app.application.dtos.pagination import Page
from app.application.services.opportunity_service import OpportunityService
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities", response_model=Page[OpportunitySummary])
async def list_opportunities(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    type: OpportunityType | None = None,
    status: OpportunityStatus | None = None,
    country: str | None = None,
    remote_type: RemoteType | None = None,
    difficulty: DifficultyLevel | None = None,
    q: str | None = None,
    tag: str | None = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: str | None = None,
) -> Page[OpportunitySummary]:
    """Public, filterable, cursor-paginated list of opportunities."""
    filters = OpportunityFilters(
        type=type,
        status=status,
        country=country,
        remote_type=remote_type,
        difficulty=difficulty,
        q=q,
        tag=tag,
    )
    return await OpportunityService(session).list(filters, limit, cursor)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityDetail)
async def get_opportunity(
    opportunity_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OpportunityDetail:
    return await OpportunityService(session).get(opportunity_id)
