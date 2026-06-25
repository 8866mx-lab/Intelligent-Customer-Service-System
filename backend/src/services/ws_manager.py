"""WebSocket connection manager for real-time message push."""

from collections import defaultdict

from fastapi import WebSocket
from pycore.core import get_logger

logger = get_logger()


class ConnectionManager:
    """Manage WebSocket connections keyed by user id."""

    def __init__(self) -> None:
        self._connections: dict[int, set[WebSocket]] = defaultdict(set)

    async def connect(self, user_id: int, websocket: WebSocket) -> None:
        await websocket.accept()
        self._connections[user_id].add(websocket)
        logger.info("WebSocket connected", user_id=user_id, count=len(self._connections[user_id]))

    def disconnect(self, user_id: int, websocket: WebSocket) -> None:
        connections = self._connections.get(user_id)
        if not connections:
            return
        connections.discard(websocket)
        if not connections:
            del self._connections[user_id]
        logger.info("WebSocket disconnected", user_id=user_id)

    async def send_to_user(self, user_id: int, payload: dict) -> None:
        connections = list(self._connections.get(user_id, set()))
        if not connections:
            return

        dead: list[WebSocket] = []
        for websocket in connections:
            try:
                await websocket.send_json(payload)
            except Exception:
                dead.append(websocket)

        for websocket in dead:
            self.disconnect(user_id, websocket)


ws_manager = ConnectionManager()
