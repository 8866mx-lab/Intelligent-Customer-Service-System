"""Conversation repository for database access."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.db.models import Conversation, ConversationStatus


class ConversationRepository:
    """Conversation repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_conversation(
        self,
        user_id: int,
        title: str,
    ) -> Conversation:
        """创建会话."""
        conversation = Conversation(
            user_id=user_id,
            title=title,
        )
        self.db.add(conversation)
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation

    async def get_conversation_by_id(
        self, conversation_id: int, user_id: int
    ) -> Conversation | None:
        """根据 ID 获取会话（含消息）."""
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()

    async def get_conversation_by_id_simple(
        self, conversation_id: int, user_id: int
    ) -> Conversation | None:
        """根据 ID 获取会话（不含消息，用于简单查询）."""
        result = await self.db.execute(
            select(Conversation).where(
                Conversation.id == conversation_id, Conversation.user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def list_conversations(
        self, user_id: int, page: int = 1, page_size: int = 50
    ) -> tuple[list[Conversation], int]:
        """获取用户会话列表（分页）."""
        # Get total count
        count_result = await self.db.execute(
            select(func.count(Conversation.id)).where(Conversation.user_id == user_id)
        )
        total = count_result.scalar_one()

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        conversations = result.scalars().all()

        return list(conversations), total

    async def update_status(
        self,
        conversation_id: int,
        user_id: int,
        status: ConversationStatus,
    ) -> Conversation | None:
        """更新会话状态."""
        conversation = await self.get_conversation_by_id_simple(conversation_id, user_id)
        if conversation is None:
            return None

        conversation.status = status
        await self.db.flush()
        await self.db.refresh(conversation)
        return conversation
