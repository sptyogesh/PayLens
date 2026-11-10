"""The short summary, labelled by who wrote it (005 US2)."""

from reportlab.platypus import Paragraph

from app.reports.format import text
from app.reports.labels import (
    REPORT_SUMMARY_AI_HEADING,
    REPORT_SUMMARY_CODE_HEADING,
)
from app.reports.styles import BODY, HEADING, Flowable
from app.schemas.report import ReportData


def summary(data: ReportData) -> list[Flowable]:
    ai = data.summary.source == "ai"
    heading = REPORT_SUMMARY_AI_HEADING if ai else REPORT_SUMMARY_CODE_HEADING
    return [Paragraph(heading, HEADING), Paragraph(text(data.summary.text), BODY)]
