"""Conversation routes for list, create, and detail."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.models.conversation import ConversationCreate, MessageSend
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.ticket_repository import TicketRepository
from src.repositories.user_profile_repository import UserProfileRepository
from src.services import ws_broadcast
from src.services.conversation_service import ConversationService
from src.services.rag.rag_pipeline import RagPipeline

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("")
async def list_conversations(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> dict:
    """获取当前用户的历史会话列表.

    Args:
        current_user: 当前认证用户
        db: 数据库会话
        page: 页码，默认 1
        page_size: 每页条数，默认 50

    Returns:
        会话列表响应
    """
    repo = ConversationRepository(db)
    service = ConversationService(repo)

    data = await service.list_conversations(
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    return {"code": 200, "message": "success", "data": data}


@router.post("")
async def create_conversation(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: ConversationCreate,
) -> dict:
    """新建会话.

    Args:
        current_user: 当前认证用户
        db: 数据库会话
        request: 创建请求（title 可选，默认「新对话」）

    Returns:
        新建的会话数据
    """
    repo = ConversationRepository(db)
    service = ConversationService(repo)

    data = await service.create_conversation(
        user_id=current_user.id,
        title=request.title,
    )

    return {"code": 200, "message": "success", "data": data}


@router.get("/{conversation_id}")
async def get_conversation_detail(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """获取会话详情及消息列表.

    Args:
        conversation_id: 会话 ID
        current_user: 当前认证用户
        db: 数据库会话

    Returns:
        会话详情（含消息列表）

    Raises:
        HTTPException: 404 如果会话不存在或不属于当前用户
    """
    repo = ConversationRepository(db)
    service = ConversationService(repo)

    data = await service.get_conversation_detail(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 2001, "message": "会话不存在", "data": None},
        )

    return {"code": 200, "message": "success", "data": data}


@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: MessageSend,
) -> dict:
    """发送用户消息并获取 AI 回复.

    Args:
        conversation_id: 会话 ID
        current_user: 当前认证用户
        db: 数据库会话
        request: 消息内容

    Returns:
        user_message: 用户消息
        assistant_message: AI 回复消息

    Raises:
        HTTPException: 404 如果会话不存在
        HTTPException: 400 如果会话已完成
    """
    repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    profile_repo = UserProfileRepository(db)
    rag_pipeline = RagPipeline(db)

    service = ConversationService(
        repo=repo,
        message_repo=message_repo,
        profile_repo=profile_repo,
        rag_pipeline=rag_pipeline,
    )

    result = await service.send_message(
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=request.content,
    )

    if "error" in result:
        if result["code"] == 2001:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": 2001, "message": result["error"], "data": None},
            )
        if result["code"] == 2002:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": 2002, "message": result["error"], "data": None},
            )

    await db.commit()
    user_id = current_user.id
    await ws_broadcast.broadcast_new_message(
        user_id,
        conversation_id=conversation_id,
        message=result["user_message"],
    )
    await ws_broadcast.broadcast_new_message(
        user_id,
        conversation_id=conversation_id,
        message=result["assistant_message"],
    )
    return {"code": 200, "message": "success", "data": result}


@router.post("/{conversation_id}/transfer")
async def transfer_conversation(
    conversation_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """转人工：创建工单并将会话置为排队中."""
    repo = ConversationRepository(db)
    message_repo = MessageRepository(db)
    ticket_repo = TicketRepository(db)
    service = ConversationService(
        repo=repo,
        message_repo=message_repo,
        ticket_repo=ticket_repo,
    )

    result = await service.transfer_to_human(
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if "error" in result:
        if result["code"] == 2001:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": 2001, "message": result["error"], "data": None},
            )
        if result["code"] in (2002, 2003):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"code": result["code"], "message": result["error"], "data": None},
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"code": result["code"], "message": result["error"], "data": None},
        )

    await db.commit()
    ticket = result["ticket"]
    await ws_broadcast.broadcast_ticket_created(
        result["user_id"],
        ticket_id=ticket["id"],
        conversation_id=ticket["conversation_id"],
        status=ticket["status"],
    )
    await ws_broadcast.broadcast_ticket_status_changed(
        result["user_id"],
        ticket_id=ticket["id"],
        status=ticket["status"],
        conversation_id=result["conversation_id"],
        conversation_status=result["conversation_status"],
    )
    await ws_broadcast.broadcast_new_message(
        result["user_id"],
        conversation_id=result["conversation_id"],
        ticket_id=ticket["id"],
        message=result["system_message"],
    )
    return {"code": 200, "message": "success", "data": result}
