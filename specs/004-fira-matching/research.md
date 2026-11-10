# Research: 004-fira-matching (2026-11-10)

## R1. Extraction call (claude-api reference, Messages API over httpx)
User content: `{"type":"document","source":{"type":"base64","media_type":"application/pdf","data":<b64, no newlines>}}`
then a text block with the instruction. Strict output with
`output_config: {"format": {"type": "json_schema", "schema": <schema, additionalProperties false, required>}, "effort": "low"}`;
the JSON arrives in the first `text` block → `json.loads` → Pydantic. Limits: 32 MB request, 600 pages —
our 5 MB file limit keeps us far below. Same wrapper, timeout and error mapping as 003 (R1 there).

## R2. No new packages
- Fake FIRA PDFs are generated with **ReportLab** (approved). Each fake PDF stores its true fields as JSON
  in the PDF `/Subject` metadata (plain text in the file). The **fake LLM** reads that marker from the
  PDF bytes — so E2E and tests exercise the full upload → extract → match path without a real LLM.
- File type check: first bytes `%PDF-` plus `.pdf`/`application/pdf`; size ≤ `FIRA_MAX_BYTES`.

## R3. Matching algorithm (pure engine)
1. Score every (FIRA, payment) pair with the same currency: +60 reference equal (case/space-insensitive
   to the PayPal transaction ID), +25 `|fira − gross| ≤ 1% × gross`, +15 `|fira date − payment IST date| ≤ 7 days`.
2. Each FIRA's best candidate (highest score, then closest date, then id). Greedy assignment in order of
   score desc: a payment taken by a higher-scoring FIRA is unavailable; the losing FIRA → needs review
   with reason "payment already matched" (F11).
3. Status by score: ≥ 80 matched, 50–79 needs review, < 50 → weekly check (FR-006): ISO week of the FIRA
   date ± same-currency unmatched payments whose gross sum is within 1% → needs review (kind weekly);
   else no match.
4. Payment status: linked to a matched FIRA → matched; linked to a needs-review FIRA → needs review;
   otherwise missing.
Decimals only; 1% computed as `abs(a − b) * 100 <= tolerance_pct * b`.

## R4. Demo samples
Generated from the seed rows (`SEED-0001…0024`), 21 PDFs:
- SEED-0001…0019: exact reference, amount and date → matched (score 100).
- SEED-0020: reference + date correct, amount 3% higher → 75 → needs review (F3 shape).
- SEED-0021: reference correct, amount 2% off, date 12 days later → 60 → needs review (F4 shape).
- SEED-0022…0024: no FIRA → missing.
