"""Ticket service for agent workflow."""

from pycore.core import get_logger
from src.db.models import ConversationStatus, MessageRole, TicketCategory, TicketStatus
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.ticket_repository import TicketRepository
from src.repositories.user_profile_repository import UserProfileRepository
from src.services.memory_service import MemoryService
from src.services.rag.rag_pipeline import RagPipeline

logger = get_logger()


class TicketService:
    """工单服务（坐席端）."""

    def __init__(
        self,
        ticket_repo: TicketRepository,
        message_repo: MessageRepository,
        conversation_repo: ConversationRepository,
        profile_repo: UserProfileRepository | None = None,
        rag_pipeline: RagPipeline | None = None,
    ):
        self.ticket_repo = ticket_repo
        self.message_repo = message_repo
        self.conversation_repo = conversation_repo
        self.profile_repo = profile_repo
        self.rag_pipeline = rag_pipeline

    async def list_tickets(
        self,
        *,
        status: str | None = None,
        page: int = 1,
        page_size: int = 50,
    ) -> dict:
        """工单列表."""
        status_enum = TicketStatus(status) if status else None
        tickets, total = await self.ticket_repo.list_tickets(
            status=status_enum,
            page=page,
            page_size=page_size,
        )

        items = []
        for ticket in tickets:
            items.append(await self._serialize_list_item(ticket))

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def get_ticket_detail(self, ticket_id: int) -> dict | None:
        """工单详情含完整对话."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None:
            return None

        user = await self.ticket_repo.get_user_by_id(ticket.user_id)
        agent = (
            await self.ticket_repo.get_user_by_id(ticket.agent_id)
            if ticket.agent_id is not None
            else None
        )
        messages = await self.message_repo.list_messages(ticket.conversation_id)
        summary = await self._build_summary(ticket.conversation_id)

        return {
            "id": ticket.id,
            "conversation_id": ticket.conversation_id,
            "user_id": ticket.user_id,
            "user_name": user.username if user else "未知用户",
            "agent_id": ticket.agent_id,
            "agent_name": agent.username if agent else None,
            "category": ticket.category.value if ticket.category else None,
            "status": ticket.status.value,
            "summary": summary,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "metadata": msg.meta_data,
                    "created_at": msg.created_at,
                }
                for msg in messages
            ],
        }

    async def accept_ticket(self, ticket_id: int, agent_id: int) -> dict:
        """坐席接单."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None:
            return {"error": "工单不存在", "code": 3001}

        if ticket.status != TicketStatus.PENDING:
            return {"error": "工单状态不允许接单", "code": 3002}

        updated = await self.ticket_repo.accept_ticket(ticket_id, agent_id)
        if updated is None:
            return {"error": "工单不存在", "code": 3001}

        conversation = await self.conversation_repo.update_status(
            conversation_id=updated.conversation_id,
            user_id=updated.user_id,
            status=ConversationStatus.PROCESSING,
        )

        logger.info(
            "Ticket accepted",
            ticket_id=ticket_id,
            agent_id=agent_id,
            conversation_id=updated.conversation_id,
        )

        return {
            "id": updated.id,
            "status": updated.status.value,
            "agent_id": updated.agent_id,
            "conversation_id": updated.conversation_id,
            "user_id": updated.user_id,
            "conversation_status": conversation.status.value if conversation else "processing",
            "updated_at": updated.updated_at,
        }

    async def send_agent_message(
        self, ticket_id: int, agent_id: int, content: str
    ) -> dict:
        """坐席发送人工回复."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None:
            return {"error": "工单不存在", "code": 3001}

        if ticket.status != TicketStatus.PROCESSING:
            return {"error": "工单状态不允许发送消息", "code": 3003}

        if ticket.agent_id is not None and ticket.agent_id != agent_id:
            return {"error": "仅接单坐席可回复此工单", "code": 3004}

        message = await self.message_repo.create_message(
            conversation_id=ticket.conversation_id,
            role=MessageRole.AGENT,
            content=content,
            metadata=None,
        )

        logger.info("Agent message sent", ticket_id=ticket_id, message_id=message.id)

        return {
            "id": message.id,
            "role": message.role.value,
            "content": message.content,
            "metadata": message.meta_data,
            "created_at": message.created_at,
            "conversation_id": ticket.conversation_id,
            "ticket_id": ticket.id,
            "user_id": ticket.user_id,
        }

    async def suggest_replies(self, ticket_id: int, agent_id: int) -> dict:
        """智能回复：RAG 生成 3 条候选."""
        if self.rag_pipeline is None or self.profile_repo is None:
            return {"error": "服务未正确初始化", "code": 5000}

        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None:
            return {"error": "工单不存在", "code": 3001}

        if ticket.status != TicketStatus.PROCESSING:
            return {"error": "工单状态不允许智能回复", "code": 3003}

        if ticket.agent_id is not None and ticket.agent_id != agent_id:
            return {"error": "仅接单坐席可使用智能回复", "code": 3004}

        messages = await self.message_repo.list_messages(ticket.conversation_id)
        message_dicts = [
            {"role": msg.role.value, "content": msg.content} for msg in messages
        ]

        memory_service = MemoryService(self.message_repo, self.profile_repo)
        long_term = await memory_service.get_long_term_memory(ticket.user_id)

        suggestions = await self.rag_pipeline.suggest_agent_replies(
            messages=message_dicts,
            user_id=ticket.user_id,
            long_term_memory=long_term,
        )

        return {"suggestions": suggestions}

    async def update_ticket(
        self,
        ticket_id: int,
        agent_id: int,
        *,
        category: str | None = None,
        status: str | None = None,
    ) -> dict:
        """更新工单分类或结束工单."""
        ticket = await self.ticket_repo.get_by_id(ticket_id)
        if ticket is None:
            return {"error": "工单不存在", "code": 3001}

        if ticket.agent_id is not None and ticket.agent_id != agent_id:
            return {"error": "仅接单坐席可更新此工单", "code": 3004}

        conversation_status = None
        system_message: dict | None = None

        if category is not None:
            if ticket.status != TicketStatus.PROCESSING:
                return {"error": "工单状态不允许此操作", "code": 3002}

            updated = await self.ticket_repo.update_category(
                ticket_id, TicketCategory(category)
            )
            if updated is None:
                return {"error": "工单不存在", "code": 3001}
            ticket = updated

        if status == "completed":
            if ticket.status != TicketStatus.PROCESSING:
                return {"error": "工单状态不允许此操作", "code": 3002}

            updated = await self.ticket_repo.complete_ticket(ticket_id)
            if updated is None:
                return {"error": "工单不存在", "code": 3001}
            ticket = updated

            conversation = await self.conversation_repo.update_status(
                conversation_id=ticket.conversation_id,
                user_id=ticket.user_id,
                status=ConversationStatus.COMPLETED,
            )
            conversation_status = (
                conversation.status.value if conversation else ConversationStatus.COMPLETED.value
            )

            closed_message = await self.message_repo.create_message(
                conversation_id=ticket.conversation_id,
                role=MessageRole.SYSTEM,
                content="工单已结束，会话已关闭。",
                metadata=None,
            )
            system_message = {
                "id": closed_message.id,
                "role": closed_message.role.value,
                "content": closed_message.content,
                "metadata": closed_message.meta_data,
                "created_at": closed_message.created_at,
            }

            logger.info(
                "Ticket completed",
                ticket_id=ticket_id,
                conversation_id=ticket.conversation_id,
            )

        if conversation_status is None:
            conv = await self.ticket_repo.get_conversation_by_id(ticket.conversation_id)
            conversation_status = conv.status.value if conv else "processing"

        result = {
            "id": ticket.id,
            "status": ticket.status.value,
            "category": ticket.category.value if ticket.category else None,
            "conversation_id": ticket.conversation_id,
            "user_id": ticket.user_id,
            "conversation_status": conversation_status,
            "updated_at": ticket.updated_at,
        }
        if system_message is not None:
            result["system_message"] = system_message
        return result

    async def _serialize_list_item(self, ticket) -> dict:
        user = await self.ticket_repo.get_user_by_id(ticket.user_id)
        summary = await self._build_summary(ticket.conversation_id)
        return {
            "id": ticket.id,
            "conversation_id": ticket.conversation_id,
            "user_id": ticket.user_id,
            "user_name": user.username if user else "未知用户",
            "agent_id": ticket.agent_id,
            "category": ticket.category.value if ticket.category else None,
            "status": ticket.status.value,
            "summary": summary,
            "created_at": ticket.created_at,
            "updated_at": ticket.updated_at,
        }

    async def _build_summary(self, conversation_id: int) -> str:
        conversation = await self.ticket_repo.get_conversation_by_id(conversation_id)
        if conversation and conversation.title.strip():
            return conversation.title.strip()

        messages = await self.message_repo.list_messages(conversation_id)
        for msg in messages:
            if msg.role == MessageRole.USER and msg.content.strip():
                text = msg.content.strip().replace("\n", " ")
                return text[:40] + ("…" if len(text) > 40 else "")

        return "无摘要"
