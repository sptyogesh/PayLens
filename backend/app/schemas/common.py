"""Shared API models. Money crosses the API as a string with its currency (FR-051)."""

from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, StringConstraints

from app.common.money import to_api_string
from app.common.types import CurrencyCode, Money

MoneyString = Annotated[str, StringConstraints(pattern=r"^-?\d+\.\d{2}$")]


class MoneyOut(BaseModel):
    amount: MoneyString
    currency: CurrencyCode

    @classmethod
    def of(cls, amount: Decimal, currency: str) -> "MoneyOut":
        return cls(amount=to_api_string(amount), currency=currency)

    @classmethod
    def from_money(cls, money: Money) -> "MoneyOut":
        return cls.of(money.amount, money.currency)


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorOut(BaseModel):
    error: ErrorDetail
