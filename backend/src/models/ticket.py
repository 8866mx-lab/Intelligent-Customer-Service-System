"""Ticket Pydantic models."""

from typing import Literal

from pydantic import BaseModel, Field, model_validator

TicketCategoryValue = Literal["it", "hr", "finance", "admin", "other"]


class TicketUpdate(BaseModel):
    """工单更新请求（归类或结束）."""

    category: TicketCategoryValue | None = None
    status: Literal["completed"] | None = None

    @model_validator(mode="after")
    def validate_payload(self) -> "TicketUpdate":
        if self.category is None and self.status is None:
            raise ValueError("请提供 category 或 status")
        return self
