import re
from datetime import UTC, datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta

_API = "https://devpost.com/api/hackathons"
_STATUS_MAP = {"open": "active", "upcoming": "upcoming", "ended": "closed"}


def _parse_end_date(dates: str | None) -> datetime | None:
    """Devpost submission_period_dates looks like 'May 19 - Aug 17, 2026'.
    Parse the end (the part with the year) as the deadline."""
    if not dates:
        return None
    end = dates.split(" - ")[-1].strip()
    match = re.search(r"([A-Za-z]{3,9})\s+(\d{1,2}),?\s+(\d{4})", end)
    if not match:
        return None
    for fmt in ("%b %d %Y", "%B %d %Y"):
        try:
            month, day, year = match.groups()
            return datetime.strptime(f"{month} {day} {year}", fmt).replace(tzinfo=UTC)
        except ValueError:
            continue
    return None


class DevpostConnector(BaseConnector):
    meta = SourceMeta(
        key="devpost",
        display_name="Devpost",
        base_url="https://devpost.com",
        opportunity_types=["hackathon"],
    )

    def __init__(self, max_pages: int = 6) -> None:
        self._max_pages = max_pages

    async def fetch(self) -> list[NormalizedOpportunity]:
        items: list[NormalizedOpportunity] = []
        headers = {"User-Agent": "OpportunityHub/1.0 (+https://opportunityhub.dev)"}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            for page in range(1, self._max_pages + 1):
                params: list[tuple[str, str | int | float | bool | None]] = [
                    ("status[]", "open"),
                    ("status[]", "upcoming"),
                    ("page", str(page)),
                ]
                resp = await client.get(_API, params=params)
                resp.raise_for_status()
                hackathons = resp.json().get("hackathons", [])
                if not hackathons:
                    break
                for h in hackathons:
                    parsed = self._normalize(h)
                    if parsed:
                        items.append(parsed)
        return items

    @staticmethod
    def _normalize(h: dict[str, Any]) -> NormalizedOpportunity | None:
        url = h.get("url")
        if not url:
            return None
        location = (h.get("displayed_location") or {}).get("location")
        is_online = bool(location and "online" in location.lower())
        banner = h.get("thumbnail_url")
        if banner and banner.startswith("//"):
            banner = f"https:{banner}"

        return NormalizedOpportunity(
            external_id=str(h["id"]),
            type="hackathon",
            status=_STATUS_MAP.get(h.get("open_state", ""), "active"),
            title=h.get("title", "Untitled hackathon"),
            organizer=h.get("organization_name") or "Devpost",
            location=location,
            country="Global" if is_online else None,
            remote_type="remote" if is_online else "onsite",
            deadline_at=_parse_end_date(h.get("submission_period_dates")),
            apply_url=url,
            source_url=url,
            banner_url=banner,
            tags=[t["name"] for t in h.get("themes", []) if t.get("name")],
            details={
                "registrations": h.get("registrations_count"),
                "submission_period": h.get("submission_period_dates"),
            },
        )
