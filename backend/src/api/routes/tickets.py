"""Ticket routes for agent list, detail, and accept."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.db.models import User
from src.db.session import get_db
from src.models.conversation import MessageSend
from src.models.ticket import TicketUpdate
from src.repositories.conversation_repository import ConversationRepository
from src.repositories.message_repository import MessageRepository
from src.repositories.ticket_repository import TicketRepository
from src.repositories.user_profile_repository import UserProfileRepository
from src.services.rag.rag_pipeline import RagPipeline
from src.services import ws_broadcast
from src.services.ticket_service import TicketService

router = APIRouter(prefix="/api/tickets", tags=["tickets"])


def _build_ticket_service(db: AsyncSession) -> TicketService:
    return TicketService(
        ticket_repo=TicketRepository(db),
        message_repo=MessageRepository(db),
        conversation_repo=ConversationRepository(db),
        profile_repo=UserProfileRepository(db),
        rag_pipeline=RagPipeline(db),
    )


@router.get("")
async def list_tickets(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    status: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
) -> dict:
    """获取工单列表（坐席端）."""
    _ = current_user
    service = _build_ticket_service(db)
    try:
        data = await service.list_tickets(status=status, page=page, page_size=page_size)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 3003, "message": "无效的工单状态", "data": None},
        ) from None

    return {"code": 200, "message": "success", "data": data}


@router.get("/{ticket_id}")
async def get_ticket_detail(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """获取工单详情及对话历史."""
    _ = current_user
    service = _build_ticket_service(db)
    data = await service.get_ticket_detail(ticket_id)
    if data is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": 3001, "message": "工单不存在", "data": None},
        )

    return {"code": 200, "message": "success", "data": data}


@router.post("/{ticket_id}/accept")
async def accept_ticket(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """坐席接单."""
    service = _build_ticket_service(db)
    result = await service.accept_ticket(ticket_id=ticket_id, agent_id=current_user.id)

    if "error" in result:
        if result["code"] == 3001:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": 3001, "message": result["error"], "data": None},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result["code"], "message": result["error"], "data": None},
        )

    await db.commit()
    await ws_broadcast.broadcast_ticket_status_changed(
        result["user_id"],
        ticket_id=result["id"],
        status=result["status"],
        conversation_id=result["conversation_id"],
        conversation_status=result["conversation_status"],
    )
    return {"code": 200, "message": "success", "data": result}


@router.post("/{ticket_id}/messages")
async def send_ticket_message(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: MessageSend,
) -> dict:
    """坐席发送人工回复."""
    service = _build_ticket_service(db)
    result = await service.send_agent_message(
        ticket_id=ticket_id,
        agent_id=current_user.id,
        content=request.content,
    )

    if "error" in result:
        if result["code"] == 3001:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": 3001, "message": result["error"], "data": None},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result["code"], "message": result["error"], "data": None},
        )

    await db.commit()
    await ws_broadcast.broadcast_new_message(
        result["user_id"],
        conversation_id=result["conversation_id"],
        ticket_id=result["ticket_id"],
        message=result,
    )
    return {"code": 200, "message": "success", "data": result}


@router.post("/{ticket_id}/suggest")
async def suggest_ticket_replies(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """智能回复：生成 3 条候选建议."""
    service = _build_ticket_service(db)
    result = await service.suggest_replies(ticket_id=ticket_id, agent_id=current_user.id)

    if "error" in result:
        if result["code"] == 3001:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": 3001, "message": result["error"], "data": None},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result["code"], "message": result["error"], "data": None},
        )

    return {"code": 200, "message": "success", "data": result}


@router.patch("/{ticket_id}")
async def update_ticket(
    ticket_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(get_db)],
    request: TicketUpdate,
) -> dict:
    """更新工单（归类或结束）."""
    service = _build_ticket_service(db)
    try:
        result = await service.update_ticket(
            ticket_id=ticket_id,
            agent_id=current_user.id,
            category=request.category,
            status=request.status,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": 3003, "message": str(exc), "data": None},
        ) from exc

    if "error" in result:
        if result["code"] == 3001:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"code": 3001, "message": result["error"], "data": None},
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"code": result["code"], "message": result["error"], "data": None},
        )

    await db.commit()
    await ws_broadcast.broadcast_ticket_status_changed(
        result["user_id"],
        ticket_id=result["id"],
        status=result["status"],
        conversation_id=result["conversation_id"],
        conversation_status=result["conversation_status"],
    )
    system_message = result.get("system_message")
    if system_message is not None:
        await ws_broadcast.broadcast_new_message(
            result["user_id"],
            conversation_id=result["conversation_id"],
            ticket_id=result["id"],
            message=system_message,
        )
    return {"code": 200, "message": "success", "data": result}
