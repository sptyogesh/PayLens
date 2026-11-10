"""API models for POST /fira/upload and GET /fira (004 contracts/http-api.md).

Uploaded bytes are never returned or stored; only extracted fields, status and matches.
"""

import re
import uuid
from datetime import date
from decimal import Decimal
from typing import Final, Literal

from pydantic import BaseModel

from app.common.constants import INR
from app.common.money import to_rate_string
from app.models import FiraDocStatus, FiraDocument, FiraMatchKind
from app.schemas.common import MoneyOut, UtcDatetime

UploadOutcome = Literal["stored", "duplicate", "rejected", "failed"]
ISO_CURRENCY: Final = re.compile(r"^[A-Z]{3}$")


class UploadFileOut(BaseModel):
    """What happened to one uploaded file. `status` is set only when it was stored."""

    file_name: str
    outcome: UploadOutcome
    message: str
    fira_id: uuid.UUID | None
    status: FiraDocStatus | None


class FiraSummaryOut(BaseModel):
    matched: int
    needs_review: int
    no_match: int
    missing_payments: int


class UploadResultOut(BaseModel):
    result: UploadFileOut
    summary: FiraSummaryOut


class FiraMatchOut(BaseModel):
    transaction_id: uuid.UUID
    paypal_transaction_id: str
    score: int
    kind: FiraMatchKind


class FiraPaymentOut(BaseModel):
    """An eligible payment (used for the "missing FIRA" list)."""

    transaction_id: uuid.UUID
    paypal_transaction_id: str
    date: date
    client: str
    gross: MoneyOut


def money_or_none(amount: Decimal | None, currency: str | None) -> MoneyOut | None:
    if amount is None or currency is None or not ISO_CURRENCY.match(currency):
        return None
    return MoneyOut.of(amount, currency)


class FiraItemOut(BaseModel):
    id: uuid.UUID
    file_name: str
    status: FiraDocStatus
    score: int | None
    reason: str | None
    foreign_amount: MoneyOut | None
    inr_amount: MoneyOut | None
    rate: str | None
    remittance_date: date | None
    reference_no: str | None
    remitter: str | None
    purpose_code: str | None
    uploaded_at: UtcDatetime
    matches: list[FiraMatchOut]

    @classmethod
    def from_model(cls, doc: FiraDocument, matches: list[FiraMatchOut]) -> "FiraItemOut":
        return cls(
            id=doc.id,
            file_name=doc.file_name,
            status=doc.status,
            score=doc.score,
            reason=doc.reason,
            foreign_amount=money_or_none(doc.foreign_amount, doc.currency),
            inr_amount=money_or_none(doc.inr_amount, INR),
            rate=to_rate_string(doc.rate) if doc.rate is not None else None,
            remittance_date=doc.remittance_date,
            reference_no=doc.reference_no,
            remitter=doc.remitter,
            purpose_code=doc.purpose_code,
            uploaded_at=doc.uploaded_at,
            matches=matches,
        )


class FiraListOut(BaseModel):
    summary: FiraSummaryOut
    items: list[FiraItemOut]
    missing: list[FiraPaymentOut]
