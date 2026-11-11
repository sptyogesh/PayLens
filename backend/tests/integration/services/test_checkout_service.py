from collections.abc import Iterator
from contextlib import contextmanager

import pytest
from sqlalchemy import select
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, sessionmaker

from app.common.errors import PaymentDeclinedError
from app.common.types import TransactionOrigin, TransactionSource
from app.fakes.fx_fake import FakeFxGateway
from app.fakes.paypal_fake import FakePayPalGateway
from app.models import Transaction
from app.schemas.pay import PayOrderIn
from app.services.checkout_service import capture_and_record, create_order


def order(amount: str = "50.00") -> PayOrderIn:
    return PayOrderIn(amount=amount, currency="USD", description="Logo design")


def test_success_records_one_paypal_sandbox_row(session_factory: sessionmaker[Session]) -> None:
    gateway = FakePayPalGateway()
    order_id = create_order(gateway, order())
    out = capture_and_record(gateway, session_factory, order_id, FakeFxGateway())
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
    assert stored.total_leakage_inr is not None  # FR-020: leakage right after /pay


def test_fx_outage_does_not_change_the_payment_result(
    session_factory: sessionmaker[Session],
) -> None:
    gateway = FakePayPalGateway()
    order_id = create_order(gateway, order())
    out = capture_and_record(gateway, session_factory, order_id, FakeFxGateway(unavailable=True))
    assert (out.recorded, out.status) == (True, "completed")
    with session_factory() as session:
        (stored,) = session.scalars(select(Transaction))
    assert stored.total_leakage_inr is None


def test_declined_payment_stores_nothing(session_factory: sessionmaker[Session]) -> None:
    gateway = FakePayPalGateway()
    order_id = create_order(gateway, order("13.13"))
    with pytest.raises(PaymentDeclinedError):
        capture_and_record(gateway, session_factory, order_id, FakeFxGateway())
    with session_factory() as session:
        assert session.scalars(select(Transaction)).first() is None


def test_db_failure_still_confirms_with_recorded_false() -> None:
    @contextmanager
    def broken_factory() -> Iterator[Session]:
        raise OperationalError("insert", {}, Exception("database down"))
        yield  # pragma: no cover

    gateway = FakePayPalGateway()
    order_id = create_order(gateway, order())
    # Ignore on the next line: a context-manager factory that fails stands in for a sessionmaker
    out = capture_and_record(gateway, broken_factory, order_id, FakeFxGateway())  # type: ignore[arg-type]
    assert (out.recorded, out.status) == (False, "completed")
