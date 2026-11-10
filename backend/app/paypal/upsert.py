"""Idempotent storage of PayPal transactions and client linking (Principle VIII, FR-015, FR-017)."""

from dataclasses import replace
from typing import Literal

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.common.constants import UNKNOWN_CLIENT_NAME
from app.common.types import TransactionOrigin, TransactionSource
from app.models import Client, Transaction
from app.paypal.dto import PayerData, TransactionUpsert
from app.paypal.reconcile import reconcile

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
    """Copy PayPal-derived fields. Leakage is cleared when its inputs change (002 FR-020);
    FIRA columns are never touched."""
    before = row.leakage_inputs()
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
    if row.leakage_inputs() != before:
        row.clear_leakage()


def find_transaction(session: Session, paypal_transaction_id: str) -> Transaction | None:
    return session.scalar(
        select(Transaction).where(Transaction.paypal_transaction_id == paypal_transaction_id)
    )


def insert_transaction(session: Session, dto: TransactionUpsert, client: Client) -> UpsertResult:
    """Insert in a savepoint. If the same ID was stored concurrently (e.g. by /pay during a sync),
    only this insert is undone and the stored row is updated instead."""
    row = Transaction(paypal_transaction_id=dto.paypal_transaction_id, origin=dto.origin)
    apply(row, dto, client)
    try:
        with session.begin_nested():
            session.add(row)
    except IntegrityError:
        existing = find_transaction(session, dto.paypal_transaction_id)
        if existing is None:  # the conflict was something else; let the caller roll back
            raise
        apply(existing, dto, client)
        return "updated"
    return "added"


def upsert_transaction(session: Session, dto: TransactionUpsert) -> UpsertResult:
    client = upsert_client(session, dto.payer, dto.currency)
    existing = find_transaction(session, dto.paypal_transaction_id)
    if existing is None:
        existing, flag_reason = reconcile(session, dto)
        if existing is not None:
            existing.paypal_transaction_id = dto.paypal_transaction_id
        elif flag_reason is not None:
            dto = replace(dto, flag_reason=dto.flag_reason or flag_reason)
    if existing is not None:
        apply(existing, dto, client)
        return "updated"
    return insert_transaction(session, dto, client)
