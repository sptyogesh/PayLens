"""By month and by client tables (same rows as the dashboard). Long names wrap; tables split."""

from typing import Final

from reportlab.platypus import Paragraph

from app.common.constants import SIMULATED_LABEL
from app.reports.format import amount, fx_cell, percent, text
from app.reports.styles import BOLD_CELL, CELL, HEADING, NUMBER_CELL, Flowable, table
from app.schemas.dashboard import BreakdownRowOut
from app.schemas.report import ReportData

BY_MONTH: Final = "By month"
BY_CLIENT: Final = "By client"
COLUMNS: Final = (
    "Payments",
    "Income (INR)",
    "Fee loss (INR)",
    f"FX loss (INR, {SIMULATED_LABEL})",
    "Total leakage (INR)",
    "Leakage %",
)
WIDTHS: Final = [130.0, 50.0, 70.0, 65.0, 75.0, 70.0, 55.0]


def row(item: BreakdownRowOut) -> list[Flowable]:
    totals = item.totals
    values = [
        str(totals.payment_count),
        amount(totals.income_inr),
        amount(totals.fee_loss_inr),
        fx_cell(totals.fx_loss_inr),
        amount(totals.total_leakage_inr),
        percent(totals.leakage_percent),
    ]
    return [Paragraph(text(item.label), CELL), *(Paragraph(v, NUMBER_CELL) for v in values)]


def breakdown(title: str, first_column: str, items: list[BreakdownRowOut]) -> list[Flowable]:
    header = [Paragraph(name, BOLD_CELL) for name in (first_column, *COLUMNS)]
    rows = [header, *(row(item) for item in items)]
    return [Paragraph(title, HEADING), table(rows, WIDTHS)]


def breakdowns(data: ReportData) -> list[Flowable]:
    if data.totals is None:
        return []
    return [
        *breakdown(BY_MONTH, "Month", data.by_month),
        *breakdown(BY_CLIENT, "Client", data.by_client),
    ]
