"""Mid-market rate lookup with the fx_rates cache (research R2).

Each (currency, IST date) is fetched at most once and stored. After the first outage in a run,
no more fetches are tried, so sync and /pay never wait on a down FX source (FR-005).
"""

import logging
from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.common.constants import INR, INR_RATE
from app.common.dates import ist_date, utc_now
from app.common.errors import FxUnavailableError
from app.fx import FxGateway, FxQuote
from app.models import FxRate

logger = logging.getLogger(__name__)

RateKey = tuple[str, date]


class RateLookup:
    def __init__(self, session: Session, gateway: FxGateway) -> None:
        self._session = session
        self._gateway = gateway
        self._known: dict[RateKey, Decimal | None] = {}
        self.source_down = False

    def mid_rate(self, currency: str, on: date) -> Decimal | None:
        if currency == INR:
            return INR_RATE
        key = (currency, min(on, ist_date(utc_now())))
        if key not in self._known:
            self._known[key] = self._stored(key) or self._fetch(key)
        return self._known[key]

    def _stored(self, key: RateKey) -> Decimal | None:
        query = select(FxRate.rate).where(FxRate.currency == key[0], FxRate.rate_date == key[1])
        return self._session.scalar(query)

    def _fetch(self, key: RateKey) -> Decimal | None:
        if self.source_down:
            return None
        try:
            quote = self._gateway.mid_rate(*key)
        except FxUnavailableError:
            logger.warning("FX source unavailable; leakage stays 'rate unavailable' for now")
            self.source_down = True
            return None
        if quote is None:
            return None
        self._save(key, quote)
        return quote.rate

    def _save(self, key: RateKey, quote: FxQuote) -> None:
        """Insert once; a concurrent run that stored the same key first wins (no error)."""
        values = {
            "currency": key[0],
            "rate_date": key[1],
            "published_date": min(quote.published_date, key[1]),
            "rate": quote.rate,
            "source": quote.source,
            "fetched_at": utc_now(),
        }
        self._session.execute(insert(FxRate).values(**values).on_conflict_do_nothing())
