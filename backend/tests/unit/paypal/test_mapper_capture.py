from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.common.types import TransactionKind, TransactionOrigin, TransactionStatus
from app.paypal.mapper import from_capture
from app.paypal.orders_api import parse_capture
from tests.fixtures.paypal.orders import capture_response

NOW = datetime(2026, 11, 10, 7, tzinfo=UTC)


def map_capture(**kwargs: Any) -> Any:
    return from_capture(parse_capture(capture_response(**kwargs)), NOW)


def test_capture_is_keyed_by_capture_id_with_positive_fee() -> None:
    dto = map_capture()
    assert (dto.paypal_transaction_id, dto.paypal_order_id) == (
        "3C679366HH908993F",
        "5O190127TN364715T",
    )
    assert (dto.gross, dto.fee, dto.net) == (Decimal("100.00"), Decimal("3.98"), Decimal("96.02"))
    assert (dto.kind, dto.origin, dto.status) == (
        TransactionKind.INCOME,
        TransactionOrigin.CHECKOUT_CAPTURE,
        TransactionStatus.COMPLETED,
    )
    assert dto.flag_reason is None
    assert (dto.payer.email, dto.payer.name, dto.payer.country) == (
        "ava.us@example.com",
        "Ava Stone",
        None,
    )


def test_negative_fee_is_normalised() -> None:
    assert map_capture(fee="-3.98").fee == Decimal("3.98")


def test_net_mismatch_is_flagged_not_fixed() -> None:
    dto = map_capture(net="90.00")
    assert (dto.net, dto.flag_reason) == (Decimal("96.02"), "NET_MISMATCH")


def test_missing_breakdown_is_flagged_with_zero_fee() -> None:
    dto = map_capture(fee=None, net=None)
    assert (dto.fee, dto.flag_reason) == (Decimal(0), "MISSING_BREAKDOWN")


def test_pending_capture_is_pending() -> None:
    assert map_capture(status="PENDING").status is TransactionStatus.PENDING
