"""Shared helpers for job connectors (Greenhouse, Lever): experience-level
classification and skill-tag extraction from a job title."""

import re

# Only ingest tech-relevant roles (the product's audience).
TECH_RE = re.compile(
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


def extract_skill_tags(title: str) -> list[str]:
    return [kw for kw in _SKILL_KEYWORDS if kw.lower() in title.lower()][:5]


_INDIA_KEYWORDS = (
    "india", "bengaluru", "bangalore", "mumbai", "delhi", "hyderabad", "pune",
    "chennai", "gurgaon", "gurugram", "noida", "kolkata", "ahmedabad",
)


def infer_country(location: str | None) -> str | None:
    """Best-effort country from a free-text job location, so India-based roles
    (from any company board) are tagged for Indian students."""
    if not location:
        return None
    loc = location.lower()
    if any(k in loc for k in _INDIA_KEYWORDS):
        return "India"
    if "remote" in loc or "anywhere" in loc:
        return "Global"
    return None
