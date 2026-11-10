# Feature Specification: FIRA Matching

**Feature Branch**: `001-paypal-sync` (owner decision)

**Created**: 2026-11-10 · **Status**: Draft

**Input**: "004 FIRA matching: PDF upload (PDF only, size limit, duplicate hash rejected); LLM extraction into a strict schema; code validation and matching with the scoring constants, weekly sum-match, one transaction per FIRA; FIRA page and grid badges; fira_status chat tool; script for fake FIRA PDFs in sample_data/fira_samples (most match, 2 need review, 3 missing); tests F1–F14, E1–E6."

## Scope (Phase 1A) *(mandatory)*

- **Phase 1A item**: S1 FIRA upload + AI extraction + matching (should-have; M1–M3 done first).
- **Plan sections used**: 2 (S1 done-when), 7 (`fira_documents`, `fira_matches`, `fira_status`), 9 (fake FIRA PDFs: most match, 2 needs review, 3 missing), 11 (extraction schema, scoring 60/25/15, thresholds 80/50, `fira_status()` tool), 12 (`POST /fira/upload`, `GET /fira`), 18.
- **Out of scope**: real bank FIRAs, OCR of scanned images beyond what the LLM reads, editing extracted fields by hand, deleting FIRAs (except via the demo reset script), email ingestion.

## User Scenarios & Testing *(mandatory)*

A FIRA (Foreign Inward Remittance Advice) is the bank's proof that a foreign payment reached India in INR; freelancers need one per export payment for GST/tax records.

### User Story 1 - Upload FIRAs and see them matched to payments (Priority: P1) 🎯

The freelancer uploads one or more FIRA PDFs. PayLens reads each with AI into fixed fields (foreign amount, currency, INR amount, date, reference, remitter, purpose code), checks them in code, and matches each FIRA to a payment with the scoring rules. The FIRA page lists every FIRA with its status (Matched / Needs review / No match), score and linked payment, and the transactions grid shows a FIRA badge (Matched / Needs review / Missing) on every income row.

**Independent Test**: Seed demo data, generate the sample FIRAs, upload them on `/fira`, and check most are Matched, 2 Need review and 3 payments show Missing.

**Acceptance Scenarios**:
1. **Given** a FIRA whose reference, amount (±1%) and date (±7 days) match a payment, **When** uploaded, **Then** it is Matched (score 100) and the payment's badge is Matched.
2. **Given** a FIRA with reference + amount but date 10 days off, **When** uploaded, **Then** Matched with score 85 (F2).
3. **Given** a FIRA with reference + date but amount 3% off, **Then** Needs review, score 75 (F3).
4. **Given** a payment with no FIRA, **Then** its badge is Missing (F13).
5. **Given** a FIRA whose total equals the sum of one week's payments in that currency (±1%), **Then** Needs review with all linked payments listed (F12).
6. **Given** two FIRAs claiming the same payment, **Then** only the higher score keeps it; the other is Needs review (F11).

### User Story 2 - Safe uploads and honest extraction (Priority: P1)

Only PDFs up to the size limit are accepted; the same file twice is rejected as a duplicate. If the AI output is missing fields or inconsistent (INR amount not ≈ foreign amount × rate), the FIRA is Needs review, never guessed. Instructions written inside a PDF are treated as text.

**Acceptance Scenarios**:
1. **Given** a non-PDF or a file over 5 MB, **When** uploaded, **Then** it is rejected with a clear message before any AI call (E6, F14 for duplicates), also checked in the browser.
2. **Given** AI output missing a required field (E2) or with inconsistent INR (E3), **Then** status Needs review with the reason.
3. **Given** AI output that is not valid JSON (E4) or the AI is down, **Then** the FIRA is not stored and the user sees a friendly error; other files in the same upload still process.
4. **Given** a PDF containing "ignore previous instructions…" (E5), **Then** the output schema is unchanged and nothing else happens.

### User Story 3 - Ask about FIRA status in chat (Priority: P2)

The chat agent gains a read-only `fira_status` tool: counts and lists of matched, needs-review and missing payments for a period.

**Acceptance Scenarios**:
1. **Given** uploaded FIRAs, **When** asking "Which payments are missing a FIRA?", **Then** the answer lists exactly the payments the FIRA page shows as Missing.

### Edge Cases
- Currency differs → no match (F10). Exactly 1.00% off counts (F6); 1.01% does not (F7); exactly 7 days counts (F8); 8 does not (F9).
- FIRA with no reference: can still score 40 (amount + date) → no match (F5).
- Payment pending/denied, non-income rows: no FIRA badge.
- Seed reset or new sync: statuses recomputed for all rows.

## Requirements *(mandatory)*

- **FR-001**: The page uploads 1–10 PDF files, one `POST /fira/upload` request each (raw PDF body); each checked for PDF signature and ≤ 5 MB, and SHA-256 duplicate against stored FIRAs, before any AI call; per-file result returned.
- **FR-002**: Extraction uses the single LLM wrapper with the PDF as a document input and a strict JSON schema; output validated by Pydantic; invalid → needs review or rejected per US2.
- **FR-003**: Validation in code: required fields present, currency ISO, amounts > 0, `|inr_amount − foreign_amount × rate| ≤ 1%` when a rate is given.
- **FR-004**: Matching in a pure engine with constants: reference +60, amount within ±1% +25, date within ±7 days +15; ≥ 80 matched, 50–79 needs review, < 50 no match; currency mismatch → 0.
- **FR-005**: Each payment is linked to at most one FIRA; conflicts resolved by higher score (ties: earlier FIRA), losers become needs review.
- **FR-006**: Weekly sum-match: an unmatched FIRA whose amount equals (±1%) the sum of one ISO week's eligible payments in its currency becomes needs review with all those payments linked.
- **FR-007**: `transactions.fira_status` for every eligible payment: matched, needs_review, or missing; recomputed after every upload, sync, seed and /pay.
- **FR-008**: `GET /fira` lists FIRAs (file name, extracted fields, status, score, reason, linked payments) and summary counts.
- **FR-009**: FIRA page: upload control (client-side type/size checks), list with status badges, summary counts; transactions grid FIRA column with badges.
- **FR-010**: Read-only chat tool `fira_status(period)` returning counts and lists by code.
- **FR-011**: Script generates fake FIRA PDFs for the demo seed into `sample_data/fira_samples/` (most match, 2 need review, 3 seed payments without FIRA).
- **FR-012**: Uploaded file bytes are not kept; only hash, name and extracted fields are stored (nothing in a public path).

### Key Entities
- **FIRA document**: file name, SHA-256 hash (unique), extracted fields, status (matched / needs_review / no_match), score, reason.
- **FIRA match**: FIRA, payment, score, kind (direct / weekly).

## Success Criteria *(mandatory)*
- **SC-001**: With the sample FIRAs, the FIRA page shows the exact expected split (all but 2 matched, 2 needs review; 3 payments missing).
- **SC-002**: F1–F14 and E1–E6 pass.
- **SC-003**: No AI call happens for rejected files.

## Assumptions
- Reference on the demo FIRAs is the PayPal transaction ID (seed ID for demo rows).
- Rate on the FIRA is INR per foreign unit; if absent, the INR consistency check is skipped.
- Date window compares the FIRA date with the payment's IST date.
- Matching is recomputed globally (all FIRAs vs all eligible payments) after each change — demo scale.
- Demo reset (`scripts.seed_demo --reset`) also clears FIRAs.
