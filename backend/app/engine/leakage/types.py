"""Validated inputs and outputs of the leakage engine. Floats are rejected (L8)."""

from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.common.types import CurrencyCode


class LeakageInput(BaseModel):
    """One payment: G (gross), F (fee) in the payment currency, and both rates to INR."""

    model_config = ConfigDict(frozen=True, strict=True)

    gross: Decimal
    fee: Decimal
    currency: CurrencyCode
    mid_rate: Decimal | None
    paypal_rate: Decimal | None

    @field_validator("mid_rate", "paypal_rate")
    @classmethod
    def rate_is_positive(cls, value: Decimal | None) -> Decimal | None:
        if value is not None and value <= 0:
            raise ValueError("an exchange rate must be greater than 0")
        return value

    @model_validator(mode="after")
    def amounts_are_valid(self) -> "LeakageInput":
        if self.gross < 0:
            raise ValueError("gross must not be negative (refunds are handled separately)")
        if self.fee < 0:
            raise ValueError("fee must not be negative")
        if self.fee > self.gross:
            raise ValueError("fee must not be greater than gross")
        return self

    @property
    def net(self) -> Decimal:
        return self.gross - self.fee


class LeakageResult(BaseModel):
    """INR values, rounded half-up to 2 dp. A negative FX loss is a gain (Principle III)."""

    model_config = ConfigDict(frozen=True)

    ideal_inr: Decimal
    inr_received: Decimal
    fee_loss_inr: Decimal
    fx_loss_inr: Decimal
    total_leakage_inr: Decimal
    leakage_percent: Decimal | None

    @property
    def is_gain(self) -> bool:
        return self.fx_loss_inr < 0


class RateUnavailable(BaseModel):
    """No numbers when a rate is missing (L7)."""

    model_config = ConfigDict(frozen=True)

    status: Literal["rate_unavailable"] = "rate_unavailable"
