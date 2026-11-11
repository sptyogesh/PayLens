"""Pydantic models for PayPal responses (Principle IV). Only the fields we use (research R2–R6)."""

import re
from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

COMPACT_OFFSET = re.compile(r"([+-]\d{2})(\d{2})$")


class PayPalModel(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)


class TokenResponse(PayPalModel):
    access_token: str
    expires_in: int


class AmountWithCurrency(PayPalModel):
    currency_code: str
    value: str


class TransactionInfo(PayPalModel):
    transaction_id: str
    transaction_event_code: str | None = None
    transaction_initiation_date: datetime
    transaction_amount: AmountWithCurrency
    fee_amount: AmountWithCurrency | None = None
    transaction_status: str | None = None

    @field_validator("transaction_initiation_date", mode="before")
    @classmethod
    def normalise_offset(cls, value: object) -> object:
        """PayPal sends offsets like +0000; make them ISO 8601 (+00:00)."""
        if isinstance(value, str):
            return COMPACT_OFFSET.sub(r"\1:\2", value)
        return value


class PayerName(PayPalModel):
    given_name: str | None = None
    surname: str | None = None
    full_name: str | None = None
    alternate_full_name: str | None = None


class PayerInfo(PayPalModel):
    email_address: str | None = None
    payer_name: PayerName | None = None
    country_code: str | None = None


class TransactionDetail(PayPalModel):
    transaction_info: TransactionInfo
    payer_info: PayerInfo | None = None


class SearchResponse(PayPalModel):
    transaction_details: list[TransactionDetail] = []
    page: int = 1
    total_pages: int = 0
    total_items: int = 0
