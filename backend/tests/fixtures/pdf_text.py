"""Read text from an uncompressed ReportLab PDF without a parser (005 SC-001).

ReportLab writes each text line as `(string) Tj`, with PDF string escapes (\\( \\) \\\\ and
octal \\ddd for non-ASCII characters in WinAnsi/cp1252). The strings are joined with spaces, so
a line break inside a paragraph reads as one space.
"""

import re
from typing import Final

SHOW_TEXT: Final = re.compile(rb"\(((?:\\.|[^\\)])*)\)\s*Tj", re.DOTALL)
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
    parts = [unescape(raw).decode("cp1252") for raw in SHOW_TEXT.findall(pdf)]
    return re.sub(r"\s+", " ", " ".join(parts))
