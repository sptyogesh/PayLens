"""CA report (005) and chat date bounds."""

from datetime import date
from typing import Final

# --- CA report (005, contracts/http-api.md) ---
REPORT_NO_PAYMENTS: Final = "No payments in this period."
RATE_LIMIT_REPORT: Final = (10, 60)
REPORT_FILE_NAME: Final = "paylens-ca-report-{period}-{day}.pdf"  # day = IST date, YYYY-MM-DD
REPORT_MEDIA_TYPE: Final = "application/pdf"
REPORT_DATA_MARKER: Final = "Report data (JSON):\n"  # first line of the summary request
REPORT_SUMMARY_MAX_CHARS: Final = 1200
# Report texts (headings, notes) live in app/reports/labels.py.

# --- Chat date bounds: explicit tool dates outside this range are rejected ---
CHAT_EARLIEST_DATE: Final = date(2000, 1, 1)
CHAT_LATEST_DATE: Final = date(2099, 12, 31)  # far-future questions still get "no data"
