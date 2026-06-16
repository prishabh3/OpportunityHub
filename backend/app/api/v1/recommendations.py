from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.recommendation import RecommendedOpportunity
from app.application.services.recommendation_service import RecommendationService
from app.core.security import AuthenticatedUser, get_current_user
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["recommendations"])


@router.get("/recommendations", response_model=list[RecommendedOpportunity])
async def get_recommendations(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=50)] = 12,
) -> list[RecommendedOpportunity]:
    """Opportunities ranked by how well they match the user's profile."""
    return await RecommendationService(session).recommend(user, limit)
