from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.pipeline import RunStats, run_connector
from app.connectors.registry import CONNECTOR_REGISTRY, build_connector


async def run_all(session: AsyncSession, only: str | None = None) -> list[RunStats]:
    """Run one connector (if `only` given) or all registered connectors.

    Each connector runs in its own try/commit so one failing source doesn't
    abort the others.
    """
    keys = [only] if only else list(CONNECTOR_REGISTRY)
    results: list[RunStats] = []
    for key in keys:
        if key not in CONNECTOR_REGISTRY:
            results.append(RunStats(source=key, error="unknown connector"))
            continue
        results.append(await run_connector(session, build_connector(key)))
    return results
