"""Title, period (label and IST dates) and generated time."""

from typing import Final

from reportlab.platypus import Paragraph

from app.common.dates import IST, ist_date
from app.common.periods import range_label
from app.reports.labels import (
    REPORT_TITLE,
)
from app.reports.styles import BODY, MUTED_BODY, TITLE, Flowable
from app.schemas.report import ReportData

PERIOD_LINE: Final = "Period: {label}"
PERIOD_DATES: Final = " ({dates})"
GENERATED_LINE: Final = "Generated {when} IST"
GENERATED_FORMAT: Final = "%d %b %Y, %H:%M"


def period_text(data: ReportData) -> str:
    period = data.period
    line = PERIOD_LINE.format(label=period.label)
    if period.start is not None and period.end is not None:
        dates = range_label(ist_date(period.start), ist_date(period.end))
        line += PERIOD_DATES.format(dates=dates)
    return line


def header(data: ReportData) -> list[Flowable]:
    when = data.generated_at.astimezone(IST).strftime(GENERATED_FORMAT)
    return [
        Paragraph(REPORT_TITLE, TITLE),
        Paragraph(period_text(data), BODY),
        Paragraph(GENERATED_LINE.format(when=when), MUTED_BODY),
    ]
