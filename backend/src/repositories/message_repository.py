"""Message repository for database access."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Message, MessageRole


class MessageRepository:
    """Message repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_message(
        self,
        conversation_id: int,
        role: MessageRole,
        content: str,
        metadata: dict | None = None,
    ) -> Message:
        """创建消息."""
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            meta_data=metadata,
        )
        self.db.add(message)
        await self.db.flush()
        await self.db.refresh(message)
        return message

    async def get_recent_messages(
        self, conversation_id: int, limit: int = 10
    ) -> list[Message]:
        """获取最近 N 条消息."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(limit)
        )
        messages = result.scalars().all()
        return list(reversed(list(messages)))

    async def list_messages(self, conversation_id: int) -> list[Message]:
        """获取会话全部消息（按时间升序）."""
        result = await self.db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )
        return list(result.scalars().all())
