"""FIRA status for the period's payments, and the payments missing a FIRA."""

from typing import Final

from reportlab.platypus import Paragraph

from app.common.periods import format_day
from app.reports.format import money, text
from app.reports.labels import (
    REPORT_NO_FIRAS,
)
from app.reports.styles import BODY, BOLD_CELL, CELL, HEADING, NUMBER_CELL, Flowable, key_values
from app.reports.styles import table as grid
from app.schemas.report import ReportData, ReportFira, ReportMissingPayment

HEADING_TEXT: Final = "FIRA status"
UPLOADED: Final = "FIRAs uploaded (all time)"
MATCHED: Final = "Payments with a matched FIRA"
REVIEW: Final = "Payments whose FIRA needs review"
MISSING: Final = "Payments missing a FIRA"
MISSING_HEADING: Final = "Payments missing a FIRA"
COLUMNS: Final = ("Date", "Client", "PayPal transaction ID", "Gross")
WIDTHS: Final = [70.0, 170.0, 145.0, 100.0]


def missing_row(item: ReportMissingPayment) -> list[Flowable]:
    return [
        Paragraph(format_day(item.date), CELL),
        Paragraph(text(item.client), CELL),
        Paragraph(text(item.paypal_transaction_id), CELL),
        Paragraph(money(item.gross), NUMBER_CELL),
    ]


def counts(fira: ReportFira) -> Flowable:
    return key_values(
        [
            (UPLOADED, str(fira.uploaded)),
            (MATCHED, str(fira.matched)),
            (REVIEW, str(fira.needs_review)),
            (MISSING, str(fira.missing)),
        ]
    )


def fira(data: ReportData) -> list[Flowable]:
    status = data.fira
    out: list[Flowable] = [Paragraph(HEADING_TEXT, HEADING)]
    if status.uploaded == 0:
        out.append(Paragraph(REPORT_NO_FIRAS, BODY))
    if not any((status.matched, status.needs_review, status.missing)):
        return out  # no payments in the period: no zero tables
    out.append(counts(status))
    if status.missing_payments:
        header = [Paragraph(name, BOLD_CELL) for name in COLUMNS]
        rows = [header, *(missing_row(item) for item in status.missing_payments)]
        out += [Paragraph(MISSING_HEADING, HEADING), grid(rows, WIDTHS)]
    return out
