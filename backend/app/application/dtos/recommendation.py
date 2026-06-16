from pydantic import Field

from app.application.dtos.opportunity import OpportunitySummary


class RecommendedOpportunity(OpportunitySummary):
    match_score: float
    matched_skills: list[str] = Field(default_factory=list)
