from datetime import datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta
from app.connectors.jobs_common import (
    TECH_RE,
    classify_experience,
    extract_skill_tags,
    infer_country,
)

# Verified public Greenhouse job boards. Unknown/blocked ones are skipped at runtime.
COMPANIES: list[str] = [
    "stripe",
    "databricks",
    "gitlab",
    "figma",
    "anthropic",
    "discord",
    "reddit",
    "coinbase",
    "robinhood",
    "ramp",
    "airbnb",
    "dropbox",
    "asana",
    "instacart",
    "lyft",
    "pinterest",
    "twitch",
    "datadog",
    "mongodb",
    "elastic",
    "twilio",
    "affirm",
    "brex",
    "gusto",
    "samsara",
    "faire",
    "chime",
    "nuro",
    "waymo",
    # Indian company boards
    "postman",
    "phonepe",
]

_BOARD = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
_PER_COMPANY = 20


def _parse_deadline(value: Any) -> datetime | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


class GreenhouseConnector(BaseConnector):
    meta = SourceMeta(
        key="greenhouse",
        display_name="Company Job Boards",
        base_url="https://boards-api.greenhouse.io",
        opportunity_types=["full_time_job", "internship"],
    )

    def __init__(self, companies: list[str] | None = None) -> None:
        self._companies = companies or COMPANIES

    async def fetch(self) -> list[NormalizedOpportunity]:
        items: list[NormalizedOpportunity] = []
        headers = {"User-Agent": "OpportunityHub/1.0 (+https://opportunityhub.dev)"}
        async with httpx.AsyncClient(timeout=20, headers=headers) as client:
            for company in self._companies:
                try:
                    resp = await client.get(_BOARD.format(company=company))
                    resp.raise_for_status()
                    jobs = resp.json().get("jobs", [])
                except (httpx.HTTPError, ValueError):
                    continue  # skip companies whose board is missing/blocked

                count = 0
                for job in jobs:
                    if count >= _PER_COMPANY:
                        break
                    title = job.get("title", "")
                    if not TECH_RE.search(title):
                        continue
                    parsed = self._normalize(company, job)
                    if parsed:
                        items.append(parsed)
                        count += 1
        return items

    @staticmethod
    def _normalize(company: str, job: dict[str, Any]) -> NormalizedOpportunity | None:
        url = job.get("absolute_url")
        if not url or not job.get("id"):
            return None
        title = job.get("title", "Role")
        location = (job.get("location") or {}).get("name")
        is_remote = bool(location and "remote" in location.lower())
        experience = classify_experience(title)
        opp_type = "internship" if experience == "intern" else "full_time_job"

        return NormalizedOpportunity(
            external_id=f"{company}-{job['id']}",
            type=opp_type,
            status="active",
            title=title,
            organizer=job.get("company_name") or company.replace("-", " ").title(),
            location=location,
            country=infer_country(location) or ("Global" if is_remote else None),
            remote_type="remote" if is_remote else "onsite",
            experience_level=experience,
            deadline_at=_parse_deadline(job.get("application_deadline")),
            apply_url=url,
            source_url=url,
            tags=extract_skill_tags(title),
        )
