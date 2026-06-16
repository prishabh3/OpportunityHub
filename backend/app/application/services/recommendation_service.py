from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.recommendation import RecommendedOpportunity
from app.application.services.opportunity_service import OpportunityService
from app.application.services.profile_service import ProfileService
from app.core.security import AuthenticatedUser
from app.infrastructure.db.models.opportunity import Opportunity
from app.infrastructure.db.repositories.opportunity_repository import OpportunityRepository

# Score weights (sum to 100).
SKILL_WEIGHT = 60
COUNTRY_WEIGHT = 20
REMOTE_WEIGHT = 20
SKILL_CAP = 5  # matched skills beyond this don't add more


class RecommendationService:
    """Heuristic, no-LLM recommendations: rank opportunities by how well their
    tags/location match the user's profile (skills, countries, work preference).
    The semantic/embedding-based version comes once AI features are enabled."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._opportunities = OpportunityRepository(session)

    async def recommend(self, user: AuthenticatedUser, limit: int) -> list[RecommendedOpportunity]:
        profile = await ProfileService(self._session).get_or_create(user)

        user_skills = {s.lower() for s in profile.skills}
        pref_countries = {c.lower() for c in profile.preferred_countries}
        pref_remote = profile.preferred_remote

        candidates = await self._opportunities.fetch_for_scoring()

        scored: list[tuple[float, list[str], Opportunity]] = []
        for opp in candidates:
            matched_skills = [t.name for t in opp.tags if t.name.lower() in user_skills]

            skill_score = (
                min(len(matched_skills), SKILL_CAP) / SKILL_CAP * SKILL_WEIGHT
                if user_skills
                else 0.0
            )
            country_score = (
                COUNTRY_WEIGHT if opp.country and opp.country.lower() in pref_countries else 0
            )
            remote_score = (
                REMOTE_WEIGHT
                if pref_remote and pref_remote != "unspecified" and opp.remote_type == pref_remote
                else 0
            )
            score = round(skill_score + country_score + remote_score, 1)
            scored.append((score, matched_skills, opp))

        # Highest score first; recent opportunities break ties (pool is already
        # ordered by created_at desc, so a stable sort preserves that).
        scored.sort(key=lambda row: row[0], reverse=True)

        return [
            RecommendedOpportunity(
                **OpportunityService._to_summary(opp).model_dump(),
                match_score=score,
                matched_skills=matched_skills,
            )
            for score, matched_skills, opp in scored[:limit]
        ]
