"""API models for the /pay sandbox checkout (FR-030, FR-031, contracts/http-api.md)."""

from decimal import Decimal
from typing import Annotated, Literal

from pydantic import BaseModel, Field, StringConstraints, field_validator

from app.common.constants import CHECKOUT_DESCRIPTION_MAX, CHECKOUT_MAX_AMOUNT
from app.common.money import to_api_string
from app.schemas.common import MoneyOut

CheckoutCurrency = Literal["USD", "GBP", "EUR", "AUD"]  # must equal CHECKOUT_CURRENCIES
AmountInput = Annotated[str, StringConstraints(pattern=r"^\d+(\.\d{1,2})?$")]
OrderId = Annotated[str, StringConstraints(pattern=r"^[A-Z0-9]{1,32}$")]


class PayOrderIn(BaseModel):
    amount: AmountInput
    currency: CheckoutCurrency
    description: str | None = Field(default=None, max_length=CHECKOUT_DESCRIPTION_MAX)

    @field_validator("amount")
    @classmethod
    def amount_in_range(cls, value: str) -> str:
        amount = Decimal(value)
        if not Decimal(0) < amount <= CHECKOUT_MAX_AMOUNT:
            raise ValueError(f"amount must be more than 0 and at most {CHECKOUT_MAX_AMOUNT}")
        return to_api_string(amount)

    @field_validator("description")
    @classmethod
    def blank_is_none(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None


class PayOrderOut(BaseModel):
    order_id: str


class CaptureOut(BaseModel):
    transaction_id: str
    order_id: str
    status: Literal["completed", "pending"]
    gross: MoneyOut
    recorded: bool
