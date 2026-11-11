"""The PDF text helper reads a small known PDF exactly (verified before trusting it in SC-001)."""

import io

from reportlab.pdfgen.canvas import Canvas

from tests.fixtures.pdf_text import pdf_text, unescape


def test_unescape_handles_parens_backslash_and_octal() -> None:
    assert unescape(rb"a \(b\) \\ \227 \n") == b"a (b) \\ \x97 \n"


def test_reads_lines_from_an_uncompressed_pdf() -> None:
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pageCompression=0)
    canvas.drawString(40, 700, "Fee (net) INR 1,23,456.78 — done \\ x")
    canvas.drawString(40, 680, "Second – line")
    canvas.save()
    assert pdf_text(buffer.getvalue()) == "Fee (net) INR 1,23,456.78 — done \\ x Second – line"


def test_rupee_font_runs_read_as_the_rupee_sign() -> None:
    raw = b"BT /F2+0 10 Tf (\\001) Tj /F1 10 Tf (1,23,456.78 total) Tj ET"
    assert pdf_text(raw) == "₹1,23,456.78 total"
