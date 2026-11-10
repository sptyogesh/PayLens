"""API models for GET /transactions. raw_json, flag_reason and origin are never exposed."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from app.common.types import TransactionKind, TransactionSource, TransactionStatus
from app.models import Transaction
from app.schemas.common import MoneyOut


class ClientRef(BaseModel):
    id: uuid.UUID
    name: str
    country: str | None


class TransactionOut(BaseModel):
    id: uuid.UUID
    paypal_transaction_id: str
    occurred_at: datetime
    client: ClientRef
    kind: TransactionKind
    status: TransactionStatus
    gross: MoneyOut
    fee: MoneyOut
    net: MoneyOut
    source: TransactionSource
    is_flagged: bool

    @classmethod
    def from_model(cls, row: Transaction) -> "TransactionOut":
        return cls(
            id=row.id,
            paypal_transaction_id=row.paypal_transaction_id,
            occurred_at=row.occurred_at,
            client=ClientRef(id=row.client.id, name=row.client.name, country=row.client.country),
            kind=row.kind,
            status=row.status,
            gross=MoneyOut.of(row.gross_amount, row.currency),
            fee=MoneyOut.of(row.fee_amount, row.currency),
            net=MoneyOut.of(row.net_amount, row.currency),
            source=row.source,
            is_flagged=row.is_flagged,
        )


class TransactionListOut(BaseModel):
    items: list[TransactionOut]
    total: int
    limit: int
    offset: int
