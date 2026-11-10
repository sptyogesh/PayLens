"""What leakage needs from an FX source: one mid-market rate to INR for a currency and date."""

from datetime import date
from decimal import Decimal
from typing import Protocol

from pydantic import BaseModel, ConfigDict


class FxQuote(BaseModel):
    """A mid-market rate (INR per 1 unit) and the date the source actually published it."""

    model_config = ConfigDict(frozen=True)

    rate: Decimal
    published_date: date
    source: str


class FxGateway(Protocol):
    def mid_rate(self, currency: str, on: date) -> FxQuote | None:
        """The rate for `on` (or the latest earlier published one); None if the source has none.

        Raises FxUnavailableError when the source cannot be reached.
        """
        ...
