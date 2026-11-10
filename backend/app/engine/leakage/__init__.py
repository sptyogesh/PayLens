"""Leakage engine (Phase 1A plan section 10). Public entry; import from here only.

Children: `types` (validated inputs/outputs), `calculate` (one payment), `aggregate` (totals,
by month, by client).
"""

from app.engine.leakage.aggregate import (
    GroupTotals,
    LeakageRow,
    LeakageTotals,
    by_client,
    by_month,
    totals,
)
from app.engine.leakage.calculate import (
    ELIGIBLE_KIND,
    ELIGIBLE_STATUS,
    calculate_leakage,
    is_eligible,
    leakage_percent,
    paypal_rate_for,
    simulated_paypal_rate,
)
from app.engine.leakage.types import LeakageInput, LeakageResult, RateUnavailable

__all__ = [
    "ELIGIBLE_KIND",
    "ELIGIBLE_STATUS",
    "GroupTotals",
    "LeakageInput",
    "LeakageResult",
    "LeakageRow",
    "LeakageTotals",
    "RateUnavailable",
    "by_client",
    "by_month",
    "calculate_leakage",
    "is_eligible",
    "leakage_percent",
    "paypal_rate_for",
    "simulated_paypal_rate",
    "totals",
]
