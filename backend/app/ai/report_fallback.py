"""Plain summary written by code (005 US2): used when the AI summary fails or is not grounded.

Only copies strings from the report figures; no arithmetic.
"""

from typing import Final

from app.common.constants import REPORT_NO_PAYMENTS, SIMULATED_LABEL
from app.common.money import group_digits
from app.schemas.report import ReportFigures, ReportSummary

RUPEE: Final = "₹"  # totals are always INR; the PDF draws it with the rupee font
PAYMENTS: Final = "{label}: {count} payments, income {income} (mid-market)."
LEAKAGE: Final = (
    f"Total leakage was {{total}}{{percent}}, with FX loss at a {SIMULATED_LABEL} rate."
)
PERCENT: Final = " ({percent}% of income)"
FIRA_MISSING: Final = "{missing} payments are missing a FIRA."
FIRA_MISSING_ONE: Final = "1 payment is missing a FIRA."


def fira_missing_text(missing: int) -> str:
    return FIRA_MISSING_ONE if missing == 1 else FIRA_MISSING.format(missing=missing)


def code_summary(figures: ReportFigures) -> ReportSummary:
    totals = figures.totals
    if totals is None:
        return ReportSummary(text=REPORT_NO_PAYMENTS, source="code")
    income, total = totals.income_inr, totals.total_leakage_inr
    percent = totals.leakage_percent
    parts = [
        PAYMENTS.format(
            label=figures.period.label,
            count=totals.payment_count,
            income=RUPEE + group_digits(income.amount, income.currency),
        ),
        LEAKAGE.format(
            total=RUPEE + group_digits(total.amount, total.currency),
            percent=PERCENT.format(percent=percent) if percent is not None else "",
        ),
        FIRA_MISSING_ONE
        if figures.fira.missing == 1
        else FIRA_MISSING.format(missing=figures.fira.missing),
    ]
    return ReportSummary(text=" ".join(parts), source="code")
