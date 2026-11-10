---
description: "Tasks for 005-ca-report"
---
# Tasks: CA Report
**Tests** inside each task. **Git**: none during the run.

- [X] T001 Constants (rate limit, file name pattern, labels); `schemas/report.py` ReportData
- [X] T002 `services/report_service.py` build_report_data + tests (values equal /dashboard and /fira)
- [X] T003 `ai/report_summary.py` + `prompts/report_summary.md` + fake LLM branch; tests (grounded, fail, invent → fallback)
- [X] T004 `reports/ca_report.py` + `reports/sections/*` (ReportLab, uncompressed); `routes/report.py` (`/report.pdf`, `/report/data`); tests: PDF text ⇄ report data (every number both ways), disclaimer/notes present, empty period
- [X] T005 Frontend DownloadReportButton on the dashboard + unit test; Playwright E9 download + PDF content check
- [X] T006 Review → fix; `check:all`; CHANGELOG; RUN_LOG
## Phase 1A hardening
- [X] T007 Journey E2E (seed → /pay → sync → dashboard → chat → FIRA → report)
- [X] T008 *(PayPal part done; real LLM call not run — no LLM_API_KEY; recorded in 001/003 research)* Real sandbox check (fresh token, Sync, one order create) + one real LLM call; record in research
- [X] T009 Whole-codebase review (pr-review-toolkit, security, constitution) → fix all
- [X] T010 `check:all` twice, both green
- [X] T011 `render.yaml` (backend, frontend, PostgreSQL 18), not deployed (002 T033)
- [X] T012 CHANGELOG + every tasks.md
