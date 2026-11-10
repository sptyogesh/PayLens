from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.common.errors import PaymentDeclinedError
from app.common.types import TransactionOrigin, TransactionSource
from app.fakes.paypal_fake import FakePayPalGateway
from app.models import Transaction
from app.schemas.pay import PayOrderIn
from app.services.checkout_service import capture_and_record, create_order


def order(amount: str = "50.00") -> PayOrderIn:
    return PayOrderIn(amount=amount, currency="USD", description="Logo design")


def test_success_records_one_paypal_sandbox_row(session_factory: sessionmaker[Session]) -> None:
    gateway = FakePayPalGateway()
    order_id = create_order(gateway, order())
    out = capture_and_record(gateway, session_factory, order_id)
    assert (out.recorded, out.status, out.gross.amount, out.gross.currency) == (
        True,
        "completed",
        "50.00",
        "USD",
    )
    with session_factory() as session:
        (stored,) = session.scalars(select(Transaction))
    assert stored.paypal_transaction_id == out.transaction_id
    assert (stored.source, stored.origin) == (
        TransactionSource.PAYPAL_SANDBOX,
        TransactionOrigin.CHECKOUT_CAPTURE,
    )


def test_declined_payment_stores_nothing(session_factory: sessionmaker[Session]) -> None:
    gateway = FakePayPalGateway()
    order_id = create_order(gateway, order("13.13"))
    with pytest.raises(PaymentDeclinedError):
        capture_and_record(gateway, session_factory, order_id)
    with session_factory() as session:
        assert session.scalars(select(Transaction)).first() is None


def test_db_failure_still_confirms_with_recorded_false() -> None:
    @contextmanager
    def broken_factory() -> Iterator[Session]:
        raise OperationalError("insert", {}, Exception("database down"))
        yield  # pragma: no cover

    gateway = FakePayPalGateway()
    out = capture_and_record(gateway, broken_factory, create_order(gateway, order()))  # type: ignore[arg-type]
    assert (out.recorded, out.status) == (False, "completed")
