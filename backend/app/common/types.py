"""Shared value types and enums. Money always travels with its currency (Principle III)."""

from decimal import Decimal
from enum import StrEnum
from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints, field_validator

CurrencyCode = Annotated[str, StringConstraints(pattern=r"^[A-Z]{3}$")]


class Money(BaseModel):
    """An exact amount in one currency. Floats are rejected."""

    model_config = ConfigDict(frozen=True)

    amount: Decimal
    currency: CurrencyCode

    @field_validator("amount", mode="before")
    @classmethod
    def reject_float(cls, value: object) -> object:
        if isinstance(value, float):
            raise ValueError("money amount must not be a float")
        return value


class TransactionSource(StrEnum):
    PAYPAL_SANDBOX = "paypal_sandbox"
    DEMO_SEED = "demo_seed"


class TransactionOrigin(StrEnum):
    TRANSACTION_SEARCH = "transaction_search"
    CHECKOUT_CAPTURE = "checkout_capture"
    SEED = "seed"


class TransactionKind(StrEnum):
    INCOME = "income"
    OUTGOING_PAYMENT = "outgoing_payment"
    REFUND = "refund"
    WITHDRAWAL = "withdrawal"
    CONVERSION = "conversion"
    HOLD = "hold"
    FEE = "fee"
    OTHER = "other"


class TransactionStatus(StrEnum):
    COMPLETED = "completed"
    PENDING = "pending"
    DENIED = "denied"
    REVERSED = "reversed"


class SyncTrigger(StrEnum):
    MANUAL = "manual"
    STARTUP = "startup"


class SyncOutcome(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"


class FiraStatus(StrEnum):
    MATCHED = "matched"
    NEEDS_REVIEW = "needs_review"
    MISSING = "missing"
