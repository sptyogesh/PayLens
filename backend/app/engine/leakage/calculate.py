"""Leakage of one payment, exactly as Phase 1A plan section 10:

    ideal INR    = G x r_mid          fee loss = F x r_mid
    INR received = N x r_pp           FX loss  = N x (r_mid - r_pp)
    total        = fee loss + FX loss (= ideal - received)

Rounding happens only on the returned values (Principle III).
"""

from decimal import Decimal

from app.common.constants import INR, PERCENT_FACTOR, SIMULATED_FX_SPREAD
from app.common.money import round_money, round_percent, round_rate
from app.common.types import TransactionKind, TransactionStatus
from app.engine.leakage.types import LeakageInput, LeakageResult, RateUnavailable


def simulated_paypal_rate(mid_rate: Decimal) -> Decimal:
    """Sandbox has no INR conversion, so the PayPal rate is simulated (plan section 9)."""
    return round_rate(mid_rate * (Decimal(1) - SIMULATED_FX_SPREAD))


def paypal_rate_for(currency: str, mid_rate: Decimal) -> Decimal:
    """INR payments need no conversion, so there is no spread (research R3)."""
    return mid_rate if currency == INR else simulated_paypal_rate(mid_rate)


def is_eligible(kind: TransactionKind, status: TransactionStatus) -> bool:
    """Only completed income has leakage; other events are stored but not analysed (P8)."""
    return kind is TransactionKind.INCOME and status is TransactionStatus.COMPLETED


def leakage_percent(total: Decimal, ideal: Decimal) -> Decimal | None:
    """Total leakage as a share of ideal INR; None when there is no income."""
    if ideal == 0:
        return None
    return round_percent(total / ideal * PERCENT_FACTOR)


def calculate_leakage(data: LeakageInput) -> LeakageResult | RateUnavailable:
    if data.mid_rate is None or data.paypal_rate is None:
        return RateUnavailable()
    mid, paypal, net = data.mid_rate, data.paypal_rate, data.net
    ideal = data.gross * mid
    fee_loss = data.fee * mid
    fx_loss = net * (mid - paypal)
    # The total is rounded from the exact sum, so |total - (ideal - received)| <= 0.01 (L10).
    total = fee_loss + fx_loss
    return LeakageResult(
        ideal_inr=round_money(ideal),
        inr_received=round_money(net * paypal),
        fee_loss_inr=round_money(fee_loss),
        fx_loss_inr=round_money(fx_loss),
        total_leakage_inr=round_money(total),
        leakage_percent=leakage_percent(total, ideal),
    )
