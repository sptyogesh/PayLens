"""fira_documents / fira_matches constraints (004 data-model.md; needs PostgreSQL)."""

from decimal import Decimal

import pytest
from sqlalchemy import delete, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.dates import utc_now
from app.models import FiraDocStatus, FiraDocument, FiraMatch, FiraMatchKind, Transaction
from tests.fixtures.rows import add_client, add_tx


def make_doc(session: Session, file_hash: str = "a" * 64, **overrides: object) -> FiraDocument:
    values: dict[str, object] = {
        "file_name": "fira.pdf",
        "file_hash": file_hash,
        "extracted_json": {},
        "foreign_amount": Decimal("10.00"),
        "currency": "USD",
        "status": FiraDocStatus.NO_MATCH,
        "uploaded_at": utc_now(),
    }
    values.update(overrides)
    doc = FiraDocument(**values)
    session.add(doc)
    session.flush()
    return doc


def link(session: Session, doc: FiraDocument, tx: Transaction) -> None:
    session.add(
        FiraMatch(fira_id=doc.id, transaction_id=tx.id, match_score=100, kind=FiraMatchKind.DIRECT)
    )
    session.flush()


def test_enums_store_their_values(db_session: Session) -> None:
    doc = make_doc(db_session, status=FiraDocStatus.NEEDS_REVIEW)
    db_session.expire_all()
    stored = db_session.get(FiraDocument, doc.id)
    assert stored is not None and stored.status is FiraDocStatus.NEEDS_REVIEW


def test_file_hash_is_unique(db_session: Session) -> None:
    make_doc(db_session)
    with pytest.raises(IntegrityError):
        make_doc(db_session)


def test_foreign_amount_must_be_positive(db_session: Session) -> None:
    with pytest.raises(IntegrityError):
        make_doc(db_session, foreign_amount=Decimal("0.00"))


def test_score_range(db_session: Session) -> None:
    with pytest.raises(IntegrityError):
        make_doc(db_session, score=101)


def test_a_payment_is_linked_to_at_most_one_fira(db_session: Session) -> None:
    tx = add_tx(db_session, add_client(db_session), "TX-1")
    link(db_session, make_doc(db_session, "a" * 64), tx)
    with pytest.raises(IntegrityError):
        link(db_session, make_doc(db_session, "b" * 64), tx)


def test_deleting_a_fira_cascades_to_its_matches(db_session: Session) -> None:
    tx = add_tx(db_session, add_client(db_session), "TX-1")
    doc = make_doc(db_session)
    link(db_session, doc, tx)
    db_session.execute(delete(FiraDocument).where(FiraDocument.id == doc.id))
    assert db_session.scalar(select(func.count()).select_from(FiraMatch)) == 0


def test_deleting_a_transaction_cascades_to_its_match(db_session: Session) -> None:
    tx = add_tx(db_session, add_client(db_session), "TX-1")
    link(db_session, make_doc(db_session), tx)
    db_session.execute(delete(Transaction).where(Transaction.id == tx.id))
    assert db_session.scalar(select(func.count()).select_from(FiraMatch)) == 0
