"""FIRA matching (004, plan section 11)."""

from decimal import Decimal
from typing import Final

# --- FIRA matching (004, Phase 1A plan section 11, research R3) ---
FIRA_SCORE_REFERENCE: Final = 60
FIRA_SCORE_AMOUNT: Final = 25
FIRA_SCORE_DATE: Final = 15
FIRA_MATCHED_MIN: Final = 80
FIRA_REVIEW_MIN: Final = 50
FIRA_AMOUNT_TOLERANCE_PCT: Final = Decimal("1")
FIRA_DATE_WINDOW_DAYS: Final = 7
FIRA_WEEKLY_MIN_PAYMENTS: Final = 2
FIRA_INR_TOLERANCE_PCT: Final = Decimal("1")
FIRA_MAX_BYTES: Final = 5 * 1024 * 1024
FIRA_MAX_FILES: Final = 10
FIRA_PDF_SIGNATURE: Final = b"%PDF-"
FIRA_FILE_NAME_MAX: Final = 255
RATE_LIMIT_FIRA: Final = (10, 60)
FIRA_SAMPLES_DIR: Final = "sample_data/fira_samples"
FIRA_PDF_MEDIA_TYPE: Final = "application/pdf"
FIRA_FILE_SUFFIX: Final = ".pdf"
FIRA_REFERENCE_MAX: Final = 64
FIRA_REMITTER_MAX: Final = 200
FIRA_PURPOSE_CODE_MAX: Final = 8
FIRA_REASON_MAX: Final = 200
FIRA_AMOUNT_MAX: Final = Decimal("999999999999.99")  # fits NUMERIC(14,2)
FIRA_RATE_MAX: Final = Decimal("99999999.999999")  # fits NUMERIC(14,6)
FIRA_REMATCH_LOCK_KEY: Final = 7_004_001
FIRA_FAKE_MARKER: Final = "PAYLENS-FAKE-FIRA:"  # true fields of a generated demo PDF (/Subject)
FIRA_FIGURE_LABELS: Final = {
    "matched": "Matched", "needs_review": "Needs review", "missing": "Missing"
}  # fmt: skip
