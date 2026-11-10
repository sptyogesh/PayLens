"""Idempotent storage of PayPal transactions and client linking (Principle VIII, FR-015, FR-017)."""

from typing import Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.constants import UNKNOWN_CLIENT_NAME
from app.common.types import TransactionOrigin, TransactionSource
from app.models import Client, Transaction
from app.paypal.dto import PayerData, TransactionUpsert

UpsertResult = Literal["added", "updated"]


def find_client(session: Session, payer: PayerData) -> Client | None:
    if payer.email is None:
        return session.scalar(select(Client).where(Client.is_unknown))
    return session.scalar(select(Client).where(Client.email == payer.email))


def upsert_client(session: Session, payer: PayerData, currency: str) -> Client:
    """Find the client by email (or the single unknown client); create it the first time."""
    client = find_client(session, payer)
    if client is None:
        client = Client(
            name=(payer.name or UNKNOWN_CLIENT_NAME) if payer.email else UNKNOWN_CLIENT_NAME,
            email=payer.email,
            country=payer.country if payer.email else None,
            currency=currency,
            is_unknown=payer.email is None,
            source=TransactionSource.PAYPAL_SANDBOX,
        )
        try:
            with session.begin_nested():
                session.add(client)
        except IntegrityError:  # created concurrently (e.g. by /pay); use that row
            client = find_client(session, payer)
            assert client is not None  # noqa: S101 - the conflicting row must exist
    elif client.country is None and payer.country and not client.is_unknown:
        client.country = payer.country
    return client


def apply(row: Transaction, dto: TransactionUpsert, client: Client) -> None:
    """Copy PayPal-derived fields only. Never touches the 002/004 leakage and FIRA columns."""
    row.client_id = client.id
    row.occurred_at = dto.occurred_at
    row.event_code = dto.event_code or row.event_code
    row.kind = dto.kind
    row.status = dto.status
    row.gross_amount = dto.gross
    row.fee_amount = dto.fee
    row.net_amount = dto.net
    row.currency = dto.currency
    row.source = TransactionSource.PAYPAL_SANDBOX
    row.is_flagged = dto.flag_reason is not None
    row.flag_reason = dto.flag_reason
    row.raw_json = dto.raw_json
    row.paypal_order_id = dto.paypal_order_id or row.paypal_order_id
    if row.origin is not TransactionOrigin.TRANSACTION_SEARCH:
        row.origin = dto.origin


def upsert_transaction(session: Session, dto: TransactionUpsert) -> UpsertResult:
    client = upsert_client(session, dto.payer, dto.currency)
    existing = session.scalar(
        select(Transaction).where(Transaction.paypal_transaction_id == dto.paypal_transaction_id)
    )
    if existing is not None:
        apply(existing, dto, client)
        return "updated"
    row = Transaction(paypal_transaction_id=dto.paypal_transaction_id, origin=dto.origin)
    apply(row, dto, client)
    session.add(row)
    session.flush()
    return "added"
