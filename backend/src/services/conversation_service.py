"""Conversation service for business logic."""

from pycore.core import get_logger
from src.db.models import ConversationStatus, MessageRole
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.ticket_repository import TicketRepository
from src.repositories.user_profile_repository import UserProfileRepository
from src.services.memory_service import MemoryService
from src.services.rag.rag_pipeline import RagPipeline

logger = get_logger()


class ConversationService:
    """会话服务."""

    def __init__(
        self,
        repo: ConversationRepository,
        message_repo: MessageRepository | None = None,
        profile_repo: UserProfileRepository | None = None,
        rag_pipeline: RagPipeline | None = None,
        ticket_repo: TicketRepository | None = None,
    ):
        self.repo = repo
        self.message_repo = message_repo
        self.profile_repo = profile_repo
        self.rag_pipeline = rag_pipeline
        self.ticket_repo = ticket_repo

    async def create_conversation(self, user_id: int, title: str | None = None) -> dict:
        """创建新会话."""
        if title is None or title.strip() == "":
            title = "新对话"

        conversation = await self.repo.create_conversation(user_id=user_id, title=title)

        return {
            "id": conversation.id,
            "title": conversation.title,
            "status": conversation.status.value,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
        }

    async def get_conversation_detail(
        self, conversation_id: int, user_id: int
    ) -> dict | None:
        """获取会话详情（含消息）."""
        conversation = await self.repo.get_conversation_by_id(conversation_id, user_id)

        if conversation is None:
            return None

        # Build messages list
        messages = []
        for msg in conversation.messages:
            messages.append(
                {
                    "id": msg.id,
                    "role": msg.role.value,
                    "content": msg.content,
                    "metadata": msg.meta_data,
                    "created_at": msg.created_at,
                }
            )

        return {
            "id": conversation.id,
            "title": conversation.title,
            "status": conversation.status.value,
            "created_at": conversation.created_at,
            "updated_at": conversation.updated_at,
            "messages": messages,
        }

    async def list_conversations(
        self, user_id: int, page: int = 1, page_size: int = 50
    ) -> dict:
        """获取会话列表（分页）."""
        conversations, total = await self.repo.list_conversations(user_id, page, page_size)

        items = []
        for conv in conversations:
            items.append(
                {
                    "id": conv.id,
                    "title": conv.title,
                    "status": conv.status.value,
                    "created_at": conv.created_at,
                    "updated_at": conv.updated_at,
                }
            )

        return {
            "items": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }

    async def send_message(
        self, conversation_id: int, user_id: int, content: str
    ) -> dict:
        """发送消息并获取 AI 回复."""
        if self.message_repo is None or self.profile_repo is None or self.rag_pipeline is None:
            return {"error": "服务未正确初始化", "code": 5000}

        conversation = await self.repo.get_conversation_by_id_simple(
            conversation_id, user_id
        )

        if conversation is None:
            return {"error": "会话不存在", "code": 2001}

        if conversation.status == ConversationStatus.COMPLETED:
            return {"error": "会话已完成，不可发送消息", "code": 2002}

        # 保存用户消息
        user_message = await self.message_repo.create_message(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            metadata=None,
        )

        # 获取记忆
        memory_service = MemoryService(self.message_repo, self.profile_repo)
        short_term = await memory_service.get_short_term_memory(conversation_id, turns=3)
        long_term = await memory_service.get_long_term_memory(user_id)

        # 执行 RAG
        rag_result = await self.rag_pipeline.run(
            query=content,
            user_id=user_id,
            short_term_memory=short_term,
            long_term_memory=long_term,
        )

        # 保存 AI 回复
        assistant_message = await self.message_repo.create_message(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=rag_result["content"],
            metadata={
                "response_type": rag_result["response_type"],
                "intent": rag_result.get("intent", "clear_query"),
                "citations": rag_result.get("citations", []),
                "match_label": rag_result.get("match_label"),
                "vector_similarity": rag_result.get("vector_similarity"),
            },
        )

        # 更新长期记忆（简单规则：提取部门关键词）
        if rag_result["response_type"] != "mock":
            extracted = self._extract_profile_info(content)
            if extracted:
                await memory_service.update_long_term_memory(user_id, extracted)

        return {
            "user_message": {
                "id": user_message.id,
                "role": user_message.role.value,
                "content": user_message.content,
                "metadata": user_message.meta_data,
                "created_at": user_message.created_at,
            },
            "assistant_message": {
                "id": assistant_message.id,
                "role": assistant_message.role.value,
                "content": assistant_message.content,
                "metadata": assistant_message.meta_data,
                "created_at": assistant_message.created_at,
            },
        }

    def _extract_profile_info(self, content: str) -> dict:
        """简单规则提取用户画像信息."""
        extracted: dict = {}

        # 简单关键词匹配
        departments = ["IT", "HR", "财务", "行政", "销售", "市场", "技术"]
        for dept in departments:
            if dept in content or dept.lower() in content.lower():
                extracted["department"] = dept
                break

        # 提取话题（简单计数）
        topics = ["请假", "报销", "VPN", "电脑", "工资", "考勤", "培训"]
        common_topics = {}
        for topic in topics:
            if topic in content:
                common_topics[topic] = 1

        if common_topics:
            extracted["common_topics"] = common_topics

        return extracted

    async def transfer_to_human(self, conversation_id: int, user_id: int) -> dict:
        """转人工：创建工单并将会话置为排队中."""
        if self.ticket_repo is None or self.message_repo is None:
            return {"error": "服务未正确初始化", "code": 5000}

        conversation = await self.repo.get_conversation_by_id_simple(conversation_id, user_id)
        if conversation is None:
            return {"error": "会话不存在", "code": 2001}

        if conversation.status == ConversationStatus.COMPLETED:
            return {"error": "会话已完成，不可转人工", "code": 2002}

        if conversation.status != ConversationStatus.AI_CHAT:
            return {"error": "会话已在排队或处理中", "code": 2003}

        existing = await self.ticket_repo.get_by_conversation_id(conversation_id)
        if existing is not None:
            return {"error": "会话已在排队或处理中", "code": 2003}

        ticket = await self.ticket_repo.create_ticket(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        updated = await self.repo.update_status(
            conversation_id=conversation_id,
            user_id=user_id,
            status=ConversationStatus.QUEUING,
        )
        if updated is None:
            return {"error": "会话不存在", "code": 2001}

        system_message = await self.message_repo.create_message(
            conversation_id=conversation_id,
            role=MessageRole.SYSTEM,
            content="已转人工，正在排队中…",
            metadata=None,
        )

        logger.info(
            "Transfer to human",
            conversation_id=conversation_id,
            ticket_id=ticket.id,
            user_id=user_id,
        )

        return {
            "conversation_id": updated.id,
            "conversation_status": updated.status.value,
            "user_id": user_id,
            "ticket": {
                "id": ticket.id,
                "conversation_id": ticket.conversation_id,
                "status": ticket.status.value,
                "created_at": ticket.created_at,
            },
            "system_message": {
                "id": system_message.id,
                "role": system_message.role.value,
                "content": system_message.content,
                "metadata": system_message.meta_data,
                "created_at": system_message.created_at,
            },
        }
