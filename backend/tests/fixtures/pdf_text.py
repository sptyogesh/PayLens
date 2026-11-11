"""Read text from an uncompressed ReportLab PDF without a parser (005 SC-001).

ReportLab writes each text line as `(string) Tj`, with PDF string escapes (\\( \\) \\\\ and
octal \\ddd for non-ASCII characters in WinAnsi/cp1252). The strings are joined with spaces, so
a line break inside a paragraph reads as one space. Runs in an embedded subset font (name with
"+", only used for the rupee sign) read as "₹" and join the next string without a space.
"""

import re
from typing import Final

SHOW_TEXT: Final = re.compile(rb"\(((?:\\.|[^\\)])*)\)\s*Tj", re.DOTALL)
# A font change ("/F2+0 10 Tf") or a shown string ("(text) Tj"), in drawing order.
TOKEN: Final = re.compile(rb"/(\S+) [\d.]+ Tf|\(((?:\\.|[^\\)])*)\)\s*Tj", re.DOTALL)
SUBSET_MARK: Final = b"+"
RUPEE: Final = "₹"
ESCAPE: Final = re.compile(rb"\\([0-7]{1,3}|.)", re.DOTALL)
SIMPLE: Final = {b"n": b"\n", b"r": b"\r", b"t": b"\t", b"b": b"\b", b"f": b"\f"}
OCTAL: Final = 8


def unescape(raw: bytes) -> bytes:
    def replace(match: re.Match[bytes]) -> bytes:
        code = match.group(1)
        if code[:1].isdigit():
            return bytes([int(code, OCTAL)])
        return SIMPLE.get(code, code)

    return ESCAPE.sub(replace, raw)


def pdf_text(pdf: bytes) -> str:
    """Every shown string in drawing order, decoded as cp1252 and joined with single spaces."""
    font, text = b"", ""
    for match in TOKEN.finditer(pdf):
        if match.group(1) is not None:
            font = match.group(1)
            continue
        if SUBSET_MARK in font:
            text += " " + RUPEE * len(unescape(match.group(2)))
        else:
            part = unescape(match.group(2)).decode("cp1252")
            text += part if text.endswith(RUPEE) else " " + part
    return re.sub(r"\s+", " ", text).strip()
