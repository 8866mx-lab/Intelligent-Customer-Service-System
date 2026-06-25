"""Tests for authentication endpoints."""

from typing import Any

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.core.security import hash_password
from src.db.models import User
from src.main import app


@pytest.fixture
async def setup_database(
    test_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Seed test user."""
    async with test_session_factory() as session:
        session.add(
            User(
                username="zhangsan",
                password_hash=hash_password("password123"),
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_login_success(setup_database: Any) -> None:  # noqa: ARG001
    """Test successful login with correct credentials."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "zhangsan", "password": "password123"},
        )

    assert response.status_code == 200
    data = response.json()
    assert data["code"] == 200
    assert data["message"] == "success"
    assert "access_token" in data["data"]
    assert data["data"]["token_type"] == "bearer"
    assert data["data"]["expires_in"] == 86400
    assert data["data"]["user"]["username"] == "zhangsan"


@pytest.mark.asyncio
async def test_login_wrong_password(setup_database: Any) -> None:  # noqa: ARG001
    """Test login with incorrect password."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "zhangsan", "password": "wrongpassword"},
        )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == 1001
    assert data["detail"]["message"] == "用户名或密码错误"


@pytest.mark.asyncio
async def test_login_nonexistent_user(setup_database: Any) -> None:  # noqa: ARG001
    """Test login with non-existent username."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post(
            "/api/auth/login",
            json={"username": "nonexistent", "password": "password123"},
        )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == 1001
    assert data["detail"]["message"] == "用户名或密码错误"


@pytest.mark.asyncio
async def test_get_me_success(setup_database: Any) -> None:  # noqa: ARG001
    """Test getting current user info with valid token."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # First login to get token
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "zhangsan", "password": "password123"},
        )
        token = login_response.json()["data"]["access_token"]

        # Get current user
        me_response = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert me_response.status_code == 200
    data = me_response.json()
    assert data["code"] == 200
    assert data["data"]["username"] == "zhangsan"


@pytest.mark.asyncio
async def test_get_me_invalid_token(setup_database: Any) -> None:  # noqa: ARG001
    """Test getting current user info with invalid token."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"},
        )

    assert response.status_code == 401
    data = response.json()
    assert data["detail"]["code"] == 1002
    assert data["detail"]["message"] == "Token 已过期或无效"


@pytest.mark.asyncio
async def test_get_me_no_token(setup_database: Any) -> None:  # noqa: ARG001
    """Test getting current user info without token."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.get("/api/auth/me")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_logout_success(setup_database: Any) -> None:  # noqa: ARG001
    """Test successful logout with valid token."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        # First login to get token
        login_response = await client.post(
            "/api/auth/login",
            json={"username": "zhangsan", "password": "password123"},
        )
        token = login_response.json()["data"]["access_token"]

        # Logout
        logout_response = await client.post(
            "/api/auth/logout",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert logout_response.status_code == 200
    data = logout_response.json()
    assert data["code"] == 200
    assert data["message"] == "success"


@pytest.mark.asyncio
async def test_logout_no_token(setup_database: Any) -> None:  # noqa: ARG001
    """Test logout without token."""
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as client:
        response = await client.post("/api/auth/logout")

    assert response.status_code == 401
