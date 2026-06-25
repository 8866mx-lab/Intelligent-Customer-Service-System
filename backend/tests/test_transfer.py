"""Tests for transfer to human endpoint."""

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from src.core.security import create_access_token, hash_password
from src.db.models import Conversation, Message, Ticket, User
from src.main import app


@pytest.fixture
async def setup_database(
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

        ai_conv = Conversation(user_id=user_id, title="AI 对话", status="ai_chat")
        done_conv = Conversation(user_id=user_id, title="已完成", status="completed")
        queuing_conv = Conversation(user_id=user_id, title="VPN 无法连接", status="queuing")
        session.add(ai_conv)
        session.add(done_conv)
        session.add(queuing_conv)
        await session.commit()
        await session.refresh(ai_conv)
        await session.refresh(done_conv)
        await session.refresh(queuing_conv)

        session.add(
            Message(
                conversation_id=queuing_conv.id,
                role="user",
                content="公司的 VPN 连不上了",
            )
        )
        pending_ticket = Ticket(
            conversation_id=queuing_conv.id,
            user_id=user_id,
            status="pending",
        )
        session.add(pending_ticket)
        await session.commit()
        await session.refresh(pending_ticket)

    token = create_access_token(data={"sub": str(user_id)})

    return {
        "token": token,
        "user_id": user_id,
        "ai_conversation_id": ai_conv.id,
        "completed_conversation_id": done_conv.id,
        "pending_ticket_id": pending_ticket.id,
        "queuing_conversation_id": queuing_conv.id,
    }


@pytest.mark.asyncio
async def test_transfer_success(
    setup_database: dict[str, Any],
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    token = setup_database["token"]
    conversation_id = setup_database["ai_conversation_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/conversations/{conversation_id}/transfer",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["conversation_id"] == conversation_id
    assert data["data"]["conversation_status"] == "queuing"
    assert data["data"]["ticket"]["status"] == "pending"

    async with test_session_factory() as session:
        ticket = (
            await session.execute(
                select(Ticket).where(Ticket.conversation_id == conversation_id)
            )
        ).scalar_one()
        assert ticket.status.value == "pending"


@pytest.mark.asyncio
async def test_transfer_completed_conversation_fails(setup_database: dict[str, Any]) -> None:
    token = setup_database["token"]
    conversation_id = setup_database["completed_conversation_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/conversations/{conversation_id}/transfer",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["code"] == 2002
    assert "不可转人工" in detail["message"]


@pytest.mark.asyncio
async def test_list_tickets(setup_database: dict[str, Any]) -> None:
    token = setup_database["token"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/tickets",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["total"] >= 1
    assert any(item["status"] == "pending" for item in data["data"]["items"])


@pytest.mark.asyncio
async def test_get_ticket_detail(setup_database: dict[str, Any]) -> None:
    token = setup_database["token"]
    ticket_id = setup_database["pending_ticket_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            f"/api/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["id"] == ticket_id
    assert len(data["messages"]) >= 1


@pytest.mark.asyncio
async def test_accept_ticket(
    setup_database: dict[str, Any],
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    token = setup_database["token"]
    ticket_id = setup_database["pending_ticket_id"]
    conversation_id = setup_database["queuing_conversation_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            f"/api/tickets/{ticket_id}/accept",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "processing"
    assert data["conversation_status"] == "processing"

    async with test_session_factory() as session:
        ticket = await session.get(Ticket, ticket_id)
        conversation = await session.get(Conversation, conversation_id)
        assert ticket is not None
        assert conversation is not None
        assert ticket.status.value == "processing"
        assert conversation.status.value == "processing"


@pytest.mark.asyncio
async def test_send_agent_message(setup_database: dict[str, Any]) -> None:
    token = setup_database["token"]
    ticket_id = setup_database["pending_ticket_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            f"/api/tickets/{ticket_id}/accept",
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.post(
            f"/api/tickets/{ticket_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "您好，我来协助您处理。"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["role"] == "agent"
    assert "协助" in data["content"]


@pytest.mark.asyncio
async def test_suggest_replies(
    setup_database: dict[str, Any], monkeypatch: pytest.MonkeyPatch
) -> None:
    from src.services.rag.rag_pipeline import RagPipeline

    async def fake_suggest(self, **kwargs: Any) -> list[dict[str, str | int]]:
        _ = kwargs
        return [
            {"index": 1, "content": "建议一"},
            {"index": 2, "content": "建议二"},
            {"index": 3, "content": "建议三"},
        ]

    monkeypatch.setattr(RagPipeline, "suggest_agent_replies", fake_suggest)

    token = setup_database["token"]
    ticket_id = setup_database["pending_ticket_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            f"/api/tickets/{ticket_id}/accept",
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.post(
            f"/api/tickets/{ticket_id}/suggest",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    suggestions = response.json()["data"]["suggestions"]
    assert len(suggestions) == 3
    assert suggestions[0]["index"] == 1


@pytest.mark.asyncio
async def test_patch_ticket_category(setup_database: dict[str, Any]) -> None:
    token = setup_database["token"]
    ticket_id = setup_database["pending_ticket_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            f"/api/tickets/{ticket_id}/accept",
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.patch(
            f"/api/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"category": "it"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["category"] == "it"
    assert data["status"] == "processing"


@pytest.mark.asyncio
async def test_complete_ticket(
    setup_database: dict[str, Any],
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    token = setup_database["token"]
    ticket_id = setup_database["pending_ticket_id"]
    conversation_id = setup_database["queuing_conversation_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            f"/api/tickets/{ticket_id}/accept",
            headers={"Authorization": f"Bearer {token}"},
        )
        response = await client.patch(
            f"/api/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "completed"},
        )

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["status"] == "completed"
    assert data["conversation_status"] == "completed"

    async with test_session_factory() as session:
        ticket = await session.get(Ticket, ticket_id)
        conversation = await session.get(Conversation, conversation_id)
        assert ticket is not None
        assert conversation is not None
        assert ticket.status.value == "completed"
        assert conversation.status.value == "completed"


@pytest.mark.asyncio
async def test_completed_conversation_cannot_send_message(setup_database: dict[str, Any]) -> None:
    token = setup_database["token"]
    ticket_id = setup_database["pending_ticket_id"]
    conversation_id = setup_database["queuing_conversation_id"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        await client.post(
            f"/api/tickets/{ticket_id}/accept",
            headers={"Authorization": f"Bearer {token}"},
        )
        await client.patch(
            f"/api/tickets/{ticket_id}",
            headers={"Authorization": f"Bearer {token}"},
            json={"status": "completed"},
        )
        response = await client.post(
            f"/api/conversations/{conversation_id}/messages",
            headers={"Authorization": f"Bearer {token}"},
            json={"content": "还能发吗"},
        )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == 2002
