"""Required test cases L1-L10 (constitution) for one payment."""

from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import ValidationError

from app.common.types import TransactionKind as K
from app.common.types import TransactionStatus as S
from app.engine.leakage import (
    LeakageInput,
    LeakageResult,
    RateUnavailable,
    calculate_leakage,
    is_eligible,
    paypal_rate_for,
    simulated_paypal_rate,
)

D = Decimal


def leak(gross: str, fee: str, mid: str | None = "84", pp: str | None = "81.5") -> LeakageResult:
    result = calculate_leakage(
        LeakageInput(
            gross=D(gross),
            fee=D(fee),
            currency="USD",
            mid_rate=D(mid) if mid else None,
            paypal_rate=D(pp) if pp else None,
        )
    )
    assert isinstance(result, LeakageResult)
    return result


def test_l1_worked_example() -> None:
    result = leak("1000.00", "44.00", "84.000000", "81.500000")
    assert result.ideal_inr == D("84000.00")
    assert result.inr_received == D("77914.00")
    assert result.fee_loss_inr == D("3696.00")
    assert result.fx_loss_inr == D("2390.00")
    assert result.total_leakage_inr == D("6086.00")
    assert result.leakage_percent == D("7.25")


def test_l2_zero_fee() -> None:
    result = leak("100.00", "0.00")
    assert result.fee_loss_inr == D("0.00")
    assert result.total_leakage_inr == result.fx_loss_inr


def test_l3_same_rates_mean_no_fx_loss() -> None:
    assert leak("100.00", "4.00", "84", "84").fx_loss_inr == D("0.00")


def test_l4_better_paypal_rate_is_a_gain() -> None:
    result = leak("100.00", "4.00", "84", "85")
    assert result.fx_loss_inr == D("-96.00")
    assert result.is_gain


@pytest.mark.parametrize(("gross", "fee"), [("10.00", "10.01"), ("-1.00", "0.00"), ("5", "-1")])
def test_l5_l6_invalid_amounts_are_rejected(gross: str, fee: str) -> None:
    with pytest.raises(ValidationError):
        LeakageInput(gross=D(gross), fee=D(fee), currency="USD", mid_rate=D(84), paypal_rate=D(81))


@pytest.mark.parametrize(("mid", "pp"), [(None, "81.5"), ("84", None), (None, None)])
def test_l7_missing_rate_gives_no_numbers(mid: str | None, pp: str | None) -> None:
    data = LeakageInput(
        gross=D(1),
        fee=D(0),
        currency="USD",
        mid_rate=D(mid) if mid else None,
        paypal_rate=D(pp) if pp else None,
    )
    assert calculate_leakage(data) == RateUnavailable()


@pytest.mark.parametrize("field", ["gross", "fee", "mid_rate", "paypal_rate"])
def test_l8_floats_are_rejected(field: str) -> None:
    values: dict[str, object] = {
        "gross": D(10),
        "fee": D(1),
        "currency": "USD",
        "mid_rate": D(84),
        "paypal_rate": D(81),
    }
    values[field] = 1.5
    with pytest.raises(ValidationError):
        LeakageInput.model_validate(values)


def test_l9_half_up_rounding() -> None:
    # fee loss 0.10 x 0.05 = 0.005 -> 0.01
    assert leak("1.00", "0.10", "0.05", "0.05").fee_loss_inr == D("0.01")


def test_zero_rate_is_rejected() -> None:
    with pytest.raises(ValidationError):
        LeakageInput(gross=D(1), fee=D(0), currency="USD", mid_rate=D(0), paypal_rate=D(1))


def test_simulated_rate_is_three_percent_below_mid() -> None:
    assert simulated_paypal_rate(D("84.000000")) == D("81.480000")
    assert simulated_paypal_rate(D("93.92")) == D("91.102400")


def test_zero_gross_has_no_percent() -> None:
    assert leak("0.00", "0.00").leakage_percent is None


cents = st.integers(min_value=0, max_value=10_000_000).map(lambda c: D(c) / 100)
rates = st.integers(min_value=1, max_value=300_000_000).map(lambda r: D(r) / 1_000_000)


@given(gross=cents, fee_share=st.integers(0, 100), mid=rates, spread=st.integers(-500, 2000))
def test_l10_total_equals_ideal_minus_received(
    gross: Decimal, fee_share: int, mid: Decimal, spread: int
) -> None:
    fee = (gross * fee_share / 100).quantize(D("0.01"), rounding="ROUND_DOWN")
    paypal = max(mid * (1 - D(spread) / 10_000), D("0.000001"))
    result = leak(str(gross), str(fee), str(mid), str(paypal))
    assert result.total_leakage_inr == result.ideal_inr - result.inr_received
    assert result.total_leakage_inr == result.fee_loss_inr + result.fx_loss_inr
    net = gross - fee
    assert abs(result.inr_received - net * paypal) <= D("0.015")
    assert abs(result.total_leakage_inr - (fee * mid + net * (mid - paypal))) <= D("0.01")


def test_inr_payments_have_no_spread() -> None:
    assert paypal_rate_for("INR", D("1.000000")) == D("1.000000")
    assert paypal_rate_for("USD", D("84")) == D("81.480000")


def test_only_completed_income_is_eligible() -> None:
    assert is_eligible(K.INCOME, S.COMPLETED)
    assert not is_eligible(K.INCOME, S.PENDING)
    assert not is_eligible(K.WITHDRAWAL, S.COMPLETED)
