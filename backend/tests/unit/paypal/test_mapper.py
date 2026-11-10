from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from app.common.types import TransactionKind, TransactionStatus
from app.paypal.mapper import from_search_row
from app.paypal.schemas import TransactionDetail
from tests.fixtures.paypal.search import row


def map_row(data: dict[str, Any]) -> Any:
    return from_search_row(TransactionDetail.model_validate(data), data)


def test_p7_negative_fee_is_stored_positive_and_net_is_computed() -> None:
    dto = map_row(row("A", amount="100.00", fee="-3.98"))
    assert (dto.gross, dto.fee, dto.net) == (Decimal("100.00"), Decimal("3.98"), Decimal("96.02"))
    assert dto.kind is TransactionKind.INCOME
    assert dto.status is TransactionStatus.COMPLETED


def test_positive_fee_is_kept_positive() -> None:
    assert map_row(row("A", fee="3.98")).fee == Decimal("3.98")


def test_missing_fee_is_zero_in_transaction_currency() -> None:
    dto = map_row(row("A", fee=None, currency="GBP"))
    assert (dto.fee, dto.currency, dto.net) == (Decimal(0), "GBP", Decimal("100.00"))


def test_paypal_date_offset_and_raw_json_are_kept() -> None:
    data = row("A", date="2026-11-01T10:00:00+0530")
    dto = map_row(data)
    assert dto.occurred_at == datetime(2026, 11, 1, 4, 30, tzinfo=UTC)
    assert dto.raw_json == data


def test_outgoing_amount_is_stored_as_positive_gross() -> None:
    dto = map_row(row("A", amount="-50.00", fee=None, code="T0400"))
    assert (dto.kind, dto.gross) == (TransactionKind.WITHDRAWAL, Decimal("50.00"))


def test_payer_email_lowercased_and_name_fallbacks() -> None:
    dto = map_row(row("A", email="Ava.Client@Example.COM"))
    assert (dto.payer.email, dto.payer.name, dto.payer.country) == (
        "ava.client@example.com",
        "Ava Client",
        "US",
    )
    data = row("B")
    data["payer_info"]["payer_name"] = {"full_name": "Acme Ltd"}
    assert map_row(data).payer.name == "Acme Ltd"
    data["payer_info"].pop("payer_name")
    assert map_row(data).payer.name == "client.us@example.com"


def test_missing_payer_email_and_unknown_status_are_handled() -> None:
    data = row("A", email=None, status="Z")
    dto = map_row(data)
    assert dto.payer.email is None
    assert dto.status is TransactionStatus.PENDING
    assert dto.flag_reason == "UNKNOWN_STATUS"


def test_fee_in_other_currency_is_flagged() -> None:
    data = row("A")
    data["transaction_info"]["fee_amount"]["currency_code"] = "EUR"
    dto = map_row(data)
    assert (dto.fee, dto.flag_reason) == (Decimal(0), "FEE_CURRENCY_MISMATCH")
