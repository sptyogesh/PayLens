"""Plain data passed from the mappers to the upsert step (no ORM, no HTTP)."""

from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any

from app.common.types import TransactionKind, TransactionOrigin, TransactionStatus
from app.paypal.schemas import TransactionDetail


@dataclass(frozen=True)
class PayerData:
    email: str | None
    name: str | None
    country: str | None


@dataclass(frozen=True)
class TransactionUpsert:
    paypal_transaction_id: str
    occurred_at: datetime
    event_code: str | None
    kind: TransactionKind
    status: TransactionStatus
    gross: Decimal
    fee: Decimal
    net: Decimal
    currency: str
    origin: TransactionOrigin
    payer: PayerData
    raw_json: dict[str, Any] | None
    flag_reason: str | None = None
    paypal_order_id: str | None = None


@dataclass(frozen=True)
class SearchRow:
    detail: TransactionDetail
    raw: dict[str, Any]


@dataclass(frozen=True)
class SearchPage:
    rows: list[SearchRow]
    page: int
    total_pages: int
