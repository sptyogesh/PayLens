"""chat_messages table: write-only log of chat questions and answers (data-model.md, FR-011)."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, IdMixin, pg_enum

OUTCOME_LENGTH = 16


class ChatRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class ChatMessage(IdMixin, Base):
    __tablename__ = "chat_messages"

    role: Mapped[ChatRole] = mapped_column(pg_enum(ChatRole, "chat_role"))
    content: Mapped[str] = mapped_column(Text)
    outcome: Mapped[str | None] = mapped_column(String(OUTCOME_LENGTH))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
