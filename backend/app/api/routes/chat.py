"""POST /chat: Ask Your Money (FR-001, FR-009 to FR-011). Rate limited per IP."""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.ai.agent import answer_question
from app.ai.llm import LlmClient
from app.api.deps import get_llm, rate_limit
from app.common.constants import CHAT_STORED_CONTENT_MAX, RATE_LIMIT_CHAT, RATE_LIMIT_LLM_GLOBAL
from app.common.dates import utc_now
from app.db import get_session
from app.models import ChatMessage, ChatRole
from app.schemas.chat import ChatIn, ChatOut

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chat"])


@router.post(
    "/chat",
    dependencies=[Depends(rate_limit("chat", RATE_LIMIT_CHAT, RATE_LIMIT_LLM_GLOBAL))],
)
def post_chat(
    body: ChatIn,
    session: Annotated[Session, Depends(get_session)],
    llm: Annotated[LlmClient, Depends(get_llm)],
) -> ChatOut:
    out = answer_question(session, llm, body, utc_now())
    store_exchange(session, body.question, out)
    return out


def store_exchange(session: Session, question: str, out: ChatOut) -> None:
    """Write-only log (FR-011). A storage failure is logged and never breaks the answer."""
    try:
        session.add_all(
            [
                ChatMessage(role=ChatRole.USER, content=question[:CHAT_STORED_CONTENT_MAX]),
                ChatMessage(
                    role=ChatRole.ASSISTANT,
                    content=out.answer[:CHAT_STORED_CONTENT_MAX],
                    outcome=out.outcome,
                ),
            ]
        )
        session.commit()
    except SQLAlchemyError as error:
        session.rollback()
        logger.exception("Could not store chat messages: %s", type(error).__name__)
