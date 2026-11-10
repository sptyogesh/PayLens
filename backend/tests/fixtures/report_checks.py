"""SC-001 checks: every report value is in the PDF text, and every PDF number is in the data."""

import re
from typing import Final

from app.ai.grounding import leaves, number_tokens
from app.common.periods import format_day
from app.reports.format import (
    RUPEE,
    RUPEE_TEXT,
    amount,
    fx_cell,
    is_gain,
    money,
    percent,
    without_sign,
)
from app.schemas.dashboard import BreakdownRowOut, TotalsOut
from app.schemas.report import ReportData

# Numbers in the PDF that are not report values: page numbers, IST dates and the generated time.
NOT_VALUES: Final = re.compile(
    r"Page \d+|\b\d{1,2} [A-Z][a-z]{2} \d{4}(, \d{2}:\d{2})?|\b[A-Z][a-z]{2} \d{4}\b"
)


def totals_strings(totals: TotalsOut) -> list[str]:
    fx = totals.fx_loss_inr
    return [
        str(totals.payment_count),
        money(totals.income_inr),
        money(totals.fee_loss_inr),
        money(without_sign(fx)) if is_gain(fx) else money(fx),
        money(totals.total_leakage_inr),
        percent(totals.leakage_percent),
    ]


def row_strings(item: BreakdownRowOut) -> list[str]:
    totals = item.totals
    return [
        item.label,
        str(totals.payment_count),
        amount(totals.income_inr),
        amount(totals.fee_loss_inr),
        fx_cell(totals.fx_loss_inr),
        amount(totals.total_leakage_inr),
        percent(totals.leakage_percent),
    ]


def expected_strings(data: ReportData) -> list[str]:
    """Every value of the report, formatted the way the PDF shows it."""
    summary = data.summary.text.replace(RUPEE, RUPEE_TEXT)
    found = [summary, data.disclaimer, *data.notes, data.period.label]
    found += [str(data.excluded_count), str(data.not_calculated_count)]
    if data.totals is not None:
        found += totals_strings(data.totals) + [money(g) for g in data.gross_by_currency]
        for item in [*data.by_month, *data.by_client]:
            found += row_strings(item)
    fira = data.fira
    found += [str(n) for n in (fira.uploaded, fira.matched, fira.needs_review, fira.missing)]
    for payment in fira.missing_payments:
        found += [format_day(payment.date), payment.client, payment.paypal_transaction_id]
        found.append(money(payment.gross))
    return found


def missing_from_pdf(data: ReportData, text: str) -> list[str]:
    return [value for value in expected_strings(data) if value not in text]


def unsigned(values: list[str]) -> set[str]:
    return {value.lstrip("-") for value in values}


def numbers_not_in_data(data: ReportData, text: str) -> list[str]:
    """Number tokens in the PDF text (minus dates, times and page numbers) not in the data."""
    known: set[str] = set()
    for _, value in leaves(data.model_dump(mode="json")):
        known |= unsigned(number_tokens(value))
    pdf_numbers = unsigned(number_tokens(NOT_VALUES.sub(" ", text)))
    return sorted(pdf_numbers - known)
