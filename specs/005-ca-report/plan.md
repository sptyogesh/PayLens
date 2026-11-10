# Implementation Plan: CA Report

**Branch**: `001-paypal-sync` | **Spec**: [spec.md](spec.md)

## Summary
`report_service.build_report_data(session, period, now)` composes dashboard totals/breakdowns
(`get_dashboard`), FIRA summary/missing list (`fira_service`), data notes and the disclaimer into a
`ReportData` model. `ai/report_summary.py` asks the LLM for a summary from that JSON (grounded via
`ai/grounding.py`; fallback by code). `reports/ca_report.py` (coordinator) renders sections from
`reports/sections/*` with ReportLab (`pageCompression=0`). Routes `GET /report.pdf`, `GET /report/data`.
Frontend: `DownloadReportButton` on the dashboard.

## Constitution Check
| # | Principle | Compliance | ✓ |
|---|---|---|---|
| I | Scope | S2 last | ✓ |
| II | Code computes | ReportData from existing services; LLM only narrative, grounded | ✓ |
| III | Money | Strings from MoneyOut; gains as gains | ✓ |
| IV | Types | ReportData Pydantic; response `application/pdf`; zod not needed for blob | ✓ |
| V | Verify | PDF text vs report data both directions; E9 download E2E | ✓ |
| VI | Security | No secrets; rate limit | ✓ |
| VII | Honest | Disclaimer + notes + Simulated labels in PDF | ✓ |
| IX | AI | Same wrapper, timeout, fallback, prompt file `prompts/report_summary.md` | ✓ |
| X–XIX | per project rules; no commits in run | ✓ |

## Reusable Parts
Used: `get_dashboard`, FIRA service, LLM wrapper, grounding, `NOT_TAX_ADVICE`, `rate_limit`, `Button`,
dashboard period state. New: `reports/sections/` renderer helpers; frontend `downloadFile` helper in `lib/api/client.ts`.

## File Split Plan
| Parent | Children |
|---|---|
| `reports/ca_report.py` | `reports/sections/{header,summary,income,breakdowns,leakage,fira,notes}.py`, `reports/styles.py` |
| `services/report_service.py` | `ai/report_summary.py` |
