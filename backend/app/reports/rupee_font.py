"""The ₹ sign in the CA report: Noto Sans (SIL OFL 1.1, see fonts/OFL.txt), embedded for that one
glyph only. All other text stays in the built-in Helvetica, so it remains readable in the
uncompressed PDF (tests and the E2E read numbers straight from the file)."""

from pathlib import Path
from typing import Final

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

RUPEE: Final = "₹"
RUPEE_FONT: Final = "PayLensRupee"
RUPEE_FONT_FILE: Final = Path(__file__).parent / "fonts" / "NotoSans-Regular.ttf"
RUPEE_MARKUP: Final = f'<font name="{RUPEE_FONT}">{RUPEE}</font>'

if RUPEE_FONT not in pdfmetrics.getRegisteredFontNames():
    pdfmetrics.registerFont(TTFont(RUPEE_FONT, str(RUPEE_FONT_FILE)))
