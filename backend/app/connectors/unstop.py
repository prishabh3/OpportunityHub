from datetime import datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta

_API = "https://unstop.com/api/public/opportunity/search-result"


def _parse_dt(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def _extract_tags(item: dict[str, Any]) -> list[str]:
    tags: list[str] = []
    for entry in item.get("required_skills") or []:
        if isinstance(entry, str):
            tags.append(entry)
        elif isinstance(entry, dict):
            name = entry.get("name") or entry.get("title")
            if name:
                tags.append(str(name))
    return tags[:6]


class UnstopConnector(BaseConnector):
    meta = SourceMeta(
        key="unstop",
        display_name="Unstop",
        base_url="https://unstop.com",
        opportunity_types=["hackathon"],
    )

    def __init__(self, max_pages: int = 3, per_page: int = 30) -> None:
        self._max_pages = max_pages
        self._per_page = per_page

    async def fetch(self) -> list[NormalizedOpportunity]:
        items: list[NormalizedOpportunity] = []
        headers = {"User-Agent": "OpportunityHub/1.0 (+https://opportunityhub.dev)"}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            for page in range(1, self._max_pages + 1):
                resp = await client.get(
                    _API,
                    params={
                        "opportunity": "hackathons",
                        "per_page": str(self._per_page),
                        "page": str(page),
                    },
                )
                resp.raise_for_status()
                rows = (resp.json().get("data") or {}).get("data") or []
                if not rows:
                    break
                for row in rows:
                    parsed = self._normalize(row)
                    if parsed:
                        items.append(parsed)
        return items

    @staticmethod
    def _normalize(row: dict[str, Any]) -> NormalizedOpportunity | None:
        url = row.get("seo_url")
        if not url:
            public = row.get("public_url")
            url = f"https://unstop.com/{public}" if public else None
        if not url:
            return None

        region = (row.get("region") or "").lower()
        is_online = region == "online"
        regn = row.get("regnRequirements") or {}
        organisation = row.get("organisation") or {}

        return NormalizedOpportunity(
            external_id=str(row["id"]),
            type="hackathon",
            status="active" if row.get("regn_open") else "closed",
            title=row.get("title", "Untitled"),
            organizer=organisation.get("name") or "Unstop",
            location="Online" if is_online else (row.get("region") or None),
            country="Global" if is_online else "India",
            remote_type="remote" if is_online else "onsite",
            deadline_at=_parse_dt(regn.get("end_regn_dt")) or _parse_dt(row.get("end_date")),
            starts_at=_parse_dt(regn.get("start_regn_dt")),
            apply_url=url,
            source_url=url,
            banner_url=row.get("logoUrl2"),
            tags=_extract_tags(row),
            details={"subtype": row.get("subtype"), "registrations": row.get("registerCount")},
        )
