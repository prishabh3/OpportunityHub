from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.profile import ProfileRead, ProfileUpdate
from app.application.services.profile_service import ProfileService
from app.core.security import AuthenticatedUser, get_current_user
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["profile"])


@router.get("/me", response_model=ProfileRead)
async def read_me(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileRead:
    """Return the current user's profile, creating it on first access."""
    return await ProfileService(session).get_or_create(user)


@router.patch("/me", response_model=ProfileRead)
async def update_me(
    data: ProfileUpdate,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> ProfileRead:
    """Partially update the current user's profile."""
    return await ProfileService(session).update(user, data)
