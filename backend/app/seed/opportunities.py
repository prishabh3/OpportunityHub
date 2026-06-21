"""Seed the database with a curated set of sample opportunities.

Run with:  python -m app.seed.opportunities

Idempotent: re-running only inserts opportunities whose (source, external_id)
pair is not already present.
"""

import asyncio
import hashlib
from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.opportunity import (
    Opportunity,
    OpportunityTag,
    Source,
    Tag,
)
from app.infrastructure.db.session import get_sessionmaker

SOURCE_KEY = "curated"


def _dt(year: int, month: int, day: int) -> datetime:
    return datetime(year, month, day, tzinfo=UTC)


# external_id, type, title, organizer, description, location, country,
# remote_type, difficulty, deadline, starts, apply_url, tags
SAMPLES: list[dict[str, Any]] = [
    {
        "external_id": "hack-mlh-global-2026",
        "type": "hackathon",
        "title": "MLH Global Hack Week: AI/ML",
        "organizer": "Major League Hacking",
        "description": "A week-long beginner-friendly hackathon focused on AI and ML projects, with workshops, mentorship, and prizes.",
        "location": "Online",
        "country": "Global",
        "remote_type": "remote",
        "difficulty": "beginner",
        "deadline_at": _dt(2026, 7, 20),
        "starts_at": _dt(2026, 7, 27),
        "apply_url": "https://mlh.io/seasons/2026/events",
        "tags": ["AI", "Machine Learning", "Beginner Friendly"],
    },
    {
        "external_id": "hack-devpost-genai-2026",
        "type": "hackathon",
        "title": "Generative AI World Hackathon",
        "organizer": "Devpost",
        "description": "Build innovative applications using the latest generative AI models. $50k in prizes across multiple tracks.",
        "location": "Online",
        "country": "Global",
        "remote_type": "remote",
        "difficulty": "intermediate",
        "deadline_at": _dt(2026, 8, 15),
        "starts_at": _dt(2026, 7, 1),
        "apply_url": "https://devpost.com/hackathons",
        "tags": ["Generative AI", "LLM", "Prizes"],
    },
    {
        "external_id": "hack-treehacks-2026",
        "type": "hackathon",
        "title": "TreeHacks 2026",
        "organizer": "Stanford University",
        "description": "Stanford's premier 36-hour hackathon bringing together 1,000+ students to build for social good.",
        "location": "Stanford, CA",
        "country": "USA",
        "remote_type": "onsite",
        "difficulty": "intermediate",
        "deadline_at": _dt(2026, 9, 30),
        "starts_at": _dt(2026, 11, 13),
        "apply_url": "https://www.treehacks.com/",
        "tags": ["University", "Social Good"],
    },
    {
        "external_id": "intern-google-step-2027",
        "type": "internship",
        "title": "STEP Software Engineering Intern, Summer 2027",
        "organizer": "Google",
        "description": "The STEP internship is for first- and second-year undergraduate students with a passion for technology.",
        "location": "Mountain View, CA",
        "country": "USA",
        "remote_type": "hybrid",
        "difficulty": "beginner",
        "deadline_at": _dt(2026, 10, 31),
        "starts_at": _dt(2027, 6, 1),
        "apply_url": "https://careers.google.com/students/",
        "tags": ["Software Engineering", "Undergraduate"],
    },
    {
        "external_id": "intern-stripe-2027",
        "type": "internship",
        "title": "Software Engineering Intern",
        "organizer": "Stripe",
        "description": "Work on real problems in payments infrastructure alongside experienced engineers.",
        "location": "Remote / Seattle",
        "country": "USA",
        "remote_type": "remote",
        "difficulty": "intermediate",
        "deadline_at": _dt(2026, 9, 15),
        "starts_at": _dt(2027, 5, 15),
        "apply_url": "https://stripe.com/jobs/university",
        "tags": ["Backend", "Payments"],
    },
    {
        "external_id": "intern-jane-street-2027",
        "type": "internship",
        "title": "Software Engineering Internship",
        "organizer": "Jane Street",
        "description": "Spend a summer working on challenging problems in a collaborative trading environment.",
        "location": "New York, NY",
        "country": "USA",
        "remote_type": "onsite",
        "difficulty": "advanced",
        "deadline_at": _dt(2026, 8, 1),
        "starts_at": _dt(2027, 6, 1),
        "apply_url": "https://www.janestreet.com/join-jane-street/",
        "tags": ["OCaml", "Quant", "Systems"],
    },
    {
        "external_id": "ft-anthropic-mts-2026",
        "type": "full_time_job",
        "title": "Member of Technical Staff, Product Engineering",
        "organizer": "Anthropic",
        "description": "Build products that make Claude useful and safe for millions of users.",
        "location": "San Francisco, CA",
        "country": "USA",
        "remote_type": "hybrid",
        "difficulty": "advanced",
        "deadline_at": None,
        "starts_at": None,
        "apply_url": "https://www.anthropic.com/careers",
        "tags": ["AI Safety", "Full Stack", "Python"],
    },
    {
        "external_id": "ft-netflix-swe-2026",
        "type": "full_time_job",
        "title": "Senior Software Engineer, Streaming",
        "organizer": "Netflix",
        "description": "Design and build the systems that stream to hundreds of millions of members worldwide.",
        "location": "Los Gatos, CA",
        "country": "USA",
        "remote_type": "remote",
        "difficulty": "advanced",
        "deadline_at": None,
        "starts_at": None,
        "apply_url": "https://jobs.netflix.com/",
        "tags": ["Distributed Systems", "Java"],
    },
    {
        "external_id": "ft-uber-newgrad-2026",
        "type": "full_time_job",
        "title": "Software Engineer, New Grad 2026",
        "organizer": "Uber",
        "description": "Join Uber as a new graduate engineer and work on systems that move the world.",
        "location": "Bengaluru",
        "country": "India",
        "remote_type": "hybrid",
        "difficulty": "intermediate",
        "deadline_at": _dt(2026, 7, 31),
        "starts_at": None,
        "apply_url": "https://www.uber.com/careers/",
        "tags": ["New Grad", "Go", "Microservices"],
    },
    {
        "external_id": "research-gsoc-2026",
        "type": "research_program",
        "title": "Google Summer of Code 2026",
        "organizer": "Google Open Source",
        "description": "A global program focused on bringing student developers into open source software development.",
        "location": "Online",
        "country": "Global",
        "remote_type": "remote",
        "difficulty": "intermediate",
        "deadline_at": _dt(2026, 7, 8),
        "starts_at": _dt(2026, 8, 1),
        "apply_url": "https://summerofcode.withgoogle.com/",
        "tags": ["Open Source", "Mentorship"],
    },
    {
        "external_id": "research-outreachy-2026",
        "type": "research_program",
        "title": "Outreachy Internship, December 2026 Cohort",
        "organizer": "Outreachy",
        "description": "Paid, remote internships in open source for people subject to underrepresentation in tech.",
        "location": "Online",
        "country": "Global",
        "remote_type": "remote",
        "difficulty": "beginner",
        "deadline_at": _dt(2026, 9, 1),
        "starts_at": _dt(2026, 12, 1),
        "apply_url": "https://www.outreachy.org/",
        "tags": ["Open Source", "Diversity", "Paid"],
    },
    {
        "external_id": "research-mitacs-2026",
        "type": "research_program",
        "title": "Mitacs Globalink Research Internship",
        "organizer": "Mitacs",
        "description": "A competitive initiative for international undergraduates to do research at Canadian universities.",
        "location": "Various",
        "country": "Canada",
        "remote_type": "onsite",
        "difficulty": "intermediate",
        "deadline_at": _dt(2026, 9, 21),
        "starts_at": _dt(2027, 5, 1),
        "apply_url": "https://www.mitacs.ca/our-programs/globalink-research-internship-students/",
        "tags": ["Research", "Undergraduate"],
    },
    {
        "external_id": "comp-kaggle-llm-2026",
        "type": "competition",
        "title": "Kaggle LLM Science Exam",
        "organizer": "Kaggle",
        "description": "Use LLMs to answer difficult science-based questions. Compete for prizes and a medal.",
        "location": "Online",
        "country": "Global",
        "remote_type": "remote",
        "difficulty": "advanced",
        "deadline_at": _dt(2026, 8, 30),
        "starts_at": _dt(2026, 6, 1),
        "apply_url": "https://www.kaggle.com/competitions",
        "tags": ["Data Science", "LLM", "Prizes"],
    },
    {
        "external_id": "comp-icpc-2026",
        "type": "competition",
        "title": "ICPC World Finals 2026",
        "organizer": "ICPC Foundation",
        "description": "The most prestigious algorithmic programming contest for university students worldwide.",
        "location": "TBD",
        "country": "Global",
        "remote_type": "onsite",
        "difficulty": "advanced",
        "deadline_at": _dt(2026, 10, 1),
        "starts_at": None,
        "apply_url": "https://icpc.global/",
        "tags": ["Competitive Programming", "Algorithms"],
    },
    {
        "external_id": "comp-meta-hackercup-2026",
        "type": "competition",
        "title": "Meta Hacker Cup 2026",
        "organizer": "Meta",
        "description": "Meta's annual open programming competition. Solve algorithmic puzzles to advance through rounds.",
        "location": "Online",
        "country": "Global",
        "remote_type": "remote",
        "difficulty": "advanced",
        "deadline_at": _dt(2026, 9, 5),
        "starts_at": _dt(2026, 9, 12),
        "apply_url": "https://www.facebook.com/codingcompetitions/hacker-cup",
        "tags": ["Competitive Programming", "Algorithms"],
    },
]


def _content_hash(item: dict[str, Any]) -> str:
    raw = f"{item['title']}|{item['organizer']}|{item['apply_url']}"
    return hashlib.sha256(raw.encode()).hexdigest()


async def _get_or_create_source(session: AsyncSession) -> Source:
    result = await session.execute(select(Source).where(Source.key == SOURCE_KEY))
    source = result.scalar_one_or_none()
    if source is None:
        source = Source(
            key=SOURCE_KEY,
            display_name="Curated",
            base_url="https://opportunityhub.dev",
            opportunity_types=[
                "hackathon",
                "internship",
                "full_time_job",
                "research_program",
                "competition",
            ],
        )
        session.add(source)
        await session.flush()
    return source


async def _get_or_create_tag(session: AsyncSession, name: str) -> Tag:
    result = await session.execute(select(Tag).where(Tag.name == name))
    tag = result.scalar_one_or_none()
    if tag is None:
        tag = Tag(name=name)
        session.add(tag)
        await session.flush()
    return tag


async def seed() -> None:
    sessionmaker = get_sessionmaker()
    async with sessionmaker() as session:
        source = await _get_or_create_source(session)

        existing = await session.execute(
            select(Opportunity.external_id).where(Opportunity.source_id == source.id)
        )
        existing_ids = set(existing.scalars().all())

        created = 0
        for item in SAMPLES:
            if item["external_id"] in existing_ids:
                continue

            opportunity = Opportunity(
                source_id=source.id,
                external_id=item["external_id"],
                type=item["type"],
                status="active",
                title=item["title"],
                organizer=item["organizer"],
                description=item["description"],
                location=item["location"],
                country=item["country"],
                remote_type=item["remote_type"],
                difficulty=item["difficulty"],
                deadline_at=item["deadline_at"],
                starts_at=item["starts_at"],
                apply_url=item["apply_url"],
                source_url=item["apply_url"],
                content_hash=_content_hash(item),
            )
            session.add(opportunity)
            await session.flush()

            for tag_name in item["tags"]:
                tag = await _get_or_create_tag(session, tag_name)
                session.add(OpportunityTag(opportunity_id=opportunity.id, tag_id=tag.id))
            created += 1

        await session.commit()
        print(f"Seed complete: {created} new opportunities ({len(existing_ids)} already present).")


if __name__ == "__main__":
    asyncio.run(seed())
