from datetime import UTC, datetime

from sqlalchemy import and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.notification import Notification


class NotificationRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_page(
        self, user_id: str, limit: int, cursor: tuple[datetime, str] | None
    ) -> tuple[list[Notification], bool]:
        stmt = select(Notification).where(Notification.user_id == user_id)
        if cursor is not None:
            created_at, item_id = cursor
            stmt = stmt.where(
                or_(
                    Notification.created_at < created_at,
                    and_(Notification.created_at == created_at, Notification.id < item_id),
                )
            )
        stmt = stmt.order_by(Notification.created_at.desc(), Notification.id.desc())
        stmt = stmt.limit(limit + 1)
        result = await self._session.execute(stmt)
        rows = list(result.scalars().all())
        return rows[:limit], len(rows) > limit

    async def unread_count(self, user_id: str) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
        )
        return int(result.scalar_one())

    async def mark_read(self, user_id: str, notification_id: str) -> None:
        await self._session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.id == notification_id)
            .values(read_at=datetime.now(UTC))
        )

    async def mark_all_read(self, user_id: str) -> None:
        await self._session.execute(
            update(Notification)
            .where(Notification.user_id == user_id, Notification.read_at.is_(None))
            .values(read_at=datetime.now(UTC))
        )
