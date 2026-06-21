from datetime import datetime

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select

from app.application.dtos.opportunity import OpportunityFilters
from app.core.validators import escape_like
from app.infrastructure.db.models.opportunity import Opportunity, Tag


class OpportunityRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @staticmethod
    def _apply_filters(
        stmt: "Select[tuple[Opportunity]]", f: OpportunityFilters
    ) -> "Select[tuple[Opportunity]]":
        if f.type:
            stmt = stmt.where(Opportunity.type == f.type)
        elif f.types:
            stmt = stmt.where(Opportunity.type.in_(f.types))
        if f.status:
            stmt = stmt.where(Opportunity.status == f.status)
        if f.country:
            stmt = stmt.where(func.lower(Opportunity.country) == f.country.lower())
        if f.remote_type:
            stmt = stmt.where(Opportunity.remote_type == f.remote_type)
        if f.difficulty:
            stmt = stmt.where(Opportunity.difficulty == f.difficulty)
        if f.experience_level:
            stmt = stmt.where(Opportunity.experience_level == f.experience_level)
        if f.q:
            # Escape LIKE wildcards (%, _, \) before building the pattern so
            # user input is treated as a literal substring, not a LIKE pattern.
            # Without this, a query containing "%" matches every row and causes
            # a catastrophically expensive full-table scan (algorithmic DoS).
            like = f"%{escape_like(f.q)}%"
            stmt = stmt.where(
                or_(
                    Opportunity.title.ilike(like, escape="\\"),
                    Opportunity.organizer.ilike(like, escape="\\"),
                    Opportunity.description.ilike(like, escape="\\"),
                )
            )
        if f.tag:
            stmt = stmt.where(Opportunity.tags.any(Tag.name == f.tag))
        return stmt

    async def list_page(
        self,
        filters: OpportunityFilters,
        limit: int,
        cursor: tuple[datetime, str] | None,
    ) -> tuple[list[Opportunity], bool]:
        """Keyset pagination ordered by (created_at, id) descending. Fetches one
        extra row to determine whether more pages exist."""
        stmt = self._apply_filters(select(Opportunity), filters)
        if cursor is not None:
            created_at, item_id = cursor
            # Keyset predicate: everything strictly "after" the cursor row in
            # (created_at desc, id desc) order. Comparing against the typed
            # columns coerces the bind params to timestamptz / uuid correctly.
            stmt = stmt.where(
                or_(
                    Opportunity.created_at < created_at,
                    and_(
                        Opportunity.created_at == created_at,
                        Opportunity.id < item_id,
                    ),
                )
            )
        stmt = stmt.order_by(Opportunity.created_at.desc(), Opportunity.id.desc()).limit(limit + 1)

        result = await self._session.execute(stmt)
        rows = list(result.scalars().unique().all())
        has_more = len(rows) > limit
        return rows[:limit], has_more

    async def get(self, opportunity_id: str) -> Opportunity | None:
        return await self._session.get(Opportunity, opportunity_id)

    async def search(self, query: str, limit: int) -> list[Opportunity]:
        """Full-text search over the maintained search_vector, ranked by
        relevance. Uses websearch_to_tsquery so natural queries (quotes, OR,
        -exclusions) work."""
        tsquery = func.websearch_to_tsquery("english", query)
        stmt = (
            select(Opportunity)
            .where(text("search_vector @@ websearch_to_tsquery('english', :q)"))
            .order_by(
                func.ts_rank(text("search_vector"), tsquery).desc(),
                Opportunity.created_at.desc(),
            )
            .limit(limit)
        ).params(q=query)
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())

    async def fetch_for_scoring(self, limit: int = 300) -> list[Opportunity]:
        """A recent pool of active opportunities to score for recommendations."""
        stmt = (
            select(Opportunity)
            .where(Opportunity.status == "active")
            .order_by(Opportunity.created_at.desc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().unique().all())
