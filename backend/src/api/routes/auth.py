"""Authentication routes for login, logout, and user info."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.deps import get_current_user
from src.core.security import create_access_token, verify_password
from src.db.models import User
from src.db.session import get_db
from src.models.auth import LoginRequest, LoginResponse, MeResponse, UserPublic

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login")
async def login(
    credentials: LoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> dict:
    """User login with username and password.

    Returns JWT access token on success.

    Args:
        credentials: Login credentials (username and password)
        db: Database session

    Returns:
        Response with code 200 and access token data

    Raises:
        HTTPException: 401 if credentials are invalid
    """
    # Query user by username
    result = await db.execute(select(User).where(User.username == credentials.username))
    user = result.scalar_one_or_none()

    # Verify user exists and password is correct
    if user is None or not verify_password(credentials.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": 1001, "message": "用户名或密码错误", "data": None},
        )

    # Create access token
    access_token = create_access_token(data={"sub": str(user.id)})

    # Build response
    response_data = LoginResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=86400,  # 24 hours in seconds
        user=UserPublic(id=user.id, username=user.username),
    )

    return {"code": 200, "message": "success", "data": response_data.model_dump()}


@router.post("/logout")
async def logout(
    current_user: Annotated[User, Depends(get_current_user)],  # noqa: ARG001
) -> dict:
    """User logout.

    This is a client-side logout - the server doesn't maintain a token blacklist.
    The client should remove the token from storage.

    Args:
        current_user: Current authenticated user (verified by dependency)

    Returns:
        Response with code 200
    """
    return {"code": 200, "message": "success", "data": None}


@router.get("/me")
async def get_me(
    current_user: Annotated[User, Depends(get_current_user)],
) -> dict:
    """Get current authenticated user information.

    Args:
        current_user: Current authenticated user (verified by dependency)

    Returns:
        Response with code 200 and user data
    """
    response_data = MeResponse(id=current_user.id, username=current_user.username)

    return {"code": 200, "message": "success", "data": response_data.model_dump()}
