"""Tests for conversation endpoints."""

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.core.security import create_access_token, hash_password
from src.db.models import Conversation, Message, User
from src.main import app


@pytest.fixture
async def setup_database(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> dict[str, Any]:
    """Seed test user and conversations."""
    async with test_session_factory() as session:
        test_user = User(
            username="zhangsan",
            password_hash=hash_password("password123"),
        )
        session.add(test_user)
        await session.commit()
        await session.refresh(test_user)
        user_id = test_user.id

        # Create test conversations
        conv1 = Conversation(
            user_id=user_id,
            title="请假流程咨询",
            status="ai_chat",
        )
        conv2 = Conversation(
            user_id=user_id,
            title="VPN 无法连接",
            status="completed",
        )
        session.add(conv1)
        session.add(conv2)
        await session.commit()
        await session.refresh(conv1)
        await session.refresh(conv2)

        # Add messages to conv1
        msg1 = Message(
            conversation_id=conv1.id,
            role="assistant",
            content="您好，我是企业内部智能助手，有什么可以帮您的？",
        )
        msg2 = Message(
            conversation_id=conv1.id,
            role="user",
            content="请问公司的请假流程是什么？",
        )
        session.add(msg1)
        session.add(msg2)
        await session.commit()

    # Generate token
    token = create_access_token(data={"sub": str(user_id)})

    return {"token": token, "user_id": user_id}


@pytest.mark.asyncio
async def test_list_conversations(setup_database: dict[str, Any]) -> None:
    """Test listing user conversations."""
    token = setup_database["token"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["message"] == "success"
    assert data["data"]["total"] == 2
    assert len(data["data"]["items"]) == 2
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 50
    # Check first item (most recent should be last created)
    items = data["data"]["items"]
    assert "id" in items[0]
    assert "title" in items[0]
    assert "status" in items[0]
    assert "created_at" in items[0]
    assert "updated_at" in items[0]


@pytest.mark.asyncio
async def test_list_conversations_pagination(setup_database: dict[str, Any]) -> None:
    """Test conversation list pagination."""
    token = setup_database["token"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/conversations?page=1&page_size=1",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["total"] == 2
    assert len(data["data"]["items"]) == 1
    assert data["data"]["page"] == 1
    assert data["data"]["page_size"] == 1


@pytest.mark.asyncio
async def test_create_conversation(setup_database: dict[str, Any]) -> None:
    """Test creating a new conversation."""
    token = setup_database["token"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
            json={"title": "新对话"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["message"] == "success"
    assert data["data"]["title"] == "新对话"
    assert data["data"]["status"] == "ai_chat"
    assert "id" in data["data"]
    assert "created_at" in data["data"]
    assert "updated_at" in data["data"]


@pytest.mark.asyncio
async def test_create_conversation_default_title(setup_database: dict[str, Any]) -> None:
    """Test creating conversation with default title."""
    token = setup_database["token"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
            json={},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["data"]["title"] == "新对话"


@pytest.mark.asyncio
async def test_get_conversation_detail(setup_database: dict[str, Any]) -> None:
    """Test getting conversation detail with messages."""
    token = setup_database["token"]

    # Get conversation list to find an ID
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        list_response = await client.get(
            "/api/conversations",
            headers={"Authorization": f"Bearer {token}"},
        )
        conversation_id = list_response.json()["data"]["items"][0]["id"]

        # Get conversation detail
        response = await client.get(
            f"/api/conversations/{conversation_id}",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["message"] == "success"
    assert data["data"]["id"] == conversation_id
    assert "title" in data["data"]
    assert "status" in data["data"]
    assert "messages" in data["data"]
    assert isinstance(data["data"]["messages"], list)


@pytest.mark.asyncio
async def test_get_conversation_detail_not_found(setup_database: dict[str, Any]) -> None:
    """Test getting non-existent conversation returns 404."""
    token = setup_database["token"]

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/conversations/99999",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 404
    data = response.json()
    assert data["detail"]["code"] == 2001
    assert data["detail"]["message"] == "会话不存在"


@pytest.mark.asyncio
async def test_list_conversations_unauthorized() -> None:
    """Test listing conversations without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/conversations")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_create_conversation_unauthorized() -> None:
    """Test creating conversation without authentication."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/conversations",
            json={"title": "测试"},
        )

    assert response.status_code == 401
