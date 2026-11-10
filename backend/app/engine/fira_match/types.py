"""Validated inputs and outputs of the FIRA matching engine. Floats are rejected (Principle III)."""

import datetime as dt
from decimal import Decimal
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.common.constants import FIRA_AMOUNT_TOLERANCE_PCT, FIRA_DATE_WINDOW_DAYS
from app.common.types import CurrencyCode

FiraStatus = Literal["matched", "needs_review", "no_match"]
PaymentStatus = Literal["matched", "needs_review", "missing"]
MatchKind = Literal["direct", "weekly"]

REASON_AMOUNT: Final = f"Amount differs by more than {FIRA_AMOUNT_TOLERANCE_PCT}%"
REASON_DATE: Final = f"Date more than {FIRA_DATE_WINDOW_DAYS} days apart"
REASON_REFERENCE: Final = "Reference not found"
REASON_TAKEN: Final = "Payment already matched to another FIRA (higher score)"
REASON_WEEKLY: Final = "Total equals the payments of one week — check each one"
REASON_NO_CURRENCY: Final = "No payment with this currency"
REASON_SEPARATOR: Final = "; "


class FiraCandidate(BaseModel):
    """One FIRA's extracted fields. `order` is the upload order, used to break ties."""

    model_config = ConfigDict(frozen=True, strict=True)

    fira_key: str
    amount: Decimal = Field(gt=0)
    currency: CurrencyCode
    date: dt.date
    reference: str | None
    order: int


class PaymentCandidate(BaseModel):
    """One eligible PayPal payment. `date` is the payment's IST calendar date."""

    model_config = ConfigDict(frozen=True, strict=True)

    payment_key: str
    paypal_transaction_id: str
    gross: Decimal = Field(gt=0)
    currency: CurrencyCode
    date: dt.date


class ScoreBreakdown(BaseModel):
    """Which of the three checks passed, and the total score."""

    model_config = ConfigDict(frozen=True, strict=True)

    reference: bool
    amount: bool
    date: bool
    total: int


class FiraOutcome(BaseModel):
    """The result for one FIRA: status, score, reason and the payments linked to it."""

    model_config = ConfigDict(frozen=True, strict=True)

    fira_key: str
    status: FiraStatus
    score: int | None
    reason: str | None
    payment_keys: list[str]
    kind: MatchKind | None


class MatchResult(BaseModel):
    """All FIRA outcomes (input order) and every payment's status (sorted by key)."""

    model_config = ConfigDict(frozen=True, strict=True)

    firas: list[FiraOutcome]
    payments: dict[str, PaymentStatus]
