"""WebSocket routes for real-time push."""

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect

from src.core.security import decode_access_token
from src.services.ws_manager import ws_manager

router = APIRouter(tags=["websocket"])


@router.websocket("/ws/messages")
async def ws_messages(websocket: WebSocket, token: str = Query(...)) -> None:
    """实时消息推送（员工端 ↔ 坐席端）."""
    payload = decode_access_token(token)
    if payload is None:
        await websocket.close(code=1008, reason="Token 已过期或无效")
        return

    user_id_str = payload.get("sub")
    if user_id_str is None:
        await websocket.close(code=1008, reason="Token 已过期或无效")
        return

    try:
        user_id = int(user_id_str)
    except (ValueError, TypeError):
        await websocket.close(code=1008, reason="Token 已过期或无效")
        return

    await ws_manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(user_id, websocket)
