from datetime import UTC, datetime

from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta
from app.core.logging import get_logger
from app.infrastructure.db.models.connector_run import ConnectorRun
from app.infrastructure.db.models.opportunity import (
    Opportunity,
    OpportunityTag,
    Source,
    Tag,
)

logger = get_logger(__name__)


class RunStats(BaseModel):
    source: str
    found: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    failed: int = 0
    error: str | None = None


async def _ensure_source(session: AsyncSession, meta: SourceMeta) -> Source:
    result = await session.execute(select(Source).where(Source.key == meta.key))
    source = result.scalar_one_or_none()
    if source is None:
        source = Source(
            key=meta.key,
            display_name=meta.display_name,
            base_url=meta.base_url,
            opportunity_types=list(meta.opportunity_types),
        )
        session.add(source)
        await session.flush()
    return source


async def _get_or_create_tag(session: AsyncSession, name: str, cache: dict[str, Tag]) -> Tag:
    key = name.lower()
    if key in cache:
        return cache[key]
    result = await session.execute(select(Tag).where(Tag.name == name))
    tag = result.scalar_one_or_none()
    if tag is None:
        tag = Tag(name=name)
        session.add(tag)
        await session.flush()
    cache[key] = tag
    return tag


async def _apply_fields(opp: Opportunity, item: NormalizedOpportunity, content_hash: str) -> None:
    opp.type = item.type
    opp.status = item.status
    opp.title = item.title
    opp.organizer = item.organizer
    opp.description = item.description
    opp.banner_url = item.banner_url
    opp.location = item.location
    opp.country = item.country
    opp.remote_type = item.remote_type
    opp.difficulty = item.difficulty
    opp.deadline_at = item.deadline_at
    opp.starts_at = item.starts_at
    opp.ends_at = item.ends_at
    opp.apply_url = item.apply_url
    opp.source_url = item.source_url
    opp.details = item.details
    opp.content_hash = content_hash


async def _sync_tags(
    session: AsyncSession, opp: Opportunity, names: list[str], cache: dict[str, Tag]
) -> None:
    await session.execute(
        delete(OpportunityTag).where(OpportunityTag.opportunity_id == opp.id)
    )
    seen: set[str] = set()
    for name in names:
        clean = name.strip()
        if not clean or clean.lower() in seen:
            continue
        seen.add(clean.lower())
        tag = await _get_or_create_tag(session, clean, cache)
        session.add(OpportunityTag(opportunity_id=opp.id, tag_id=tag.id))


async def run_connector(session: AsyncSession, connector: BaseConnector) -> RunStats:
    """Fetch from a connector and upsert results, logging a connector_run row."""
    source = await _ensure_source(session, connector.meta)
    run = ConnectorRun(source_id=source.id, status="running")
    session.add(run)
    await session.flush()

    stats = RunStats(source=connector.meta.key)
    tag_cache: dict[str, Tag] = {}

    try:
        items = await connector.fetch()
    except Exception as exc:  # noqa: BLE001 - record and surface connector failures
        logger.warning("connector_fetch_failed", source=connector.meta.key, error=repr(exc))
        run.status = "failed"
        run.error_message = repr(exc)[:1000]
        run.finished_at = datetime.now(UTC)
        await session.commit()
        stats.error = repr(exc)
        return stats

    stats.found = len(items)

    existing_result = await session.execute(
        select(Opportunity).where(Opportunity.source_id == source.id)
    )
    by_external = {o.external_id: o for o in existing_result.scalars().unique().all()}

    for item in items:
        if not item.is_valid():
            stats.failed += 1
            continue
        content_hash = item.content_hash()
        existing = by_external.get(item.external_id)
        if existing is None:
            opp = Opportunity(source_id=source.id, external_id=item.external_id)
            await _apply_fields(opp, item, content_hash)
            session.add(opp)
            await session.flush()
            await _sync_tags(session, opp, item.tags, tag_cache)
            stats.created += 1
        elif existing.content_hash != content_hash:
            await _apply_fields(existing, item, content_hash)
            await _sync_tags(session, existing, item.tags, tag_cache)
            stats.updated += 1
        else:
            stats.skipped += 1

    run.status = "success" if stats.failed == 0 else "partial"
    run.items_found = stats.found
    run.items_created = stats.created
    run.items_updated = stats.updated
    run.items_failed = stats.failed
    run.finished_at = datetime.now(UTC)

    await session.commit()
    logger.info("connector_run_complete", **stats.model_dump())
    return stats
