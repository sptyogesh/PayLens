"""Fake FX source for tests and E2E (FX_MODE=fake, APP_ENV=test only).

Fixed mid-market rates; weekends fall back to Friday like ECB reference rates.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Final

from app.common.constants import FX_FAKE_SOURCE_NAME
from app.common.errors import FxUnavailableError
from app.fx.gateway import FxQuote

FAKE_RATES: Final = {
    "USD": Decimal("84.000000"),
    "GBP": Decimal("106.500000"),
    "EUR": Decimal("90.250000"),
    "AUD": Decimal("55.100000"),
}
SATURDAY: Final = 5


def last_working_day(on: date) -> date:
    return on - timedelta(days=max(0, on.weekday() - SATURDAY + 1))


class FakeFxGateway:
    def __init__(self, *, unavailable: bool = False) -> None:
        self.unavailable = unavailable
        self.calls: list[tuple[str, date]] = []

    def mid_rate(self, currency: str, on: date) -> FxQuote | None:
        self.calls.append((currency, on))
        if self.unavailable:
            raise FxUnavailableError("Fake FX source is down.")
        rate = FAKE_RATES.get(currency)
        if rate is None:
            return None
        return FxQuote(rate=rate, published_date=last_working_day(on), source=FX_FAKE_SOURCE_NAME)
