from typing import Any

import httpx

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta
from app.connectors.jobs_common import (
    TECH_RE,
    classify_experience,
    extract_skill_tags,
    infer_country,
)

# Verified public Lever boards. Others are skipped if they don't return a list.
COMPANIES: list[str] = [
    "spotify",
    "mistral",
    "palantir",
    "plaid",
    "notion",
    "cohere",
    # Indian company boards
    "cred",
    "meesho",
]

_API = "https://api.lever.co/v0/postings/{company}?mode=json"
_PER_COMPANY = 20

_WORKPLACE = {"remote": "remote", "hybrid": "hybrid", "on-site": "onsite", "onsite": "onsite"}


class LeverConnector(BaseConnector):
    meta = SourceMeta(
        key="lever",
        display_name="Company Job Boards (Lever)",
        base_url="https://jobs.lever.co",
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
                    resp = await client.get(_API.format(company=company))
                    resp.raise_for_status()
                    postings = resp.json()
                except (httpx.HTTPError, ValueError):
                    continue
                if not isinstance(postings, list):
                    continue  # error/dict response — skip this board

                count = 0
                for job in postings:
                    if count >= _PER_COMPANY:
                        break
                    if not isinstance(job, dict) or not TECH_RE.search(job.get("text", "")):
                        continue
                    parsed = self._normalize(company, job)
                    if parsed:
                        items.append(parsed)
                        count += 1
        return items

    @staticmethod
    def _normalize(company: str, job: dict[str, Any]) -> NormalizedOpportunity | None:
        url = job.get("hostedUrl") or job.get("applyUrl")
        if not url or not job.get("id"):
            return None
        title = job.get("text", "Role")
        categories = job.get("categories") or {}
        location = categories.get("location")
        commitment = (categories.get("commitment") or "").lower()
        workplace = (job.get("workplaceType") or "").lower()
        remote_type = _WORKPLACE.get(workplace, "unspecified")

        experience = classify_experience(title)
        if "intern" in commitment:
            experience = "intern"
        opp_type = "internship" if experience == "intern" else "full_time_job"

        return NormalizedOpportunity(
            external_id=f"{company}-{job['id']}",
            type=opp_type,
            status="active",
            title=title,
            organizer=company.replace("-", " ").title(),
            location=location,
            country=infer_country(location)
            or ("Global" if remote_type == "remote" else (job.get("country") or None)),
            remote_type=remote_type,
            experience_level=experience,
            apply_url=url,
            source_url=url,
            tags=extract_skill_tags(title),
        )
