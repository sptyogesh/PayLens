"""Database constraints from data-model.md (needs PostgreSQL)."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.types import (
    TransactionKind,
    TransactionOrigin,
    TransactionSource,
    TransactionStatus,
)
from app.models import Client, Transaction


def make_client(
    session: Session, email: str | None = "a@example.com", unknown: bool = False
) -> Client:
    client = Client(
        name="A",
        email=email,
        currency="USD",
        is_unknown=unknown,
        source=TransactionSource.PAYPAL_SANDBOX,
    )
    session.add(client)
    session.flush()
    return client


def make_tx(client: Client, tx_id: str = "TX1", **overrides: object) -> Transaction:
    values: dict[str, object] = {
        "paypal_transaction_id": tx_id,
        "client_id": client.id,
        "occurred_at": datetime(2026, 11, 1, tzinfo=UTC),
        "kind": TransactionKind.INCOME,
        "status": TransactionStatus.COMPLETED,
        "gross_amount": Decimal("100.00"),
        "fee_amount": Decimal("3.98"),
        "net_amount": Decimal("96.02"),
        "currency": "USD",
        "source": TransactionSource.PAYPAL_SANDBOX,
        "origin": TransactionOrigin.TRANSACTION_SEARCH,
    }
    values.update(overrides)
    return Transaction(**values)


def assert_rejected(session: Session, row: object) -> None:
    session.add(row)
    with pytest.raises(IntegrityError):
        session.flush()
    session.rollback()


def test_valid_transaction_is_stored(db_session: Session) -> None:
    db_session.add(make_tx(make_client(db_session)))
    db_session.flush()


def test_duplicate_paypal_transaction_id_is_rejected(db_session: Session) -> None:
    client = make_client(db_session)
    db_session.add(make_tx(client))
    db_session.flush()
    assert_rejected(db_session, make_tx(client))


def test_negative_fee_is_rejected(db_session: Session) -> None:
    client = make_client(db_session)
    assert_rejected(
        db_session, make_tx(client, fee_amount=Decimal("-1.00"), net_amount=Decimal("101.00"))
    )


def test_net_must_equal_gross_minus_fee(db_session: Session) -> None:
    assert_rejected(db_session, make_tx(make_client(db_session), net_amount=Decimal("96.00")))


def test_only_one_unknown_client(db_session: Session) -> None:
    make_client(db_session, email=None, unknown=True)
    assert_rejected(
        db_session,
        Client(
            name="U2",
            email=None,
            currency="USD",
            is_unknown=True,
            source=TransactionSource.PAYPAL_SANDBOX,
        ),
    )
