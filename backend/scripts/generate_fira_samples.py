"""Generate demo FIRA PDFs for the demo seed rows (004 FR-011, research R4).

Usage (from backend/):
    uv run python -m scripts.generate_fira_samples              # → <repo>/sample_data/fira_samples
    uv run python -m scripts.generate_fira_samples --out DIR

21 PDFs: SEED-0001..0019 match exactly; SEED-0020 amount 3% higher (needs review); SEED-0021
amount 2% higher and 12 days late (needs review); SEED-0022..0024 get none (missing). Dates use
the same seed dates as `scripts.seed_demo`, so run both on the same day. Every PDF says it is a
demo sample, and its true fields sit in the /Subject metadata for the fake LLM.
"""

import argparse
import io
import json
from collections.abc import Sequence
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Final

from reportlab.lib.pagesizes import A4
from reportlab.pdfgen.canvas import Canvas

from app.common.constants import FIRA_FAKE_MARKER, FIRA_SAMPLES_DIR
from app.common.dates import ist_date, utc_now
from app.common.money import round_money, to_api_string, to_rate_string
from app.fakes.fx_fake import FAKE_RATES
from app.services.seed_service import months_before
from scripts.seed_data import SEED_CLIENTS, SeedRow, seed_rows

REPO_ROOT: Final = Path(__file__).resolve().parents[2]
DEMO_LABEL: Final = "DEMO SAMPLE — not a real bank document"
TITLE: Final = "Foreign Inward Remittance Advice (FIRA)"
REMITTER: Final = "PayPal (demo)"
PURPOSE_CODE: Final = "P0802"
DAYS_AFTER_PAYMENT: Final = 2
DAYS_LATE: Final = 12  # outside the 7-day window
# seed id → (amount factor, days after the payment): the two needs-review samples (F3, F4 shape).
ADJUSTED: Final = {
    "SEED-0020": (Decimal("1.03"), DAYS_AFTER_PAYMENT),
    "SEED-0021": (Decimal("1.02"), DAYS_LATE),
}
WITHOUT_FIRA: Final = frozenset({"SEED-0022", "SEED-0023", "SEED-0024"})
CURRENCY_INDEX: Final = 3
LEFT_MARGIN: Final = 72
TOP: Final = 770
LINE_HEIGHT: Final = 20
TITLE_FONT_SIZE: Final = 16
BODY_FONT_SIZE: Final = 11
LABELS: Final = {
    "reference_no": "Remittance reference",
    "remittance_date": "Remittance date",
    "foreign_amount": "Foreign amount",
    "currency": "Currency",
    "rate": "Exchange rate (INR per unit)",
    "inr_amount": "INR amount credited",
    "remitter": "Remitter",
    "purpose_code": "Purpose code",
}


def sample_fields(row: SeedRow, now: datetime) -> dict[str, str]:
    """The true FIRA fields for one seed payment (strings, as an extraction returns them)."""
    currency = SEED_CLIENTS[row.client_index][CURRENCY_INDEX]
    factor, days = ADJUSTED.get(row.seed_id, (Decimal(1), DAYS_AFTER_PAYMENT))
    amount = round_money(row.gross * factor)
    rate = FAKE_RATES[currency]
    paid_on = ist_date(months_before(now, row.months_ago, row.day))
    return {
        "foreign_amount": to_api_string(amount),
        "currency": currency,
        "inr_amount": to_api_string(amount * rate),
        "rate": to_rate_string(rate),
        "remittance_date": (paid_on + timedelta(days=days)).isoformat(),
        "reference_no": row.seed_id,
        "remitter": REMITTER,
        "purpose_code": PURPOSE_CODE,
    }


def fira_pdf_bytes(fields: dict[str, object], extra_lines: Sequence[str] = ()) -> bytes:
    """A one-page demo FIRA. `fields` go in the visible text and in the /Subject marker."""
    buffer = io.BytesIO()
    canvas = Canvas(buffer, pagesize=A4, invariant=1, pageCompression=0)  # plain-text page
    canvas.setTitle(TITLE)
    canvas.setSubject(FIRA_FAKE_MARKER + json.dumps(fields, sort_keys=True))
    canvas.setFont("Helvetica-Bold", TITLE_FONT_SIZE)
    canvas.drawString(LEFT_MARGIN, TOP, TITLE)
    canvas.setFont("Helvetica", BODY_FONT_SIZE)
    lines = [DEMO_LABEL, *(f"{LABELS.get(k, k)}: {v}" for k, v in fields.items()), *extra_lines]
    for number, line in enumerate(lines, start=2):
        canvas.drawString(LEFT_MARGIN, TOP - number * LINE_HEIGHT, line)
    canvas.showPage()
    canvas.save()
    return buffer.getvalue()


def generate(out_dir: Path, now: datetime) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for row in seed_rows():
        if row.seed_id in WITHOUT_FIRA:
            continue
        path = out_dir / f"fira-{row.seed_id}.pdf"
        path.write_bytes(fira_pdf_bytes(dict(sample_fields(row, now))))
        written.append(path)
    return written


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Generate demo FIRA PDFs for the seed rows.")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / FIRA_SAMPLES_DIR)
    args = parser.parse_args(argv)
    written = generate(args.out, utc_now())
    print(f"Wrote {len(written)} demo FIRA PDFs to {args.out}.")


if __name__ == "__main__":
    main()
