"""fx_rates cache: fetch once, weekend fallback stored, fail fast on outage (research R2)."""

from datetime import date
from decimal import Decimal

from freezegun import freeze_time
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.fakes.fx_fake import FakeFxGateway
from app.models import FxRate
from app.services.fx_rate_service import RateLookup

SATURDAY = date(2026, 11, 7)


@freeze_time("2026-11-10 06:00:00")
def test_rate_is_fetched_once_and_cached(db_session: Session) -> None:
    fx = FakeFxGateway()
    assert RateLookup(db_session, fx).mid_rate("USD", SATURDAY) == Decimal("84.000000")
    assert RateLookup(db_session, fx).mid_rate("USD", SATURDAY) == Decimal("84.000000")
    assert fx.calls == [("USD", SATURDAY)]
    stored = db_session.scalars(select(FxRate)).one()
    assert (stored.rate_date, stored.published_date) == (SATURDAY, date(2026, 11, 6))
    assert stored.source == "fake"


@freeze_time("2026-11-10 06:00:00")
def test_inr_needs_no_fetch(db_session: Session) -> None:
    fx = FakeFxGateway()
    assert RateLookup(db_session, fx).mid_rate("INR", SATURDAY) == Decimal("1.000000")
    assert fx.calls == []


@freeze_time("2026-11-10 06:00:00")
def test_unknown_currency_is_not_cached(db_session: Session) -> None:
    assert RateLookup(db_session, FakeFxGateway()).mid_rate("JPY", SATURDAY) is None
    assert db_session.scalars(select(FxRate)).first() is None


@freeze_time("2026-11-10 06:00:00")
def test_outage_stops_fetching_for_the_rest_of_the_run(db_session: Session) -> None:
    fx = FakeFxGateway(unavailable=True)
    lookup = RateLookup(db_session, fx)
    assert lookup.mid_rate("USD", SATURDAY) is None
    assert lookup.mid_rate("GBP", SATURDAY) is None
    assert lookup.source_down
    assert len(fx.calls) == 1


@freeze_time("2026-11-10 06:00:00")
def test_future_dates_use_today(db_session: Session) -> None:
    fx = FakeFxGateway()
    RateLookup(db_session, fx).mid_rate("USD", date(2026, 12, 25))
    assert fx.calls == [("USD", date(2026, 11, 10))]
