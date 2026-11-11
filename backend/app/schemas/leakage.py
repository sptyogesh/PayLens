"""Leakage of one transaction in the API (contracts/http-api.md). All values come from code."""

from typing import Annotated, Literal

from pydantic import BaseModel, StringConstraints

from app.common.constants import INR
from app.common.money import to_percent_string, to_rate_string
from app.engine.leakage import LeakageInput, LeakageResult, calculate_leakage, is_eligible
from app.models import Transaction
from app.schemas.common import MoneyOut

RateString = Annotated[str, StringConstraints(pattern=r"^\d+\.\d{6}$")]
PercentString = Annotated[str, StringConstraints(pattern=r"^-?\d+\.\d{2}$")]
LeakageStatus = Literal["calculated", "rate_unavailable", "not_calculated", "not_applicable"]


class LeakageOut(BaseModel):
    mid_market_rate: RateString
    paypal_rate: RateString
    paypal_rate_simulated: Literal[True] = True
    ideal_inr: MoneyOut
    inr_received: MoneyOut
    fee_loss_inr: MoneyOut
    fx_loss_inr: MoneyOut
    total_leakage_inr: MoneyOut
    leakage_percent: PercentString | None


def stored_result(row: Transaction) -> LeakageResult | None:
    """Re-derive the full result (incl. ideal INR and %) from the stored rates, or None."""
    eligible = is_eligible(row.kind, row.status)
    if not eligible or row.total_leakage_inr is None or row.fee_amount > row.gross_amount:
        return None
    data = LeakageInput(
        gross=row.gross_amount,
        fee=row.fee_amount,
        currency=row.currency,
        mid_rate=row.mid_market_rate,
        paypal_rate=row.paypal_rate,
    )
    result = calculate_leakage(data)
    return result if isinstance(result, LeakageResult) else None


def leakage_status(row: Transaction) -> LeakageStatus:
    if not is_eligible(row.kind, row.status):
        return "not_applicable"
    if row.total_leakage_inr is not None:
        return "calculated"
    return "not_calculated" if row.fee_amount > row.gross_amount else "rate_unavailable"


def leakage_out(row: Transaction) -> LeakageOut | None:
    """Ideal INR and leakage % are derived with the engine from the stored rates (research R5)."""
    result = stored_result(row)
    if result is None or row.mid_market_rate is None or row.paypal_rate is None:
        return None
    percent = result.leakage_percent
    return LeakageOut(
        mid_market_rate=to_rate_string(row.mid_market_rate),
        paypal_rate=to_rate_string(row.paypal_rate),
        ideal_inr=MoneyOut.of(result.ideal_inr, INR),
        inr_received=MoneyOut.of(result.inr_received, INR),
        fee_loss_inr=MoneyOut.of(result.fee_loss_inr, INR),
        fx_loss_inr=MoneyOut.of(result.fx_loss_inr, INR),
        total_leakage_inr=MoneyOut.of(result.total_leakage_inr, INR),
        leakage_percent=to_percent_string(percent) if percent is not None else None,
    )
