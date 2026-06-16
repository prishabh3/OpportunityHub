"""Curated, real early-career programs (internships / new-grad) so the
Fresher and Intern experience filters reflect genuine high-value opportunities.
Ingested through the standard pipeline (idempotent upsert)."""

from typing import Any

from app.connectors.base import BaseConnector, NormalizedOpportunity, SourceMeta

_PROGRAMS: list[dict[str, Any]] = [
    {
        "external_id": "microsoft-explore",
        "title": "Microsoft Explore Internship",
        "organizer": "Microsoft",
        "description": "A 12-week summer internship for first- and second-year students to explore software engineering and product management.",
        "experience_level": "intern",
        "apply_url": "https://careers.microsoft.com/students/us/en/usexploreprogram",
        "tags": ["Software Engineering", "Internship", "Undergraduate"],
    },
    {
        "external_id": "meta-university-engineering",
        "title": "Meta University Engineering Internship",
        "organizer": "Meta",
        "description": "A hands-on internship for students from communities underrepresented in tech, early in their CS journey.",
        "experience_level": "intern",
        "apply_url": "https://www.metacareers.com/careerprograms/students/",
        "tags": ["Software Engineering", "Internship", "Diversity"],
    },
    {
        "external_id": "amazon-future-engineer",
        "title": "Amazon Future Engineer Internship",
        "organizer": "Amazon",
        "description": "Internships and scholarships for students pursuing computer science, with mentorship at Amazon.",
        "experience_level": "intern",
        "apply_url": "https://www.amazonfutureengineer.com/",
        "tags": ["Software Engineering", "Internship"],
    },
    {
        "external_id": "tesla-start",
        "title": "Tesla START Program",
        "organizer": "Tesla",
        "description": "An intensive, hands-on training program transitioning students into full-time roles at Tesla.",
        "experience_level": "fresher",
        "apply_url": "https://www.tesla.com/careers/university",
        "tags": ["Engineering", "New Grad"],
    },
    {
        "external_id": "bloomberg-swe-intern",
        "title": "Bloomberg Software Engineering Internship",
        "organizer": "Bloomberg",
        "description": "Summer internship building products on Bloomberg's financial technology platform.",
        "experience_level": "intern",
        "apply_url": "https://careers.bloomberg.com/",
        "tags": ["Software Engineering", "Internship", "Finance"],
    },
    {
        "external_id": "goldman-engineering-analyst",
        "title": "Goldman Sachs Engineering New Analyst",
        "organizer": "Goldman Sachs",
        "description": "Entry-level analyst program for new graduates joining Goldman Sachs Engineering.",
        "experience_level": "fresher",
        "apply_url": "https://www.goldmansachs.com/careers/students/",
        "tags": ["Software Engineering", "New Grad", "Finance"],
    },
    {
        "external_id": "salesforce-futureforce",
        "title": "Salesforce Futureforce Internship",
        "organizer": "Salesforce",
        "description": "Internships across engineering and product for students, with mentorship and full-time conversion.",
        "experience_level": "intern",
        "apply_url": "https://www.salesforce.com/company/careers/university-recruiting/",
        "tags": ["Software Engineering", "Internship", "Cloud"],
    },
    {
        "external_id": "jpmc-software-engineer-program",
        "title": "JPMorgan Chase Software Engineer Program (New Grad)",
        "organizer": "JPMorgan Chase",
        "description": "A two-year rotational program for new-graduate software engineers.",
        "experience_level": "fresher",
        "apply_url": "https://careers.jpmorgan.com/us/en/students/programs",
        "tags": ["Software Engineering", "New Grad", "Finance"],
    },
]


class CuratedEarlyCareerConnector(BaseConnector):
    meta = SourceMeta(
        key="early-career",
        display_name="Early-Career Programs",
        base_url="https://opportunityhub.dev",
        opportunity_types=["internship"],
    )

    async def fetch(self) -> list[NormalizedOpportunity]:
        return [
            NormalizedOpportunity(
                external_id=p["external_id"],
                type="internship",
                status="active",
                title=p["title"],
                organizer=p["organizer"],
                description=p["description"],
                country="Global",
                remote_type="onsite",
                experience_level=p["experience_level"],
                apply_url=p["apply_url"],
                source_url=p["apply_url"],
                tags=p["tags"],
            )
            for p in _PROGRAMS
        ]
