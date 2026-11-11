"""CA report PDF coordinator (005 FR-001, FR-002): renders ReportData strings, never computes.

Page compression is off so the text stays readable in the PDF bytes (tests check every number
without a PDF parser). The disclaimer is printed in the body and on every page footer.
"""

import io
from collections.abc import Callable
from typing import Any

from reportlab.platypus import SimpleDocTemplate

from app.reports.labels import (
    REPORT_TITLE,
)
from app.reports.sections import SECTIONS
from app.reports.styles import (
    FOOTER_FONT,
    FOOTER_FONT_SIZE,
    FOOTER_Y,
    MARGIN,
    PAGE_LABEL,
    PAGE_SIZE,
    Flowable,
)
from app.schemas.report import ReportData

PageCallback = Callable[[Any, Any], None]


def page_footer(disclaimer: str) -> PageCallback:
    def draw(canvas: Any, doc: Any) -> None:
        canvas.saveState()
        canvas.setFont(FOOTER_FONT, FOOTER_FONT_SIZE)
        canvas.drawString(MARGIN, FOOTER_Y, disclaimer)
        canvas.drawRightString(PAGE_SIZE[0] - MARGIN, FOOTER_Y, PAGE_LABEL.format(page=doc.page))
        canvas.restoreState()

    return draw


def render_pdf(data: ReportData) -> bytes:
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=PAGE_SIZE,
        pageCompression=0,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=REPORT_TITLE,
    )
    story: list[Flowable] = [flowable for section in SECTIONS for flowable in section(data)]
    footer = page_footer(data.disclaimer)
    document.build(story, onFirstPage=footer, onLaterPages=footer)
    return buffer.getvalue()
