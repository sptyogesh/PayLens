"""Map PayPal records to TransactionUpsert.

Fees become positive and net = gross − fee, computed in code (research R3).
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from app.common.money import parse_money
from app.common.types import TransactionKind, TransactionOrigin, TransactionStatus
from app.paypal.classify import classify, map_status
from app.paypal.dto import PayerData, TransactionUpsert
from app.paypal.orders_api import CaptureResult
from app.paypal.schemas import PayerInfo, TransactionDetail, TransactionInfo
from app.paypal.schemas_orders import Capture, OrderPayer

ZERO = Decimal("0.00")


def payer_from_search(info: PayerInfo | None) -> PayerData:
    if info is None:
        return PayerData(email=None, name=None, country=None)
    email = info.email_address.strip().lower() if info.email_address else None
    return PayerData(email=email, name=payer_name(info, email), country=info.country_code)


def payer_name(info: PayerInfo, email: str | None) -> str | None:
    name = info.payer_name
    if name is not None:
        if name.full_name or name.alternate_full_name:
            return name.full_name or name.alternate_full_name
        parts = [part for part in (name.given_name, name.surname) if part]
        if parts:
            return " ".join(parts)
    return email


def fee_of(info: TransactionInfo, currency: str) -> tuple[Decimal, str | None]:
    """Positive fee in the transaction currency, plus a flag reason if it can't be trusted."""
    if info.fee_amount is None:
        return ZERO, None
    if info.fee_amount.currency_code != currency:
        return ZERO, "FEE_CURRENCY_MISMATCH"
    return abs(parse_money(info.fee_amount.value)), None


def from_search_row(detail: TransactionDetail, raw: dict[str, Any]) -> TransactionUpsert:
    info = detail.transaction_info
    amount = parse_money(info.transaction_amount.value)
    currency = info.transaction_amount.currency_code
    fee, flag_reason = fee_of(info, currency)
    status = map_status(info.transaction_status)
    if status is None:
        status, flag_reason = TransactionStatus.PENDING, flag_reason or "UNKNOWN_STATUS"
    gross = abs(amount)
    return TransactionUpsert(
        paypal_transaction_id=info.transaction_id,
        occurred_at=info.transaction_initiation_date,
        event_code=info.transaction_event_code,
        kind=classify(info.transaction_event_code, amount),
        status=status,
        gross=gross,
        fee=fee,
        net=gross - fee,
        currency=currency,
        origin=TransactionOrigin.TRANSACTION_SEARCH,
        payer=payer_from_search(detail.payer_info),
        raw_json=raw,
        flag_reason=flag_reason,
    )


def payer_from_order(payer: OrderPayer | None) -> PayerData:
    if payer is None:
        return PayerData(email=None, name=None, country=None)
    email = payer.email_address.strip().lower() if payer.email_address else None
    parts = [p for p in (payer.name.given_name, payer.name.surname) if p] if payer.name else []
    country = payer.address.country_code if payer.address else None
    return PayerData(email=email, name=" ".join(parts) or email, country=country)


def amounts_from_capture(capture: Capture) -> tuple[Decimal, Decimal, str | None]:
    """Gross and positive fee from the breakdown; flags a missing breakdown or a net mismatch."""
    breakdown = capture.seller_receivable_breakdown
    if breakdown is None or breakdown.paypal_fee is None:
        return parse_money(capture.amount.value), ZERO, "MISSING_BREAKDOWN"
    gross = parse_money(breakdown.gross_amount.value)
    fee = abs(parse_money(breakdown.paypal_fee.value))
    net = breakdown.net_amount
    mismatch = net is not None and parse_money(net.value) != gross - fee
    return gross, fee, "NET_MISMATCH" if mismatch else None


def from_capture(result: CaptureResult, now: datetime) -> TransactionUpsert:
    """A /pay capture, keyed by the capture ID (research R1)."""
    capture = result.response.first_capture()
    if capture is None:
        raise ValueError("capture response has no capture")
    gross, fee, flag_reason = amounts_from_capture(capture)
    status = (
        TransactionStatus.PENDING if capture.status == "PENDING" else TransactionStatus.COMPLETED
    )
    return TransactionUpsert(
        paypal_transaction_id=capture.id,
        paypal_order_id=result.response.id,
        occurred_at=capture.create_time or now,
        event_code=None,
        kind=TransactionKind.INCOME,
        status=status,
        gross=gross,
        fee=fee,
        net=gross - fee,
        currency=capture.amount.currency_code,
        origin=TransactionOrigin.CHECKOUT_CAPTURE,
        payer=payer_from_order(result.response.payer),
        raw_json=result.raw,
        flag_reason=flag_reason,
    )
