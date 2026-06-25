"""User profile repository for database access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import UserProfile


class UserProfileRepository:
    """User profile repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, user_id: int) -> UserProfile | None:
        """获取用户画像."""
        result = await self.db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_profile(
        self,
        user_id: int,
        department: str | None = None,
        common_topics: dict | None = None,
        preferences: dict | None = None,
    ) -> UserProfile:
        """创建用户画像."""
        profile = UserProfile(
            user_id=user_id,
            department=department,
            common_topics=common_topics or {},
            preferences=preferences or {},
        )
        self.db.add(profile)
        await self.db.flush()
        await self.db.refresh(profile)
        return profile

    async def update_profile(
        self,
        user_id: int,
        department: str | None = None,
        common_topics: dict | None = None,
        preferences: dict | None = None,
    ) -> UserProfile | None:
        """更新用户画像，不存在则创建."""
        profile = await self.get_profile(user_id)
        if profile is None:
            return await self.create_profile(
                user_id=user_id,
                department=department,
                common_topics=common_topics,
                preferences=preferences,
            )

        if department is not None:
            profile.department = department
        if common_topics is not None:
            profile.common_topics = common_topics
        if preferences is not None:
            profile.preferences = preferences

        await self.db.flush()
        await self.db.refresh(profile)
        return profile
