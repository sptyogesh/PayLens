"""Excluded counts, data notes and the disclaimer (Principle VII)."""

from typing import Final

from reportlab.platypus import Paragraph

from app.reports.format import text
from app.reports.styles import BODY, HEADING, Flowable, key_values
from app.schemas.report import ReportData

HEADING_TEXT: Final = "Data notes"
EXCLUDED: Final = "Payments excluded (no exchange rate)"
NOT_CALCULATED: Final = "Payments not calculated (fee above gross)"
BULLET: Final = "- {note}"
DISCLAIMER: Final = "<b>{text}</b>"


def notes(data: ReportData) -> list[Flowable]:
    counts = key_values(
        [(EXCLUDED, str(data.excluded_count)), (NOT_CALCULATED, str(data.not_calculated_count))]
    )
    lines = [Paragraph(BULLET.format(note=text(note)), BODY) for note in data.notes]
    disclaimer = Paragraph(DISCLAIMER.format(text=text(data.disclaimer)), BODY)
    return [Paragraph(HEADING_TEXT, HEADING), counts, *lines, disclaimer]
