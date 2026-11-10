"""Idempotent demo seed and reset (FR-040, FR-041). Only touches source=demo_seed rows."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any, cast

from sqlalchemy import CursorResult, delete, func, select
from sqlalchemy.orm import Session

from app.common.constants import SEED_FEE_FIXED, SEED_FEE_PERCENT
from app.common.money import round_money
from app.common.types import (
    TransactionKind,
    TransactionOrigin,
    TransactionSource,
    TransactionStatus,
)
from app.models import Client, Transaction

SEED = TransactionSource.DEMO_SEED
ClientSeed = tuple[str, str, str, str]


def seed_fee(gross: Decimal, currency: str) -> Decimal:
    return round_money(gross * SEED_FEE_PERCENT + SEED_FEE_FIXED[currency])


def months_before(now: datetime, months: int, day: int) -> datetime:
    """Noon UTC on `day` of the month that is `months` before the current month."""
    index = now.year * 12 + (now.month - 1) - months
    return datetime(index // 12, index % 12 + 1, day, 12, tzinfo=UTC)


def upsert_seed_client(session: Session, seed: ClientSeed) -> Client:
    name, email, country, currency = seed
    client = session.scalar(select(Client).where(Client.email == email))
    if client is None:
        client = Client(name=name, email=email, country=country, currency=currency, source=SEED)
        session.add(client)
        session.flush()
    return client


def upsert_seed_transaction(
    session: Session, seed_id: str, client: Client, when: datetime, gross: Decimal
) -> bool:
    """Insert or refresh one seed row. Returns True when it was newly added."""
    row = session.scalar(select(Transaction).where(Transaction.paypal_transaction_id == seed_id))
    added = row is None
    if row is None:
        row = Transaction(paypal_transaction_id=seed_id, origin=TransactionOrigin.SEED)
        session.add(row)
    fee = seed_fee(gross, client.currency)
    before = row.leakage_inputs()
    row.client_id, row.occurred_at, row.currency = client.id, when, client.currency
    row.kind, row.status, row.source = TransactionKind.INCOME, TransactionStatus.COMPLETED, SEED
    row.gross_amount, row.fee_amount, row.net_amount = gross, fee, gross - fee
    if row.leakage_inputs() != before:
        row.clear_leakage()
    return added


def reset_seed(session: Session) -> tuple[int, int]:
    """Delete demo_seed transactions, then seed clients left without transactions."""
    removed = session.execute(delete(Transaction).where(Transaction.source == SEED))
    in_use = select(Transaction.client_id).where(Transaction.client_id == Client.id).exists()
    clients = session.execute(delete(Client).where(Client.source == SEED, ~in_use))
    return rowcount(removed), rowcount(clients)


def rowcount(result: object) -> int:
    """DELETE statements return a CursorResult; its rowcount is the number of rows removed."""
    return cast("CursorResult[Any]", result).rowcount


def count_seed_rows(session: Session) -> int:
    return session.scalar(select(func.count()).where(Transaction.source == SEED)) or 0
