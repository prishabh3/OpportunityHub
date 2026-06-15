from sqlalchemy import delete, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.db.models.profile import Profile, Skill, UserSkill


class ProfileRepository:
    """Data access for profiles and their skills."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, user_id: str) -> Profile | None:
        return await self._session.get(Profile, user_id)

    async def ensure_auth_user(self, user_id: str, email: str | None) -> None:
        """Dev-only: insert a stub ``auth.users`` row so the ``profiles`` FK is
        satisfied locally. In production the backend points at Supabase's
        database, where ``auth.users`` is managed and this is a no-op path
        (guarded by the caller)."""
        await self._session.execute(
            text(
                "insert into auth.users (id, email) values (:id, :email) "
                "on conflict (id) do nothing"
            ),
            {"id": user_id, "email": email},
        )

    async def create(self, user_id: str) -> Profile:
        profile = Profile(id=user_id)
        self._session.add(profile)
        await self._session.flush()
        await self._session.refresh(profile)
        return profile

    async def get_skill_names(self, user_id: str) -> list[str]:
        result = await self._session.execute(
            select(Skill.name)
            .join(UserSkill, UserSkill.skill_id == Skill.id)
            .where(UserSkill.user_id == user_id)
            .order_by(Skill.name)
        )
        return list(result.scalars().all())

    async def set_skills(self, user_id: str, names: list[str]) -> None:
        """Replace the user's skills with the given names, creating skill rows
        as needed."""
        await self._session.execute(delete(UserSkill).where(UserSkill.user_id == user_id))

        cleaned = sorted({name.strip() for name in names if name.strip()})
        for name in cleaned:
            existing = await self._session.execute(select(Skill).where(Skill.name == name))
            skill = existing.scalar_one_or_none()
            if skill is None:
                skill = Skill(name=name)
                self._session.add(skill)
                await self._session.flush()
            self._session.add(UserSkill(user_id=user_id, skill_id=skill.id))
