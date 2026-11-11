"""Storage cases from the 004 review: strange extracted values are Needs review, never a 500 or a
false "duplicate"; a failed rematch is reported honestly (fake LLM; needs PostgreSQL)."""

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.fakes.llm_fake import FakeLlm
from app.models import FiraDocStatus, FiraDocument
from app.services import fira_service
from app.services.fira_service import MATCH_PENDING, upload
from tests.fixtures.fira import fira_pdf

Factory = sessionmaker[Session]


def only_document(factory: Factory) -> FiraDocument:
    with factory() as session:
        return session.scalars(select(FiraDocument)).one()


@pytest.mark.parametrize(
    ("overrides", "column"),
    [
        ({"foreign_amount": "0"}, "foreign_amount"),
        ({"foreign_amount": "-1.00"}, "foreign_amount"),
        ({"foreign_amount": "1000000000000000.00"}, "foreign_amount"),
        ({"currency": "US Dollar"}, "currency"),
        ({"rate": "0"}, "rate"),
    ],
)
def test_impossible_values_are_stored_empty_as_needs_review(
    session_factory: Factory, overrides: dict[str, str], column: str
) -> None:
    out = upload(session_factory, FakeLlm(), "odd.pdf", fira_pdf((), **overrides))
    assert (out.result.outcome, out.result.status) == ("stored", FiraDocStatus.NEEDS_REVIEW)
    document = only_document(session_factory)
    assert getattr(document, column) is None
    assert document.validation_reason


def test_long_texts_are_shortened_and_flagged(session_factory: Factory) -> None:
    out = upload(
        session_factory, FakeLlm(), "long.pdf", fira_pdf(purpose_code="P0802 – Software services")
    )
    assert (out.result.outcome, out.result.status) == ("stored", FiraDocStatus.NEEDS_REVIEW)
    document = only_document(session_factory)
    assert document.purpose_code == "P0802 – "[:8]
    assert "Purpose code is too long" in (document.validation_reason or "")


def test_failed_rematch_says_matching_will_run_again(
    session_factory: Factory, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(fira_service, "safe_rematch", lambda _factory: None)
    out = upload(session_factory, FakeLlm(), "fira.pdf", fira_pdf())
    assert (out.result.outcome, out.result.message, out.result.status) == (
        "stored",
        MATCH_PENDING,
        None,
    )
