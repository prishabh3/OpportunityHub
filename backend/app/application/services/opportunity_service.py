from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.opportunity import (
    OpportunityDetail,
    OpportunityFilters,
    OpportunitySummary,
    SourceRead,
)
from app.application.dtos.pagination import Page, PageMeta
from app.core.exceptions import NotFoundError
from app.core.pagination import decode_cursor, encode_cursor
from app.infrastructure.db.models.opportunity import Opportunity
from app.infrastructure.db.repositories.opportunity_repository import OpportunityRepository


class OpportunityService:
    def __init__(self, session: AsyncSession) -> None:
        self._repo = OpportunityRepository(session)

    async def list_page(
        self, filters: OpportunityFilters, limit: int, cursor: str | None
    ) -> Page[OpportunitySummary]:
        decoded = decode_cursor(cursor) if cursor else None
        rows, has_more = await self._repo.list_page(filters, limit, decoded)

        next_cursor = (
            encode_cursor(rows[-1].created_at, rows[-1].id) if has_more and rows else None
        )
        return Page(
            data=[self._to_summary(o) for o in rows],
            page=PageMeta(next_cursor=next_cursor, has_more=has_more, limit=limit),
        )

    async def search(self, query: str, limit: int) -> list[OpportunitySummary]:
        if not query.strip():
            return []
        rows = await self._repo.search(query.strip(), limit)
        return [self._to_summary(o) for o in rows]

    async def get(self, opportunity_id: str) -> OpportunityDetail:
        opportunity = await self._repo.get(opportunity_id)
        if opportunity is None:
            raise NotFoundError("Opportunity not found")
        return self._to_detail(opportunity)

    @staticmethod
    def _to_summary(o: Opportunity) -> OpportunitySummary:
        return OpportunitySummary(
            id=o.id,
            type=o.type,
            status=o.status,
            title=o.title,
            organizer=o.organizer,
            location=o.location,
            country=o.country,
            remote_type=o.remote_type,
            difficulty=o.difficulty,
            experience_level=o.experience_level,
            deadline_at=o.deadline_at,
            starts_at=o.starts_at,
            apply_url=o.apply_url,
            banner_url=o.banner_url,
            tags=[t.name for t in o.tags],
        )

    @classmethod
    def _to_detail(cls, o: Opportunity) -> OpportunityDetail:
        summary = cls._to_summary(o)
        return OpportunityDetail(
            **summary.model_dump(),
            description=o.description,
            source_url=o.source_url,
            posted_at=o.posted_at,
            ends_at=o.ends_at,
            details=o.details or {},
            source=SourceRead.model_validate(o.source),
        )
