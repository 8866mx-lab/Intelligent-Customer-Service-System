"""Memory service for managing user short-term and long-term memory."""

from pycore.core import get_logger
from src.repositories.message_repository import MessageRepository
from src.repositories.user_profile_repository import UserProfileRepository

logger = get_logger()


class MemoryService:
    """记忆服务：管理短期记忆（3轮对话）和长期画像."""

    def __init__(
        self,
        message_repo: MessageRepository,
        profile_repo: UserProfileRepository,
    ):
        self.message_repo = message_repo
        self.profile_repo = profile_repo

    async def get_short_term_memory(
        self, conversation_id: int, turns: int = 3
    ) -> list[dict]:
        """获取短期记忆（最近 N 轮对话）.

        Args:
            conversation_id: 会话 ID
            turns: 轮数（默认 3 轮，即最近 6 条消息：3 user + 3 assistant）

        Returns:
            消息列表（按时间正序）
        """
        limit = turns * 2
        messages = await self.message_repo.get_recent_messages(conversation_id, limit)

        return [
            {
                "role": msg.role.value,
                "content": msg.content,
            }
            for msg in messages
            if msg.role.value in ("user", "assistant")
        ]

    async def get_long_term_memory(self, user_id: int) -> dict:
        """获取长期记忆（用户画像）.

        Returns:
            用户画像字典（department, common_topics, preferences）
        """
        profile = await self.profile_repo.get_profile(user_id)
        if profile is None:
            return {
                "department": None,
                "common_topics": {},
                "preferences": {},
            }

        return {
            "department": profile.department,
            "common_topics": profile.common_topics or {},
            "preferences": profile.preferences or {},
        }

    async def update_long_term_memory(self, user_id: int, extracted_info: dict) -> None:
        """更新长期记忆（从对话中提取的信息）.

        Args:
            user_id: 用户 ID
            extracted_info: 提取的信息字典（可能包含 department, common_topics, preferences）
        """
        profile = await self.profile_repo.get_profile(user_id)
        if profile is None:
            await self.profile_repo.create_profile(
                user_id=user_id,
                department=extracted_info.get("department"),
                common_topics=extracted_info.get("common_topics", {}),
                preferences=extracted_info.get("preferences", {}),
            )
            return

        department = extracted_info.get("department")
        if department:
            profile.department = department

        common_topics = profile.common_topics or {}
        new_topics = extracted_info.get("common_topics", {})
        if new_topics:
            for key, value in new_topics.items():
                common_topics[key] = common_topics.get(key, 0) + value
            profile.common_topics = common_topics

        preferences = profile.preferences or {}
        new_preferences = extracted_info.get("preferences", {})
        if new_preferences:
            preferences.update(new_preferences)
            profile.preferences = preferences

        await self.profile_repo.update_profile(
            user_id=user_id,
            department=profile.department,
            common_topics=profile.common_topics,
            preferences=profile.preferences,
        )
