from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.bookmark import BookmarkCreate, BookmarkRead
from app.application.dtos.pagination import Page, PageMeta
from app.application.services.opportunity_service import OpportunityService
from app.application.services.profile_service import ProfileService
from app.core.exceptions import NotFoundError
from app.core.pagination import decode_cursor, encode_cursor
from app.core.security import AuthenticatedUser
from app.infrastructure.db.models.bookmark import Bookmark
from app.infrastructure.db.repositories.bookmark_repository import BookmarkRepository
from app.infrastructure.db.repositories.opportunity_repository import OpportunityRepository


class BookmarkService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = BookmarkRepository(session)
        self._opportunities = OpportunityRepository(session)

    async def list_page(
        self, user: AuthenticatedUser, limit: int, cursor: str | None
    ) -> Page[BookmarkRead]:
        decoded = decode_cursor(cursor) if cursor else None
        rows, has_more = await self._repo.list_page(user.id, limit, decoded)
        next_cursor = (
            encode_cursor(rows[-1].created_at, rows[-1].id) if has_more and rows else None
        )
        return Page(
            data=[self._to_read(b) for b in rows],
            page=PageMeta(next_cursor=next_cursor, has_more=has_more, limit=limit),
        )

    async def list_ids(self, user: AuthenticatedUser) -> list[str]:
        return await self._repo.list_opportunity_ids(user.id)

    async def add(self, user: AuthenticatedUser, data: BookmarkCreate) -> BookmarkRead:
        opportunity = await self._opportunities.get(data.opportunity_id)
        if opportunity is None:
            raise NotFoundError("Opportunity not found")

        # Ensure the user's profile row exists (bookmarks FK references profiles).
        await ProfileService(self._session).get_or_create(user)

        existing = await self._repo.get(user.id, data.opportunity_id)
        if existing is not None:
            return self._to_read(existing)

        try:
            bookmark = await self._repo.add(user.id, data.opportunity_id, data.notes, data.tags)
            await self._session.commit()
        except IntegrityError:
            # Concurrent add hit the (user_id, opportunity_id) unique constraint —
            # treat the request as idempotent and return the existing bookmark.
            await self._session.rollback()
            current = await self._repo.get(user.id, data.opportunity_id)
            if current is None:
                raise
            return self._to_read(current)

        return self._to_read(bookmark)

    async def remove(self, user: AuthenticatedUser, opportunity_id: str) -> None:
        await self._repo.delete(user.id, opportunity_id)
        await self._session.commit()

    @staticmethod
    def _to_read(bookmark: Bookmark) -> BookmarkRead:
        return BookmarkRead(
            id=bookmark.id,
            opportunity_id=bookmark.opportunity_id,
            notes=bookmark.notes,
            tags=bookmark.tags or [],
            created_at=bookmark.created_at,
            opportunity=OpportunityService._to_summary(bookmark.opportunity),
        )
