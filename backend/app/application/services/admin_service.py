from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.admin import AdminAnalytics, ConnectorRunRead, SourceStat
from app.infrastructure.db.models.bookmark import Bookmark
from app.infrastructure.db.models.connector_run import ConnectorRun
from app.infrastructure.db.models.notification import Notification
from app.infrastructure.db.models.opportunity import Opportunity, Source
from app.infrastructure.db.models.profile import Profile


class AdminService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _count(self, model: type) -> int:
        result = await self._session.execute(select(func.count()).select_from(model))
        return int(result.scalar_one())

    async def analytics(self) -> AdminAnalytics:
        by_type_rows = await self._session.execute(
            select(Opportunity.type, func.count()).group_by(Opportunity.type)
        )
        return AdminAnalytics(
            opportunities_total=await self._count(Opportunity),
            by_type={t: n for t, n in by_type_rows.all()},
            users_total=await self._count(Profile),
            bookmarks_total=await self._count(Bookmark),
            notifications_total=await self._count(Notification),
        )

    async def sources(self) -> list[SourceStat]:
        rows = await self._session.execute(
            select(Source.key, Source.display_name, func.count(Opportunity.id))
            .outerjoin(Opportunity, Opportunity.source_id == Source.id)
            .group_by(Source.id)
            .order_by(func.count(Opportunity.id).desc())
        )
        return [
            SourceStat(key=key, display_name=name, opportunity_count=count)
            for key, name, count in rows.all()
        ]

    async def recent_runs(self, limit: int = 20) -> list[ConnectorRunRead]:
        rows = await self._session.execute(
            select(ConnectorRun, Source.key)
            .join(Source, Source.id == ConnectorRun.source_id)
            .order_by(ConnectorRun.started_at.desc())
            .limit(limit)
        )
        return [
            ConnectorRunRead(
                id=run.id,
                source_key=key,
                status=run.status,
                started_at=run.started_at,
                finished_at=run.finished_at,
                items_found=run.items_found,
                items_created=run.items_created,
                items_updated=run.items_updated,
                items_failed=run.items_failed,
                error_message=run.error_message,
            )
            for run, key in rows.all()
        ]
