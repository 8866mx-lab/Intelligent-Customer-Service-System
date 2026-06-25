"""Pydantic models for authentication."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request body."""

    username: str = Field(..., min_length=1, max_length=128)
    password: str = Field(..., min_length=1, max_length=128)


class UserPublic(BaseModel):
    """Public user information (without sensitive fields)."""

    id: int
    username: str


class LoginResponse(BaseModel):
    """Login response with access token and user info."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserPublic


class MeResponse(BaseModel):
    """Current user response."""

    id: int
    username: str
