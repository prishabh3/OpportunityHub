import re
from datetime import datetime
from typing import Any

import httpx

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta

# Companies with public Greenhouse job boards. Unknown/blocked ones are skipped.
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
]

_BOARD = "https://boards-api.greenhouse.io/v1/boards/{company}/jobs"
_PER_COMPANY = 30

# Only ingest tech-relevant roles (the product's audience).
_TECH = re.compile(
    r"engineer|developer|software|\bdata\b|machine learning|\bml\b|\bai\b|scientist|intern|"
    r"frontend|front-end|backend|back-end|full[\s-]?stack|devops|\bsre\b|security|mobile|"
    r"\bios\b|android|\bweb\b|cloud|infrastructure|platform|\bqa\b|analyst|research",
    re.IGNORECASE,
)

_SKILL_KEYWORDS = [
    "Python", "Java", "JavaScript", "TypeScript", "Go", "Rust", "C++", "React",
    "Machine Learning", "AI", "Data", "Backend", "Frontend", "Full Stack", "DevOps",
    "Security", "Cloud", "Mobile", "iOS", "Android", "Infrastructure", "Platform",
]


def classify_experience(title: str) -> str:
    t = title.lower()
    if re.search(r"\bintern(ship)?\b", t):
        return "intern"
    # Seniority signals take precedence (e.g. "Associate Manager" is senior).
    if re.search(
        r"senior|\bsr\b|staff|principal|\blead\b|director|head of|\bvp\b|manager|architect", t
    ):
        return "senior"
    if re.search(
        r"new[\s-]?grad|graduate|entry[\s-]?level|\bjunior\b|\bjr\b|associate|early career|"
        r"campus|apprentice|fresher|university",
        t,
    ):
        return "fresher"
    return "mid"


def _extract_tags(title: str) -> list[str]:
    return [kw for kw in _SKILL_KEYWORDS if kw.lower() in title.lower()][:5]


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
                    if not _TECH.search(title):
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
            country="Global" if is_remote else None,
            remote_type="remote" if is_remote else "onsite",
            experience_level=experience,
            deadline_at=_parse_deadline(job.get("application_deadline")),
            apply_url=url,
            source_url=url,
            tags=_extract_tags(title),
        )
