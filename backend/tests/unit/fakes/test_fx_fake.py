from datetime import date
from decimal import Decimal

import pytest

from app.api.deps import get_fx_gateway
from app.common.errors import FxUnavailableError
from app.config import get_settings
from app.fakes.fx_fake import FakeFxGateway
from app.fx import FrankfurterGateway


@pytest.mark.parametrize(
    ("on", "published"),
    [
        (date(2026, 11, 6), date(2026, 11, 6)),  # Friday
        (date(2026, 11, 7), date(2026, 11, 6)),  # Saturday
        (date(2026, 11, 8), date(2026, 11, 6)),  # Sunday
        (date(2026, 11, 9), date(2026, 11, 9)),  # Monday
    ],
)
def test_weekends_fall_back_to_friday(on: date, published: date) -> None:
    quote = FakeFxGateway().mid_rate("USD", on)
    assert quote is not None
    assert (quote.rate, quote.published_date) == (Decimal("84.000000"), published)


def test_unknown_currency_and_outage() -> None:
    assert FakeFxGateway().mid_rate("JPY", date(2026, 11, 6)) is None
    with pytest.raises(FxUnavailableError):
        FakeFxGateway(unavailable=True).mid_rate("USD", date(2026, 11, 6))


def test_dependency_picks_gateway_by_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    get_fx_gateway.cache_clear()
    assert isinstance(get_fx_gateway(), FakeFxGateway)
    monkeypatch.setenv("FX_MODE", "http")
    get_settings.cache_clear()
    get_fx_gateway.cache_clear()
    assert isinstance(get_fx_gateway(), FrankfurterGateway)
    get_fx_gateway.cache_clear()
