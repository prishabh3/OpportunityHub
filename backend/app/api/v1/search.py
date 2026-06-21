from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.opportunity import OpportunitySummary
from app.application.services.opportunity_service import OpportunityService
from app.core.config import get_settings
from app.core.rate_limit import RateLimiter
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["search"])

# Full-text search is the most expensive public endpoint (ranked ts_query over the
# whole table). A tight sliding-window limit blocks scraping / DoS via search spam,
# layered under the global per-identity budget.
_search_limiter = RateLimiter(
    times=get_settings().rate_limit_search_per_minute, scope="search"
)


@router.get(
    "/search",
    response_model=list[OpportunitySummary],
    dependencies=[Depends(_search_limiter)],
)
async def search_opportunities(
    session: Annotated[AsyncSession, Depends(get_db_session)],
    q: Annotated[str, Query(min_length=1, max_length=200)],
    limit: Annotated[int, Query(ge=1, le=50)] = 30,
) -> list[OpportunitySummary]:
    """Full-text search across opportunities, ranked by relevance."""
    return await OpportunityService(session).search(q, limit)
