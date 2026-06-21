import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.bookmark import BookmarkCreate, BookmarkRead
from app.application.dtos.pagination import Page
from app.application.services.bookmark_service import BookmarkService
from app.core.security import AuthenticatedUser, get_current_user
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["bookmarks"])


@router.get("/bookmarks", response_model=Page[BookmarkRead])
async def list_bookmarks(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    cursor: Annotated[str | None, Query(max_length=200)] = None,
) -> Page[BookmarkRead]:
    return await BookmarkService(session).list_page(user, limit, cursor)


@router.get("/bookmarks/ids", response_model=list[str])
async def list_bookmark_ids(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> list[str]:
    """Opportunity ids the user has bookmarked — used to render toggle state."""
    return await BookmarkService(session).list_ids(user)


@router.post("/bookmarks", response_model=BookmarkRead, status_code=status.HTTP_201_CREATED)
async def add_bookmark(
    data: BookmarkCreate,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> BookmarkRead:
    return await BookmarkService(session).add(user, data)


@router.delete("/bookmarks/{opportunity_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_bookmark(
    opportunity_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    await BookmarkService(session).remove(user, str(opportunity_id))
