"""Conversation Pydantic models for request/response validation."""

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """会话创建请求模型."""

    title: str | None = Field(default="新对话", max_length=255)


class MessageSend(BaseModel):
    """发送消息请求模型."""

    content: str = Field(..., min_length=1, max_length=2000)
