from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.notification import NotificationRead
from app.application.dtos.pagination import Page, PageMeta
from app.core.pagination import decode_cursor, encode_cursor
from app.core.security import AuthenticatedUser
from app.infrastructure.db.models.bookmark import Bookmark
from app.infrastructure.db.models.notification import DeadlineReminderSent, Notification
from app.infrastructure.db.models.opportunity import Opportunity
from app.infrastructure.db.repositories.notification_repository import NotificationRepository


class NotificationService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = NotificationRepository(session)

    async def list_page(
        self, user: AuthenticatedUser, limit: int, cursor: str | None
    ) -> Page[NotificationRead]:
        decoded = decode_cursor(cursor) if cursor else None
        rows, has_more = await self._repo.list_page(user.id, limit, decoded)
        next_cursor = (
            encode_cursor(rows[-1].created_at, rows[-1].id) if has_more and rows else None
        )
        return Page(
            data=[NotificationRead.model_validate(n) for n in rows],
            page=PageMeta(next_cursor=next_cursor, has_more=has_more, limit=limit),
        )

    async def unread_count(self, user: AuthenticatedUser) -> int:
        return await self._repo.unread_count(user.id)

    async def mark_read(self, user: AuthenticatedUser, notification_id: str) -> None:
        await self._repo.mark_read(user.id, notification_id)
        await self._session.commit()

    async def mark_all_read(self, user: AuthenticatedUser) -> None:
        await self._repo.mark_all_read(user.id)
        await self._session.commit()


def _format_deadline(deadline: datetime) -> str:
    return deadline.strftime("%b %d, %Y")


async def generate_deadline_reminders(session: AsyncSession) -> int:
    """Create in-app reminders for bookmarked opportunities whose deadlines fall
    within the next 7 days (24h reminder when very close). Idempotent via the
    deadline_reminders_sent table."""
    now = datetime.now(UTC)
    horizon = now + timedelta(days=7)

    result = await session.execute(
        select(Bookmark.user_id, Opportunity)
        .join(Opportunity, Opportunity.id == Bookmark.opportunity_id)
        .where(
            Opportunity.deadline_at.is_not(None),
            Opportunity.deadline_at > now,
            Opportunity.deadline_at <= horizon,
        )
    )

    created = 0
    for user_id, opp in result.all():
        delta = opp.deadline_at - now
        event = "deadline_24h" if delta <= timedelta(hours=24) else "deadline_7d"

        already = await session.get(
            DeadlineReminderSent,
            {"user_id": user_id, "opportunity_id": opp.id, "event": event},
        )
        if already is not None:
            continue

        when = "in 24 hours" if event == "deadline_24h" else _format_deadline(opp.deadline_at)
        urgency = "soon" if event == "deadline_24h" else "approaching"
        session.add(
            Notification(
                user_id=user_id,
                opportunity_id=opp.id,
                event=event,
                channel="in_app",
                title=f"Deadline {urgency}: {opp.title}",
                body=f"Applications for {opp.title} ({opp.organizer}) close {when}.",
                status="sent",
                sent_at=now,
            )
        )
        session.add(
            DeadlineReminderSent(user_id=user_id, opportunity_id=opp.id, event=event)
        )
        created += 1

    await session.commit()
    return created
