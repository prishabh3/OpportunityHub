from sqlalchemy.ext.asyncio import AsyncSession

from app.application.dtos.profile import ProfileRead, ProfileUpdate
from app.core.config import get_settings
from app.core.security import AuthenticatedUser
from app.infrastructure.db.models.profile import Profile
from app.infrastructure.db.repositories.profile_repository import ProfileRepository


class ProfileService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._repo = ProfileRepository(session)

    async def get_or_create(self, user: AuthenticatedUser) -> ProfileRead:
        profile = await self._repo.get(user.id)
        if profile is None:
            if get_settings().environment == "development":
                await self._repo.ensure_auth_user(user.id, user.email)
            profile = await self._repo.create(user.id)
            await self._session.commit()
        skills = await self._repo.get_skill_names(user.id)
        return self._to_read(profile, skills)

    async def update(self, user: AuthenticatedUser, data: ProfileUpdate) -> ProfileRead:
        await self.get_or_create(user)  # ensure the row exists
        profile = await self._repo.get(user.id)
        assert profile is not None  # just ensured above

        changes = data.model_dump(exclude_unset=True)
        skills = changes.pop("skills", None)

        for field, value in changes.items():
            setattr(profile, field, value)

        if skills is not None:
            await self._repo.set_skills(user.id, skills)

        await self._session.commit()
        await self._session.refresh(profile)

        skill_names = await self._repo.get_skill_names(user.id)
        return self._to_read(profile, skill_names)

    @staticmethod
    def _to_read(profile: Profile, skills: list[str]) -> ProfileRead:
        return ProfileRead(
            id=profile.id,
            full_name=profile.full_name,
            preferred_role=profile.preferred_role,
            preferred_companies=profile.preferred_companies or [],
            preferred_countries=profile.preferred_countries or [],
            preferred_remote=profile.preferred_remote,
            expected_graduation=profile.expected_graduation,
            weekly_digest_enabled=profile.weekly_digest_enabled,
            timezone=profile.timezone,
            skills=skills,
        )
