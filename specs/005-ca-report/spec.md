# Feature Specification: CA Report

**Feature Branch**: `001-paypal-sync` (owner decision) · **Created**: 2026-11-10 · **Status**: Draft

**Input**: "005 CA report: one-click PDF for a period with income summary, by month and client, fee and FX loss, FIRA status, data notes, disclaimer; numbers from code only; LLM writes a short summary with a plain fallback; download button; tests compare every PDF number with the API."

## Scope (Phase 1A) *(mandatory)*
- **Phase 1A item**: S2 CA report PDF.
- **Plan sections used**: 2 (S2 done-when), 4 (ReportLab), 11 (LLM explains only), 12 (`GET /report.pdf`), 18, constitution VII (disclaimer on every report).
- **Out of scope**: emailing the report, custom branding, multi-currency reporting currency other than INR, editing the summary.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Download a CA-ready PDF for a period (Priority: P1) 🎯
From the dashboard the freelancer clicks "Download CA report". A PDF for the selected period downloads with: title and period, generated time, income summary (payments, income INR, gross by currency), tables by month and by client, fee and FX loss (with Simulated (sandbox) label), FIRA status (counts + list of payments missing a FIRA), data notes (sandbox data, demo seed rows, simulated PayPal rate, ECB reference rates), and "Prepared from user data — not tax advice. Confirm with a CA."

**Acceptance Scenarios**:
1. **Given** seeded data, **When** the button is clicked, **Then** a PDF downloads (`application/pdf`, file name with the period) and every number in it equals the corresponding API value (`/dashboard`, `/fira`).
2. **Given** an empty period, **Then** the PDF still downloads and says there are no payments in the period (no zero tables pretending to be data).
3. **Given** any report, **Then** the disclaimer and data notes are present.

### User Story 2 - Short AI summary with a safe fallback (Priority: P2)
The report opens with a 2–4 sentence summary written by the AI from the report's numbers only. If the AI fails, times out, or writes a number not in the report, a plain summary written by code is used instead and marked as such.

**Acceptance Scenarios**:
1. **Given** the AI answers with grounded numbers, **Then** the summary appears, labelled "Summary (AI-written from the figures below)".
2. **Given** the AI fails or invents a number, **Then** the code summary appears, labelled "Summary", and the report still downloads.

### Edge Cases
Rate-unavailable rows listed as excluded count; FX gain shown as gain; long client names wrap; > 1 page tables paginate; no FIRAs uploaded → FIRA section says none uploaded and lists missing payments.

## Requirements *(mandatory)*
- **FR-001**: `GET /report.pdf?period=` (dashboard periods) returns a PDF; rate limited; never 500 because of the AI.
- **FR-002**: All numbers come from the same services as `/dashboard` and `/fira` (`report_data` built from them); the PDF renders strings only.
- **FR-003**: LLM summary through the single wrapper, given only the report data JSON; grounding check as in 003; fallback summary by code.
- **FR-004**: Every report includes the CA disclaimer, data notes and source labels.
- **FR-005**: Dashboard "Download CA report" button for the selected period; shows progress and errors.
- **FR-006**: `GET /report/data?period=` returns the JSON the PDF is built from (used by tests and the UI is not required to call it).

## Success Criteria
- **SC-001**: Tests prove every money/count/percent string in the PDF is present in the report data, and every report-data value appears in the PDF.
- **SC-002**: Report downloads in < 5 s locally with the fake LLM.

## Assumptions
- Periods = dashboard periods (this month, last 3 months, all time); default = dashboard selection.
- PDF built with ReportLab (approved), page compression off so tests can read text without a PDF parser.
- Times shown in IST.
