"""Research R1 fallback: link a Transaction Search row to an earlier /pay capture."""

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.types import TransactionOrigin
from app.models import Transaction
from app.paypal.mapper import from_capture, from_search_row
from app.paypal.orders_api import parse_capture
from app.paypal.schemas import TransactionDetail
from app.paypal.upsert import upsert_transaction
from tests.fixtures.paypal.orders import capture_response
from tests.fixtures.paypal.search import row

NOW = datetime(2026, 11, 10, 7, tzinfo=UTC)


def capture(capture_id: str = "CAP1") -> Any:
    return from_capture(parse_capture(capture_response(capture_id=capture_id)), NOW)


def search(tx_id: str, date: str = "2026-11-10T06:31:00+0000") -> Any:
    data = row(tx_id, fee="-3.98", email="ava.us@example.com", date=date)
    return from_search_row(TransactionDetail.model_validate(data), data)


def rows(session: Session) -> list[Transaction]:
    return list(session.scalars(select(Transaction).order_by(Transaction.paypal_transaction_id)))


def test_same_id_updates_instead_of_duplicating(db_session: Session) -> None:
    upsert_transaction(db_session, capture("SAMEID"))
    assert upsert_transaction(db_session, search("SAMEID")) == "updated"
    (stored,) = rows(db_session)
    assert stored.origin is TransactionOrigin.TRANSACTION_SEARCH
    assert stored.paypal_order_id == "5O190127TN364715T"


def test_different_id_with_one_candidate_is_rekeyed(db_session: Session) -> None:
    upsert_transaction(db_session, capture("CAP1"))
    assert upsert_transaction(db_session, search("SEARCH1")) == "updated"
    (stored,) = rows(db_session)
    assert (stored.paypal_transaction_id, stored.origin) == (
        "SEARCH1",
        TransactionOrigin.TRANSACTION_SEARCH,
    )


def test_two_candidates_insert_and_flag(db_session: Session) -> None:
    upsert_transaction(db_session, capture("CAP1"))
    upsert_transaction(db_session, capture("CAP2"))
    assert upsert_transaction(db_session, search("SEARCH1")) == "added"
    added = next(r for r in rows(db_session) if r.paypal_transaction_id == "SEARCH1")
    assert (added.is_flagged, added.flag_reason) == (True, "AMBIGUOUS_RECONCILE")


def test_outside_window_inserts_new_row(db_session: Session) -> None:
    upsert_transaction(db_session, capture("CAP1"))
    assert (
        upsert_transaction(db_session, search("SEARCH1", date="2026-11-20T06:30:00+0000"))
        == "added"
    )
    assert len(rows(db_session)) == 2
