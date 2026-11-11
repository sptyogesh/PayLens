"""Global rematch: engine results → fira_documents, fira_matches, transactions.fira_status."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from app.common.dates import utc_now
from app.common.types import FiraStatus, TransactionKind, TransactionStatus
from app.fakes.fx_fake import FakeFxGateway
from app.models import FiraDocStatus, FiraDocument, FiraMatch, FiraMatchKind
from app.services.fira_rematch import delete_all_firas, rematch, safe_rematch
from app.services.refresh_service import safe_refresh
from tests.fixtures.rows import add_client, add_tx


def add_doc(session: Session, reference: str, amount: str, **overrides: object) -> FiraDocument:
    values: dict[str, object] = {
        "file_name": f"{reference}.pdf",
        "file_hash": reference.ljust(64, "0"),
        "extracted_json": {},
        "foreign_amount": Decimal(amount),
        "currency": "USD",
        "remittance_date": date(2026, 11, 8),
        "reference_no": reference,
        "status": FiraDocStatus.NO_MATCH,
        "uploaded_at": utc_now(),
    }
    values.update(overrides)
    doc = FiraDocument(**values)
    session.add(doc)
    session.flush()
    return doc


def test_statuses_matches_and_payment_badges(db_session: Session) -> None:
    client = add_client(db_session)
    exact = add_tx(db_session, client, "TX-1")
    review = add_tx(db_session, client, "TX-2", gross="500.00")
    missing = add_tx(db_session, client, "TX-3", gross="700.00")
    pending = add_tx(db_session, client, "TX-4", status=TransactionStatus.PENDING)
    refund = add_tx(db_session, client, "TX-5", kind=TransactionKind.REFUND)
    matched_doc = add_doc(db_session, "TX-1", "1000.00")
    review_doc = add_doc(db_session, "TX-2", "515.00")  # 3% off → 75
    rematch(db_session)
    assert (matched_doc.status, matched_doc.score, matched_doc.reason) == (
        FiraDocStatus.MATCHED,
        100,
        None,
    )
    assert (review_doc.status, review_doc.score) == (FiraDocStatus.NEEDS_REVIEW, 75)
    assert review_doc.reason == "Amount differs by more than 1%"
    assert exact.fira_status is FiraStatus.MATCHED
    assert review.fira_status is FiraStatus.NEEDS_REVIEW
    assert missing.fira_status is FiraStatus.MISSING
    assert pending.fira_status is None and refund.fira_status is None
    links = db_session.scalars(select(FiraMatch)).all()
    assert {(link.transaction_id, link.kind, link.match_score) for link in links} == {
        (exact.id, FiraMatchKind.DIRECT, 100),
        (review.id, FiraMatchKind.DIRECT, 75),
    }


def test_invalid_document_keeps_its_validation_reason(db_session: Session) -> None:
    add_tx(db_session, add_client(db_session), "TX-1")
    doc = add_doc(db_session, "TX-1", "1000.00", validation_reason="Missing currency")
    rematch(db_session)
    assert (doc.status, doc.score, doc.reason) == (
        FiraDocStatus.NEEDS_REVIEW,
        None,
        "Missing currency",
    )
    assert db_session.scalars(select(FiraMatch)).all() == []


def test_rematch_is_repeatable_and_follows_status_changes(db_session: Session) -> None:
    tx = add_tx(db_session, add_client(db_session), "TX-1")
    add_doc(db_session, "TX-1", "1000.00")
    rematch(db_session)
    rematch(db_session)
    assert len(db_session.scalars(select(FiraMatch)).all()) == 1
    tx.status = TransactionStatus.REVERSED
    rematch(db_session)
    assert tx.fira_status is None
    assert db_session.scalars(select(FiraMatch)).all() == []


def test_f11_two_firas_for_one_payment_higher_score_wins(db_session: Session) -> None:
    tx = add_tx(db_session, add_client(db_session), "TX-1")
    weaker = add_doc(db_session, "TX-1", "1030.00", file_hash="b" * 64)  # 75
    stronger = add_doc(db_session, "TX-1", "1000.00", file_hash="c" * 64)  # 100
    rematch(db_session)
    assert stronger.status is FiraDocStatus.MATCHED
    assert weaker.status is FiraDocStatus.NEEDS_REVIEW and weaker.reason
    assert tx.fira_status is FiraStatus.MATCHED


def test_delete_all_firas(db_session: Session) -> None:
    add_tx(db_session, add_client(db_session), "TX-1")
    add_doc(db_session, "TX-1", "1000.00")
    rematch(db_session)
    assert delete_all_firas(db_session) == 1
    assert db_session.scalars(select(FiraMatch)).all() == []


def test_safe_rematch_never_raises(session_factory: sessionmaker[Session]) -> None:
    def broken_factory() -> Session:
        raise RuntimeError("database down")

    assert safe_rematch(broken_factory) is None
    assert safe_rematch(session_factory) is not None


def test_safe_refresh_recalculates_leakage_then_rematches(
    session_factory: sessionmaker[Session],
) -> None:
    with session_factory() as session:
        tx = add_tx(session, add_client(session), "TX-1")
        session.commit()
    summary = safe_refresh(session_factory, FakeFxGateway())
    assert summary is not None and summary.calculated == 1
    with session_factory() as session:
        row = session.get(type(tx), tx.id)
        assert row is not None
        assert row.fira_status is FiraStatus.MISSING and row.total_leakage_inr is not None
