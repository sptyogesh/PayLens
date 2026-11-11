"""Page, text and table styles for the CA report PDF (ReportLab built-in Helvetica, A4).

The built-in fonts keep text readable in the uncompressed PDF (tests read it without a parser).
The ₹ sign alone comes from the embedded Noto Sans (rupee_font.py).
"""

from typing import Any, Final

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, Table, TableStyle

Flowable = Any  # ReportLab ships no type hints
PAGE_SIZE: Final = A4
MARGIN: Final = 40
FOOTER_Y: Final = 22
FOOTER_FONT: Final = "Helvetica"
FOOTER_FONT_SIZE: Final = 7
PAGE_LABEL: Final = "Page {page}"
TABLE_FONT_SIZE: Final = 8
CELL_LEADING: Final = 10
KEY_WIDTH: Final = 200
VALUE_WIDTH: Final = 160
CELL_PADDING: Final = 3
GRID_WIDTH: Final = 0.25
HEADER_FILL: Final = colors.HexColor("#EEF1F5")
GRID_COLOR: Final = colors.HexColor("#C5CCD6")
MUTED: Final = colors.HexColor("#5A6472")

_SHEET: Final = getSampleStyleSheet()
TITLE: Final = ParagraphStyle("ReportTitle", parent=_SHEET["Title"], alignment=0)
HEADING: Final = _SHEET["Heading2"]
BODY: Final = _SHEET["BodyText"]
MUTED_BODY: Final = ParagraphStyle("Muted", parent=BODY, textColor=MUTED)
CELL: Final = ParagraphStyle("Cell", parent=BODY, fontSize=TABLE_FONT_SIZE, leading=CELL_LEADING)
NUMBER_CELL: Final = ParagraphStyle("NumberCell", parent=CELL, alignment=2)
BOLD_CELL: Final = ParagraphStyle("BoldCell", parent=CELL, fontName="Helvetica-Bold")


def table(rows: list[list[Flowable]], widths: list[float] | None = None) -> Flowable:
    """A bordered table whose first row is a header repeated on every page it spans."""
    style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), GRID_WIDTH, GRID_COLOR),
            ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), CELL_PADDING),
            ("BOTTOMPADDING", (0, 0), (-1, -1), CELL_PADDING),
        ]
    )
    return Table(rows, colWidths=widths, repeatRows=1, style=style, hAlign="LEFT")


def key_values(pairs: list[tuple[str, str]]) -> Flowable:
    """A two-column label/value table (no header row)."""
    rows = [[Paragraph(label, BOLD_CELL), Paragraph(value, NUMBER_CELL)] for label, value in pairs]
    style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), GRID_WIDTH, GRID_COLOR),
            ("TOPPADDING", (0, 0), (-1, -1), CELL_PADDING),
            ("BOTTOMPADDING", (0, 0), (-1, -1), CELL_PADDING),
        ]
    )
    return Table(rows, colWidths=[KEY_WIDTH, VALUE_WIDTH], style=style, hAlign="LEFT")
