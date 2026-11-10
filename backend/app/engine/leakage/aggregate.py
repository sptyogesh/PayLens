"""Totals of many payments: overall, by month and by client (FR-030, FR-032).

Sums use the rounded per-payment values, so group rows always add up to the totals exactly
(SC-003). Leakage % is total leakage / income x 100, computed once from the sums.
"""

from collections.abc import Callable, Iterable
from datetime import date
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.common.constants import MONTH_LABEL_FORMAT
from app.engine.leakage.calculate import leakage_percent
from app.engine.leakage.types import LeakageResult


class LeakageRow(BaseModel):
    """One calculated payment with the keys it is grouped by. `month` is "YYYY-MM" (IST)."""

    model_config = ConfigDict(frozen=True)

    month: str
    client_key: str
    client_label: str
    result: LeakageResult


class LeakageTotals(BaseModel):
    model_config = ConfigDict(frozen=True)

    payment_count: int
    income_inr: Decimal
    fee_loss_inr: Decimal
    fx_loss_inr: Decimal
    total_leakage_inr: Decimal
    leakage_percent: Decimal | None


class GroupTotals(BaseModel):
    model_config = ConfigDict(frozen=True)

    key: str
    label: str
    totals: LeakageTotals


def totals(rows: Iterable[LeakageRow]) -> LeakageTotals:
    results = [row.result for row in rows]
    income = sum((r.ideal_inr for r in results), Decimal(0))
    total = sum((r.total_leakage_inr for r in results), Decimal(0))
    return LeakageTotals(
        payment_count=len(results),
        income_inr=income,
        fee_loss_inr=sum((r.fee_loss_inr for r in results), Decimal(0)),
        fx_loss_inr=sum((r.fx_loss_inr for r in results), Decimal(0)),
        total_leakage_inr=total,
        leakage_percent=leakage_percent(total, income),
    )


def group(
    rows: Iterable[LeakageRow], key: Callable[[LeakageRow], tuple[str, str]]
) -> list[GroupTotals]:
    groups: dict[str, tuple[str, list[LeakageRow]]] = {}
    for row in rows:
        group_key, label = key(row)
        groups.setdefault(group_key, (label, []))[1].append(row)
    return [GroupTotals(key=k, label=label, totals=totals(rs)) for k, (label, rs) in groups.items()]


def month_label(month: str) -> str:
    """ "2026-11" -> "Nov 2026"."""
    return date.fromisoformat(f"{month}-01").strftime(MONTH_LABEL_FORMAT)


def by_month(rows: Iterable[LeakageRow]) -> list[GroupTotals]:
    """Newest month first."""
    months = group(rows, lambda row: (row.month, month_label(row.month)))
    return sorted(months, key=lambda g: g.key, reverse=True)


def by_client(rows: Iterable[LeakageRow]) -> list[GroupTotals]:
    """Highest total leakage first; ties by name."""
    clients = group(rows, lambda row: (row.client_key, row.client_label))
    return sorted(clients, key=lambda g: (-g.totals.total_leakage_inr, g.label, g.key))
