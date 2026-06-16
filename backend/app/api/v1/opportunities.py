from typing import Annotated, Literal

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

# Top-level categories grouping the opportunity types.
CATEGORY_TYPES: dict[str, list[OpportunityType]] = {
    "hackathons": ["hackathon", "competition"],
    "jobs": ["internship", "full_time_job", "research_program"],
}
Category = Literal["hackathons", "jobs"]


@router.get("/opportunities", response_model=Page[OpportunitySummary])
async def list_opportunities(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    category: Category | None = None,
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
    """Public, filterable, cursor-paginated list of opportunities.

    `category` expands to a set of types (a specific `type` narrows within it).
    """
    filters = OpportunityFilters(
        type=type,
        types=CATEGORY_TYPES[category] if category else None,
        status=status,
        country=country,
        remote_type=remote_type,
        difficulty=difficulty,
        q=q,
        tag=tag,
    )
    return await OpportunityService(session).list_page(filters, limit, cursor)


@router.get("/opportunities/{opportunity_id}", response_model=OpportunityDetail)
async def get_opportunity(
    opportunity_id: str,
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> OpportunityDetail:
    return await OpportunityService(session).get(opportunity_id)
