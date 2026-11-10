"""CA report PDF rendered from hand-built ReportData (005 T004): labels, gain, empty, paging."""

import re

from app.common.constants import (
    NOT_TAX_ADVICE,
    REPORT_NO_PAYMENTS,
)
from app.reports.ca_report import render_pdf
from app.reports.labels import (
    REPORT_NO_FIRAS,
    REPORT_SUMMARY_AI_HEADING,
    REPORT_SUMMARY_CODE_HEADING,
    REPORT_TITLE,
)
from tests.fixtures.pdf_text import pdf_text
from tests.fixtures.report import report, row, totals
from tests.fixtures.report_checks import missing_from_pdf, numbers_not_in_data


def page_count(text: str) -> int:
    return len(re.findall(r"Page \d+", text))


def test_every_value_both_ways_and_labels() -> None:
    data = report()
    pdf = render_pdf(data)
    text = pdf_text(pdf)
    assert pdf.startswith(b"%PDF-")
    assert missing_from_pdf(data, text) == []
    assert numbers_not_in_data(data, text) == []
    assert REPORT_TITLE in text and "Period: This month (1 Nov 2026 – 10 Nov 2026)" in text
    assert "Generated 10 Nov 2026, 11:30 IST" in text
    assert "INR 1,68,000.00" in text and "USD 2,000.00" in text
    assert "FX loss (Simulated (sandbox)) INR 5,040.00" in text
    assert "Payments missing a FIRA 1" in text and "4 Nov 2026 Ava Stone TX-2" in text
    assert f"{REPORT_SUMMARY_CODE_HEADING} Summary text." in text


def test_disclaimer_is_in_the_body_and_on_every_page() -> None:
    clients = [row(f"c{i}", f"Client {chr(65 + i % 26)}") for i in range(80)]
    text = pdf_text(render_pdf(report(by_client=clients)))
    pages = page_count(text)
    assert pages > 1  # the client table split across pages
    assert text.count(NOT_TAX_ADVICE) == pages + 1
    assert text.count("Client Payments Income (INR)") == pages  # header repeated per page


def test_fx_gain_is_shown_as_gain() -> None:
    data = report(totals=totals(fx="-120.50"), by_month=[row("2026-11", "Nov 2026", fx="-120.50")])
    text = pdf_text(render_pdf(data))
    assert "FX gain (Simulated (sandbox)) INR 120.50" in text
    assert "120.50 gain" in text and "-120.50" not in text
    assert numbers_not_in_data(data, text) == []


def test_long_client_names_wrap_and_markup_is_escaped() -> None:
    name = "Very Long Client Name & Partners International Consulting Services Private Ltd"
    data = report(by_client=[row("c1", name)])
    text = pdf_text(render_pdf(data))
    assert name in text


def test_ai_summary_heading() -> None:
    summary = "For This month, income was ₹1,68,000.00."
    text = pdf_text(render_pdf(report(source="ai", text=summary)))
    assert f"{REPORT_SUMMARY_AI_HEADING} For This month, income was INR 1,68,000.00." in text


def test_empty_period_has_no_tables() -> None:
    fira = {"uploaded": 0, "matched": 0, "needs_review": 0, "missing": 0, "missing_payments": []}
    data = report(
        totals=None, gross_by_currency=[], by_month=[], by_client=[], fira=fira, excluded_count=0
    )
    text = pdf_text(render_pdf(data))
    assert REPORT_NO_PAYMENTS in text and REPORT_NO_FIRAS in text
    assert "By month" not in text and "By client" not in text and "INR" not in text
    assert NOT_TAX_ADVICE in text and "Sandbox data." in text
    assert numbers_not_in_data(data, text) == []
