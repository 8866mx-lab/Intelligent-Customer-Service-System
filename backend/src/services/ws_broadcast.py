"""WebSocket event broadcast helpers."""

from datetime import datetime
from typing import Any

from src.services.ws_manager import ws_manager


def _serialize_dt(value: Any) -> Any:
    if isinstance(value, datetime):
        return value.isoformat()
    return value


def _serialize_message(message: dict) -> dict:
    return {
        "id": message["id"],
        "role": message["role"],
        "content": message["content"],
        "metadata": message.get("metadata"),
        "created_at": _serialize_dt(message["created_at"]),
    }


async def broadcast_new_message(
    user_id: int,
    *,
    conversation_id: int,
    message: dict,
    ticket_id: int | None = None,
) -> None:
    """推送新消息事件."""
    data: dict[str, Any] = {
        "conversation_id": conversation_id,
        "message": _serialize_message(message),
    }
    if ticket_id is not None:
        data["ticket_id"] = ticket_id

    await ws_manager.send_to_user(
        user_id,
        {"event": "new_message", "data": data},
    )


async def broadcast_ticket_status_changed(
    user_id: int,
    *,
    ticket_id: int,
    status: str,
    conversation_id: int,
    conversation_status: str,
) -> None:
    """推送工单/会话状态变更."""
    await ws_manager.send_to_user(
        user_id,
        {
            "event": "ticket_status_changed",
            "data": {
                "ticket_id": ticket_id,
                "status": status,
                "conversation_id": conversation_id,
                "conversation_status": conversation_status,
            },
        },
    )


async def broadcast_ticket_created(
    user_id: int,
    *,
    ticket_id: int,
    conversation_id: int,
    status: str,
) -> None:
    """推送新工单创建（转人工）."""
    await ws_manager.send_to_user(
        user_id,
        {
            "event": "ticket_created",
            "data": {
                "ticket_id": ticket_id,
                "conversation_id": conversation_id,
                "status": status,
            },
        },
    )
