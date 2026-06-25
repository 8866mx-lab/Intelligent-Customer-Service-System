"""Ticket repository for database access."""

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.db.models import Conversation, Ticket, TicketCategory, TicketStatus, User


class TicketRepository:
    """Ticket repository."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_ticket(self, conversation_id: int, user_id: int) -> Ticket:
        """创建待处理工单."""
        ticket = Ticket(
            conversation_id=conversation_id,
            user_id=user_id,
            status=TicketStatus.PENDING,
        )
        self.db.add(ticket)
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def get_by_conversation_id(self, conversation_id: int) -> Ticket | None:
        """根据会话 ID 获取工单."""
        result = await self.db.execute(
            select(Ticket).where(Ticket.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, ticket_id: int) -> Ticket | None:
        """根据 ID 获取工单."""
        result = await self.db.execute(select(Ticket).where(Ticket.id == ticket_id))
        return result.scalar_one_or_none()

    async def list_tickets(
        self,
        *,
        status: TicketStatus | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> tuple[list[Ticket], int]:
        """分页获取工单列表."""
        query = select(Ticket)
        count_query = select(func.count(Ticket.id))

        if status is not None:
            query = query.where(Ticket.status == status)
            count_query = count_query.where(Ticket.status == status)

        total = (await self.db.execute(count_query)).scalar_one()
        offset = (page - 1) * page_size
        result = await self.db.execute(
            query.order_by(Ticket.updated_at.desc()).offset(offset).limit(page_size)
        )
        return list(result.scalars().all()), total

    async def get_user_by_id(self, user_id: int) -> User | None:
        """获取用户信息."""
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    async def get_conversation_by_id(self, conversation_id: int) -> Conversation | None:
        """获取会话标题等信息."""
        result = await self.db.execute(
            select(Conversation).where(Conversation.id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def accept_ticket(self, ticket_id: int, agent_id: int) -> Ticket | None:
        """坐席接单."""
        ticket = await self.get_by_id(ticket_id)
        if ticket is None:
            return None
        if ticket.status != TicketStatus.PENDING:
            return ticket

        ticket.status = TicketStatus.PROCESSING
        ticket.agent_id = agent_id
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def update_category(self, ticket_id: int, category: TicketCategory) -> Ticket | None:
        """更新工单分类."""
        ticket = await self.get_by_id(ticket_id)
        if ticket is None:
            return None

        ticket.category = category
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket

    async def complete_ticket(self, ticket_id: int) -> Ticket | None:
        """结束工单."""
        ticket = await self.get_by_id(ticket_id)
        if ticket is None:
            return None

        ticket.status = TicketStatus.COMPLETED
        await self.db.flush()
        await self.db.refresh(ticket)
        return ticket
