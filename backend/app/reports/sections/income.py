"""Income summary: payments, income in INR and gross received per original currency."""

from typing import Final

from reportlab.platypus import Paragraph

from app.common.constants import REPORT_NO_PAYMENTS
from app.reports.format import money
from app.reports.styles import BODY, HEADING, Flowable, key_values
from app.schemas.report import ReportData

HEADING_TEXT: Final = "Income summary"
PAYMENTS: Final = "Payments"
INCOME: Final = "Income (INR, mid-market)"
GROSS: Final = "Gross received ({currency})"


def income(data: ReportData) -> list[Flowable]:
    totals = data.totals
    if totals is None:
        return [Paragraph(HEADING_TEXT, HEADING), Paragraph(REPORT_NO_PAYMENTS, BODY)]
    pairs = [(PAYMENTS, str(totals.payment_count)), (INCOME, money(totals.income_inr))]
    pairs += [(GROSS.format(currency=g.currency), money(g)) for g in data.gross_by_currency]
    return [Paragraph(HEADING_TEXT, HEADING), key_values(pairs)]
