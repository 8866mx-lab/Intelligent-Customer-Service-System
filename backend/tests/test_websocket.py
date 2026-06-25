"""Tests for WebSocket real-time push."""

from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.security import create_access_token, hash_password
from src.db.models import Conversation, ConversationStatus, Message, Ticket, User
from src.main import app


@pytest.fixture
async def transfer_setup(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    async with test_session_factory() as session:
        test_user = User(
            username="zhangsan",
            password_hash=hash_password("password123"),
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        user_id = test_user.id

        ai_conv = Conversation(
            user_id=user_id,
            title="转人工测试",
            status=ConversationStatus.AI_CHAT,
        )
        session.add(ai_conv)
        await session.commit()
        await session.refresh(ai_conv)

    token = create_access_token({"sub": str(user_id)})
    return {
        "token": token,
        "user_id": user_id,
        "conversation_id": ai_conv.id,
    }


@pytest.fixture
async def ticket_setup(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    async with test_session_factory() as session:
        test_user = User(
            username="zhangsan",
            password_hash=hash_password("password123"),
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        user_id = test_user.id

        conversation = Conversation(
            user_id=user_id,
            title="测试会话",
            status=ConversationStatus.QUEUING,
        )
        session.add(conversation)
        await session.commit()
        await session.refresh(conversation)

        session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content="需要人工帮助",
            )
        )
        pending_ticket = Ticket(
            conversation_id=conversation.id,
            user_id=user_id,
            status="pending",
        )
        session.add(pending_ticket)
        await session.commit()
        await session.refresh(pending_ticket)

    token = create_access_token({"sub": str(user_id)})
    return {
        "token": token,
        "user_id": user_id,
        "conversation_id": conversation.id,
        "ticket_id": pending_ticket.id,
    }


@pytest.mark.asyncio
async def test_websocket_rejects_invalid_token() -> None:
    with TestClient(app) as client:
        with pytest.raises(Exception):
            with client.websocket_connect("/ws/messages?token=invalid"):
                pass


@pytest.mark.asyncio
async def test_websocket_new_message_on_agent_reply(ticket_setup: dict[str, Any]) -> None:
    token = ticket_setup["token"]
    ticket_id = ticket_setup["ticket_id"]
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        accept_resp = client.post(f"/api/tickets/{ticket_id}/accept", headers=headers)
        assert accept_resp.status_code == 200

        with client.websocket_connect(f"/ws/messages?token={token}") as ws:
            send_resp = client.post(
                f"/api/tickets/{ticket_id}/messages",
                headers=headers,
                json={"content": "坐席实时回复"},
            )
            assert send_resp.status_code == 200

            event = ws.receive_json()
            assert event["event"] == "new_message"
            assert event["data"]["ticket_id"] == ticket_id
            assert event["data"]["message"]["role"] == "agent"
            assert event["data"]["message"]["content"] == "坐席实时回复"


@pytest.mark.asyncio
async def test_websocket_ticket_created_on_transfer(transfer_setup: dict[str, Any]) -> None:
    token = transfer_setup["token"]
    conversation_id = transfer_setup["conversation_id"]
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        with client.websocket_connect(f"/ws/messages?token={token}") as ws:
            transfer_resp = client.post(
                f"/api/conversations/{conversation_id}/transfer",
                headers=headers,
            )
            assert transfer_resp.status_code == 200

            event = ws.receive_json()
            assert event["event"] == "ticket_created"
            assert event["data"]["conversation_id"] == conversation_id
            assert event["data"]["status"] == "pending"


@pytest.mark.asyncio
async def test_websocket_ticket_status_changed_on_complete(ticket_setup: dict[str, Any]) -> None:
    token = ticket_setup["token"]
    ticket_id = ticket_setup["ticket_id"]
    conversation_id = ticket_setup["conversation_id"]
    headers = {"Authorization": f"Bearer {token}"}

    with TestClient(app) as client:
        accept_resp = client.post(f"/api/tickets/{ticket_id}/accept", headers=headers)
        assert accept_resp.status_code == 200

        with client.websocket_connect(f"/ws/messages?token={token}") as ws:
            patch_resp = client.patch(
                f"/api/tickets/{ticket_id}",
                headers=headers,
                json={"status": "completed"},
            )
            assert patch_resp.status_code == 200

            event = ws.receive_json()
            assert event["event"] == "ticket_status_changed"
            assert event["data"]["ticket_id"] == ticket_id
            assert event["data"]["status"] == "completed"
            assert event["data"]["conversation_id"] == conversation_id
            assert event["data"]["conversation_status"] == "completed"
