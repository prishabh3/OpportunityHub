from datetime import datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta
from app.connectors.jobs_common import classify_experience

_API = "https://unstop.com/api/public/opportunity/search-result"

# (api param, opportunity type, default experience or "" to classify, pages)
# Unstop is India-centric, so this surfaces Indian internships and fresher jobs.
_KINDS: list[tuple[str, str, str, int]] = [
    ("hackathons", "hackathon", "unspecified", 3),
    ("internships", "internship", "intern", 4),
    ("jobs", "full_time_job", "", 4),
]


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
        display_name="Unstop (India)",
        base_url="https://unstop.com",
        opportunity_types=["hackathon", "internship", "full_time_job"],
    )

    def __init__(self, per_page: int = 30) -> None:
        self._per_page = per_page

    async def fetch(self) -> list[NormalizedOpportunity]:
        items: list[NormalizedOpportunity] = []
        headers = {"User-Agent": "OpportunityHub/1.0 (+https://opportunityhub.dev)"}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            for api_param, opp_type, default_exp, pages in _KINDS:
                for page in range(1, pages + 1):
                    try:
                        resp = await client.get(
                            _API,
                            params={
                                "opportunity": api_param,
                                "per_page": str(self._per_page),
                                "page": str(page),
                            },
                        )
                        resp.raise_for_status()
                        rows = (resp.json().get("data") or {}).get("data") or []
                    except (httpx.HTTPError, ValueError):
                        break
                    if not rows:
                        break
                    for row in rows:
                        parsed = self._normalize(row, opp_type, default_exp)
                        if parsed:
                            items.append(parsed)
        return items

    @staticmethod
    def _normalize(
        row: dict[str, Any], opp_type: str, default_exp: str
    ) -> NormalizedOpportunity | None:
        url = row.get("seo_url")
        if not url:
            public = row.get("public_url")
            url = f"https://unstop.com/{public}" if public else None
        if not url:
            return None

        title = row.get("title", "Untitled")
        region = (row.get("region") or "").lower()
        is_online = region == "online"
        regn = row.get("regnRequirements") or {}
        organisation = row.get("organisation") or {}
        experience = default_exp if default_exp else classify_experience(title)

        return NormalizedOpportunity(
            external_id=str(row["id"]),  # Unstop ids are globally unique across types
            type=opp_type,
            status="active" if row.get("regn_open") else "closed",
            title=title,
            organizer=organisation.get("name") or "Unstop",
            location="Online" if is_online else (row.get("region") or None),
            country="India",  # Unstop is India-centric (online roles still target Indian students)
            remote_type="remote" if is_online else "onsite",
            experience_level=experience,
            deadline_at=_parse_dt(regn.get("end_regn_dt")) or _parse_dt(row.get("end_date")),
            starts_at=_parse_dt(regn.get("start_regn_dt")),
            apply_url=url,
            source_url=url,
            banner_url=row.get("logoUrl2"),
            tags=_extract_tags(row),
            details={"subtype": row.get("subtype"), "registrations": row.get("registerCount")},
        )
