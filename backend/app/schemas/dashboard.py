"""GET /dashboard response (contracts/http-api.md). Every number comes from backend code."""

from typing import Literal

from pydantic import BaseModel

from app.common.constants import INR
from app.common.money import to_percent_string
from app.common.periods import DashboardPeriod
from app.common.types import TransactionSource
from app.engine.leakage import GroupTotals, LeakageTotals
from app.schemas.common import MoneyOut, UtcDatetime
from app.schemas.leakage import PercentString


class DashboardPeriodOut(BaseModel):
    key: DashboardPeriod
    label: str
    start: UtcDatetime | None
    end: UtcDatetime | None


class TotalsOut(BaseModel):
    payment_count: int
    income_inr: MoneyOut
    fee_loss_inr: MoneyOut
    fx_loss_inr: MoneyOut
    total_leakage_inr: MoneyOut
    leakage_percent: PercentString | None

    @classmethod
    def of(cls, totals: LeakageTotals) -> "TotalsOut":
        percent = totals.leakage_percent
        return cls(
            payment_count=totals.payment_count,
            income_inr=MoneyOut.of(totals.income_inr, INR),
            fee_loss_inr=MoneyOut.of(totals.fee_loss_inr, INR),
            fx_loss_inr=MoneyOut.of(totals.fx_loss_inr, INR),
            total_leakage_inr=MoneyOut.of(totals.total_leakage_inr, INR),
            leakage_percent=to_percent_string(percent) if percent is not None else None,
        )


class BreakdownRowOut(BaseModel):
    key: str
    label: str
    totals: TotalsOut

    @classmethod
    def of(cls, group: GroupTotals) -> "BreakdownRowOut":
        return cls(key=group.key, label=group.label, totals=TotalsOut.of(group.totals))


class DashboardOut(BaseModel):
    period: DashboardPeriodOut
    totals: TotalsOut | None
    excluded_count: int
    not_calculated_count: int
    sources: list[TransactionSource]
    paypal_rate_simulated: Literal[True] = True
    simulated_spread_percent: PercentString
    by_month: list[BreakdownRowOut]
    by_client: list[BreakdownRowOut]
