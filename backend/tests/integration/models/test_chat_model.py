"""chat_messages table (data-model.md, needs PostgreSQL)."""

import pytest
from sqlalchemy import select
from sqlalchemy.exc import DataError, IntegrityError
from sqlalchemy.orm import Session

from app.models import ChatMessage, ChatRole


def test_messages_are_stored_with_role_outcome_and_time(db_session: Session) -> None:
    db_session.add_all(
        [
            ChatMessage(role=ChatRole.USER, content="FX loss last quarter?"),
            ChatMessage(role=ChatRole.ASSISTANT, content="₹38000.00", outcome="answered"),
        ]
    )
    db_session.flush()
    rows = db_session.scalars(select(ChatMessage).order_by(ChatMessage.role)).all()
    assert [(r.role, r.outcome) for r in rows] == [
        (ChatRole.USER, None),
        (ChatRole.ASSISTANT, "answered"),
    ]
    assert all(r.created_at is not None and r.id is not None for r in rows)


def test_content_is_required(db_session: Session) -> None:
    db_session.add(ChatMessage(role=ChatRole.USER))
    with pytest.raises(IntegrityError):
        db_session.flush()


def test_outcome_longer_than_16_characters_is_rejected(db_session: Session) -> None:
    db_session.add(ChatMessage(role=ChatRole.ASSISTANT, content="x", outcome="x" * 17))
    with pytest.raises(DataError):
        db_session.flush()
