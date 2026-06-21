from datetime import datetime

from sqlalchemy import and_, delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.bookmark import Bookmark


class BookmarkRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_page(
        self, user_id: str, limit: int, cursor: tuple[datetime, str] | None
    ) -> tuple[list[Bookmark], bool]:
        stmt = select(Bookmark).where(Bookmark.user_id == user_id)
        if cursor is not None:
            created_at, item_id = cursor
            stmt = stmt.where(
                or_(
                    Bookmark.created_at < created_at,
                    and_(Bookmark.created_at == created_at, Bookmark.id < item_id),
                )
            )
        stmt = stmt.order_by(Bookmark.created_at.desc(), Bookmark.id.desc()).limit(limit + 1)
        result = await self._session.execute(stmt)
        rows = list(result.scalars().unique().all())
        return rows[:limit], len(rows) > limit

    async def list_opportunity_ids(self, user_id: str) -> list[str]:
        result = await self._session.execute(
            select(Bookmark.opportunity_id).where(Bookmark.user_id == user_id)
        )
        return list(result.scalars().all())

    async def get(self, user_id: str, opportunity_id: str) -> Bookmark | None:
        result = await self._session.execute(
            select(Bookmark).where(
                Bookmark.user_id == user_id, Bookmark.opportunity_id == opportunity_id
            )
        )
        return result.scalar_one_or_none()

    async def add(
        self, user_id: str, opportunity_id: str, notes: str | None, tags: list[str]
    ) -> Bookmark:
        bookmark = Bookmark(user_id=user_id, opportunity_id=opportunity_id, notes=notes, tags=tags)
        self._session.add(bookmark)
        await self._session.flush()
        await self._session.refresh(bookmark)
        return bookmark

    async def delete(self, user_id: str, opportunity_id: str) -> None:
        await self._session.execute(
            delete(Bookmark).where(
                Bookmark.user_id == user_id, Bookmark.opportunity_id == opportunity_id
            )
        )
