"""Shared builders for clients and transactions in DB tests (002+)."""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.common.types import (
    TransactionKind,
    TransactionOrigin,
    TransactionSource,
    TransactionStatus,
)
from app.models import Client, Transaction

FRIDAY_NOON = datetime(2026, 11, 6, 6, 30, tzinfo=UTC)  # 12:00 IST


def add_client(session: Session, name: str = "Ava Stone", currency: str = "USD") -> Client:
    email = f"{name.lower().replace(' ', '.')}@example.com"
    client = Client(
        name=name, email=email, currency=currency, source=TransactionSource.PAYPAL_SANDBOX
    )
    session.add(client)
    session.flush()
    return client


def add_tx(session: Session, client: Client, tx_id: str, **overrides: object) -> Transaction:
    gross = Decimal(str(overrides.pop("gross", "1000.00")))
    fee = Decimal(str(overrides.pop("fee", "44.00")))
    values: dict[str, object] = {
        "paypal_transaction_id": tx_id,
        "client_id": client.id,
        "occurred_at": FRIDAY_NOON,
        "kind": TransactionKind.INCOME,
        "status": TransactionStatus.COMPLETED,
        "gross_amount": gross,
        "fee_amount": fee,
        "net_amount": gross - fee,
        "currency": client.currency,
        "source": TransactionSource.PAYPAL_SANDBOX,
        "origin": TransactionOrigin.TRANSACTION_SEARCH,
    }
    values.update(overrides)
    row = Transaction(**values)
    session.add(row)
    session.flush()
    return row
