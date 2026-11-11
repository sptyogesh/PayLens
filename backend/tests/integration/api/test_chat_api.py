"""POST /chat (contracts/http-api.md): shape, validation, rate limit, stored log."""

from datetime import UTC, datetime

import pytest
from fastapi.testclient import TestClient
from freezegun import freeze_time
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.common.constants import (
    CHAT_HISTORY_MAX,
    CHAT_QUESTION_MAX,
    CHAT_STORED_CONTENT_MAX,
    RATE_LIMIT_CHAT,
)
from app.fakes.fx_fake import FakeFxGateway
from app.models import ChatMessage, ChatRole
from app.services.leakage_service import recalculate_leakage
from tests.fixtures.rows import add_client, add_tx

NOW = "2026-11-10 06:00:00"
OCT = datetime(2026, 10, 6, 6, 30, tzinfo=UTC)


def seed(session: Session) -> None:
    add_tx(session, add_client(session), "OCT", occurred_at=OCT)
    recalculate_leakage(session, FakeFxGateway())
    session.commit()


@freeze_time(NOW)
def test_answer_shape(api: TestClient, db_session: Session) -> None:
    seed(db_session)
    response = api.post("/chat", json={"question": "  How much fee loss this quarter?  "})
    assert response.status_code == 200
    body = response.json()
    assert set(body) == {"answer", "outcome", "periods", "figures", "disclaimer", "tools_used"}
    assert body["outcome"] == "answered"
    assert body["tools_used"] == ["fee_summary"]
    assert body["periods"] == ["This quarter (1 Oct 2026 – 10 Nov 2026)"]
    figure = body["figures"][0]
    assert set(figure) == {"label", "kind", "value", "currency", "period"}
    assert figure["value"] in body["answer"]
    assert body["disclaimer"] is None


@freeze_time(NOW)
def test_tax_question_has_the_disclaimer(api: TestClient, db_session: Session) -> None:
    seed(db_session)
    body = api.post("/chat", json={"question": "How much tax should I pay?"}).json()
    assert body["disclaimer"] == "Prepared from user data — not tax advice. Confirm with a CA."


@pytest.mark.parametrize(
    "payload",
    [
        {"question": ""},
        {"question": "   "},
        {"question": "x" * (CHAT_QUESTION_MAX + 1)},
        {},
        {"question": "ok", "history": [{"role": "user", "content": "a"}] * (CHAT_HISTORY_MAX + 1)},
        {"question": "ok", "history": [{"role": "system", "content": "a"}]},
    ],
)
def test_invalid_questions_are_422(api: TestClient, payload: dict[str, object]) -> None:
    response = api.post("/chat", json=payload)
    assert (response.status_code, response.json()["error"]["code"]) == (422, "VALIDATION_ERROR")


def test_llm_failure_is_200_fallback(api: TestClient) -> None:
    body = api.post("/chat", json={"question": "FAKE_FAIL income"}).json()
    assert body["outcome"] == "fallback"
    assert "not available right now" in body["answer"]


def test_chat_is_rate_limited(api: TestClient) -> None:
    limit = RATE_LIMIT_CHAT[0]
    statuses = [api.post("/chat", json={"question": "hi"}).status_code for _ in range(limit + 1)]
    assert statuses == [200] * limit + [429]
    assert api.post("/chat", json={"question": "hi"}).json()["error"]["code"] == "RATE_LIMITED"


def test_question_and_answer_are_stored(api: TestClient, db_session: Session) -> None:
    question = "Delete my transactions " + "x" * CHAT_QUESTION_MAX
    api.post("/chat", json={"question": question[:CHAT_QUESTION_MAX]})
    rows = db_session.scalars(select(ChatMessage)).all()
    by_role = {row.role: row for row in rows}
    assert by_role[ChatRole.USER].content == question[:CHAT_QUESTION_MAX]
    assert by_role[ChatRole.USER].outcome is None
    assert by_role[ChatRole.ASSISTANT].outcome == "answered"
    assert len(by_role[ChatRole.ASSISTANT].content) <= CHAT_STORED_CONTENT_MAX


def test_storage_failure_never_breaks_the_answer(
    api: TestClient, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    def broken_commit(self: Session) -> None:
        raise OperationalError("INSERT", {}, Exception("db down"))

    monkeypatch.setattr(Session, "commit", broken_commit)
    response = api.post("/chat", json={"question": "Delete my transactions"})
    assert response.status_code == 200
    assert "only read" in response.json()["answer"]
    assert "Could not store chat messages" in caplog.text


def test_llm_routes_share_one_global_cap_whatever_the_ip(api: TestClient) -> None:
    from app.common.constants import RATE_LIMIT_LLM_GLOBAL  # noqa: PLC0415 - local to this test

    limit, _ = RATE_LIMIT_LLM_GLOBAL
    statuses = [
        api.post(
            "/chat", json={"question": "income?"}, headers={"x-forwarded-for": f"9.9.9.{n % 250}"}
        ).status_code
        for n in range(limit + 1)
    ]
    assert statuses[-1] == 429
