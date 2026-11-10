---
description: "Tasks for 004-fira-matching"
---
# Tasks: FIRA Matching
**Tests** inside each task. **Git**: none during the run. Branch `001-paypal-sync`.

## Phase 1: Setup
- [X] T001 Constants (scores, thresholds, tolerance, window, limits, rate limit, sample dir); upload uses raw PDF bodies (no python-multipart)
## Phase 2: Foundational
- [X] T002 [P] [A] Pure engine `app/engine/fira_match/{__init__,types,score,match,weekly}.py`; tests F1–F13 + property tests in `tests/unit/engine/fira_match/`
- [X] T003 [P] [B] Models `fira_documents`, `fira_matches` (+ enums), constraint tests
## Phase 3: US1 upload + match (P1)
- [X] T004 [B] `app/ai/fira_extract.py` + `app/ai/prompts/fira_extract.md` (document block, json_schema output, Pydantic, validation E1–E3); fake LLM extraction from the embedded marker
- [X] T005 [B] `services/fira_rematch.py` (engine → tables + transactions.fira_status), hooked after upload, sync, seed, /pay and seed reset
- [X] T006 [B] `services/fira_service.py` + `schemas/fira.py` + `routes/fira.py` (`POST /fira/upload`, `GET /fira`), `fira_status` on `/transactions`; API tests
- [X] T007 [B] `scripts/generate_fira_samples.py` → `sample_data/fira_samples/` (21 PDFs per research R4) + test
- [X] T008 [P] [C] Frontend: `components/ui/FileUpload` (U10), `features/fira/**`, `app/fira/page.tsx`, nav, grid FIRA column with `Badge`, unit tests
- [X] T009 Integrate; Playwright `e2e/fira.spec.ts` E7 (upload samples → split), E8 (invalid file); review → fix; `check:all`; RUN_LOG
## Phase 4: US2 safety (P1)
- [X] T010 Tests E4–E6, F14, injection PDF, partial batch failure; review → fix; `check:all`; RUN_LOG
## Phase 5: US3 chat tool (P2)
- [X] T011 `fira_status` tool in the chat registry + fake LLM keyword + golden test; E2E chat question; review → fix; `check:all`; CHANGELOG; RUN_LOG
