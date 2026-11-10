"""Leakage engine (Phase 1A plan section 10). Public entry; import from here only.

Children: `types` (validated inputs/outputs), `calculate` (one payment).
"""

from app.engine.leakage.calculate import (
    calculate_leakage,
    is_eligible,
    leakage_percent,
    paypal_rate_for,
    simulated_paypal_rate,
)
from app.engine.leakage.types import LeakageInput, LeakageResult, RateUnavailable

__all__ = [
    "LeakageInput",
    "LeakageResult",
    "RateUnavailable",
    "calculate_leakage",
    "is_eligible",
    "leakage_percent",
    "paypal_rate_for",
    "simulated_paypal_rate",
]
