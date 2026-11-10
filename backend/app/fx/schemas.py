"""Frankfurter v2 single-rate response (research R1), e.g.
{"date": "2026-11-06", "base": "USD", "quote": "INR", "rate": 93.92}
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.common.types import CurrencyCode


class FrankfurterRate(BaseModel):
    date: date
    base: CurrencyCode
    quote: CurrencyCode
    rate: Decimal = Field(gt=0)
