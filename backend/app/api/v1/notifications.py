import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.notification import NotificationRead
from app.application.dtos.pagination import Page
from app.application.services.notification_service import (
    NotificationService,
    generate_deadline_reminders,
)
from app.core.security import AuthenticatedUser, get_current_user, verify_job_token
from app.infrastructure.db.session import get_db_session

router = APIRouter(tags=["notifications"])


@router.get("/notifications", response_model=Page[NotificationRead])
async def list_notifications(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> Page[NotificationRead]:
    return await NotificationService(session).list_page(user, limit, cursor)


@router.get("/notifications/unread-count")
async def unread_count(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, int]:
    return {"count": await NotificationService(session).unread_count(user)}


@router.post("/notifications/read-all", status_code=status.HTTP_204_NO_CONTENT)
async def mark_all_read(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    await NotificationService(session).mark_all_read(user)


@router.post("/notifications/{notification_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_read(
    notification_id: uuid.UUID,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    await NotificationService(session).mark_read(user, str(notification_id))


@router.post("/notifications/run", dependencies=[Depends(verify_job_token)])
async def run_notifications(
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> dict[str, int]:
    """Cron-triggered: generate deadline reminders. Same token as ingestion."""
    created = await generate_deadline_reminders(session)
    return {"created": created}
