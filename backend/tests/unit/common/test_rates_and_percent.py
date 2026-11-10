from decimal import Decimal

from app.common.money import round_percent, round_rate, to_percent_string, to_rate_string


def test_rate_rounds_half_up_to_six_places() -> None:
    assert round_rate(Decimal("81.4800005")) == Decimal("81.480001")
    assert round_rate(Decimal("81.4800004")) == Decimal("81.480000")


def test_rate_string_always_has_six_places() -> None:
    assert to_rate_string(Decimal("84")) == "84.000000"
    assert to_rate_string(Decimal("93.92")) == "93.920000"


def test_percent_rounds_half_up_to_two_places() -> None:
    assert round_percent(Decimal("7.245")) == Decimal("7.25")
    assert to_percent_string(Decimal("7.2452380")) == "7.25"
    assert to_percent_string(Decimal("-0.005")) == "-0.01"
