from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.common.types import TransactionStatus
from app.models import Client, Transaction
from app.paypal.mapper import from_search_row
from app.paypal.schemas import TransactionDetail
from app.paypal.upsert import upsert_transaction
from tests.fixtures.paypal.search import row


def dto(data: dict[str, Any]) -> Any:
    return from_search_row(TransactionDetail.model_validate(data), data)


def count(session: Session, model: type[Any]) -> int:
    return session.scalar(select(func.count()).select_from(model)) or 0


def test_p3_same_transaction_twice_gives_one_row(db_session: Session) -> None:
    assert upsert_transaction(db_session, dto(row("A"))) == "added"
    assert upsert_transaction(db_session, dto(row("A"))) == "updated"
    assert count(db_session, Transaction) == 1


def test_pending_then_completed_updates_the_row(db_session: Session) -> None:
    upsert_transaction(db_session, dto(row("A", status="P")))
    upsert_transaction(db_session, dto(row("A", status="S", fee="-4.10")))
    stored = db_session.scalars(select(Transaction)).one()
    assert stored.status is TransactionStatus.COMPLETED
    assert (stored.fee_amount, stored.net_amount) == (Decimal("4.10"), Decimal("95.90"))


def test_update_never_touches_leakage_columns(db_session: Session) -> None:
    upsert_transaction(db_session, dto(row("A")))
    stored = db_session.scalars(select(Transaction)).one()
    stored.fee_loss_inr = Decimal("330.00")
    upsert_transaction(db_session, dto(row("A")))
    assert stored.fee_loss_inr == Decimal("330.00")


def test_clients_are_linked_by_email(db_session: Session) -> None:
    upsert_transaction(db_session, dto(row("A", email="Ava@Example.com")))
    upsert_transaction(db_session, dto(row("B", email="ava@example.com")))
    upsert_transaction(db_session, dto(row("C", email="ben@example.com")))
    assert count(db_session, Client) == 2
    ava = db_session.scalars(select(Client).where(Client.email == "ava@example.com")).one()
    assert (ava.name, ava.country, ava.currency) == ("Ava Client", "US", "USD")


def test_missing_email_links_to_single_unknown_client(db_session: Session) -> None:
    upsert_transaction(db_session, dto(row("A", email=None)))
    upsert_transaction(db_session, dto(row("B", email=None)))
    unknown = db_session.scalars(select(Client)).one()
    assert (unknown.is_unknown, unknown.name, unknown.email) == (True, "Unknown client", None)
