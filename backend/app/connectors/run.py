"""CLI to run connectors locally:  python -m app.connectors.run [connector_key]"""

import asyncio
import sys

from app.connectors.service import run_all
from app.infrastructure.db.session import get_sessionmaker


async def _main(only: str | None) -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        results = await run_all(session, only)
    for r in results:
        print(
            f"[{r.source}] found={r.found} created={r.created} updated={r.updated} "
            f"skipped={r.skipped} failed={r.failed}" + (f" error={r.error}" if r.error else "")
        )


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(_main(only))
