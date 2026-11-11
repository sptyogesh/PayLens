# Phase 1A continuous run log

One entry per user story: what was built, review fixes, verification counts. Newest last.
All work is on branch `001-paypal-sync`, uncommitted unless noted.

## 002 US2 — summary cards and period filter (committed 3a87f00, approved)

- Built: `GET /dashboard?period=`, five cards, period filter, notes, `StatCard`, `SegmentedControl`.
- Review fixes: cards add up exactly (rounding), invalid rows counted separately, sources only from
  included rows, stale leakage cleared on change, loading state on period switch, layering.
- Verification: backend 267, frontend unit 93, Playwright 28 — all passed.

## 002 US3 — breakdown by month and by client

- Built: month and client breakdown tables (shared `DataGrid` with new `autoHeight` option), label
  column width constant, E2E checks that rows appear in API order and amounts match.
- Visual check: dashboard screenshots at 1280 px and 390 px (project Playwright; the Playwright MCP
  browser crashes on this machine's GTK settings). Fix found: long client names truncated → wider
  label column.
- Review fixes (pr-review-toolkit code-reviewer): CHANGELOG entry, magic number → constant, row-order
  assertions.
- 002 US4: render.yaml moved to the Phase 1A hardening pass; README/deploy deferred by owner.
- Verification: lint, typecheck (136 files), size OK; backend 267; frontend unit 96; Playwright 30 —
  all passed.

## 003 US1–US3 — Ask Your Money (chat)

- Spec Kit: spec, research (Messages API over httpx, `anthropic-version: 2026-10-21`, model
  `claude-opus-5-5`, no temperature/tool_choice/thinking params), plan, contracts, tasks; analyze fix:
  shared `app/ai/types.py` written by the main agent before parallel work.
- Built in parallel (3 subagents, disjoint files): A — named IST periods, `leakage_query` (dashboard
  refactored onto it), tools `income_summary` / `fee_summary` / `get_transactions`; B — LLM wrapper,
  fake LLM, agent loop, grounding, answer rules, prompt file, `/chat` route, `chat_messages`;
  C — chat page, `TextArea`, chat schemas, E2E. Main agent: integration, `lib/constants/` split
  (file was at the 200-line limit), contract check, safety tests (N1–N5, T1, T2, injection).
- Review fixes (pr-review-toolkit silent-failure-hunter + code-reviewer):
  - Grounding rewritten: numbers inside client names / labels no longer count (injection bypass);
    small integers next to `%`/`₹`/currency codes must be grounded; integer parts no longer accepted
    (no rounding/truncation); negative values need a minus or the word "gain"; FY "2026-27" allowed.
  - Whole-answer deadline (`CHAT_DEADLINE_S`) with per-call timeout = remaining time; client-side
    abort (`apiPost` timeout) with a "took too long" message.
  - Logging: fallback reasons and stop reason, config errors at ERROR, storage and unhandled errors
    with tracebacks; injection test tightened.
  - `agent.py` split (217 → 159 lines) into `outcome.py`.
- Visual check (screenshots 1280/390): chat answers, "Based on" figures, periods, CA disclaimer OK;
  no console errors on any page.
- Verification: lint/typecheck (190 files)/size OK; backend 485; frontend unit 117; Playwright 40.
- Note: `LLM_API_KEY` / `LLM_MODEL` are not yet in `backend/.env`; with `LLM_MODE=http` (default) the
  backend now refuses to start without a key (constitution: fail fast). Real LLM check is pending.

## 004 US1–US3 — FIRA matching

- Spec Kit: spec, research (document block + `output_config.format` json_schema; fake FIRAs carry their
  truth in the PDF /Subject so the fake LLM can "read" them), data model, contract, plan, tasks.
  Analyze fixes: `python-multipart` is not installed (no unapproved install) → upload is one raw
  `application/pdf` body per request; sample design clarified (19 match, 2 needs review, 3 missing).
- Built in parallel: engine subagent (pure `engine/fira_match`, F1–F13, 100% coverage); backend
  subagent (models, extraction, upload service, rematch, `safe_refresh` after sync/seed//pay,
  `fira_status` chat tool, sample generator + 21 PDFs; resumed once after a usage limit); frontend
  subagent (`FileUpload`, FIRA page, grid FIRA column, E2E). Main agent: constants, integration,
  contract checks, data-model notes, CHANGELOG.
- Review fixes (silent-failure-hunter + code-reviewer): impossible extracted values (≤ 0, too large,
  non-ISO currency, over-long texts) are stored empty/shortened as Needs review instead of a 500 or a
  false "already uploaded"; only a real duplicate-hash conflict counts as duplicate; a failed rematch
  is reported ("matching runs again") instead of a wrong "no match"; rematch serialised with an
  advisory lock; React key fix. Not changed: refresh failures after sync//pay are logged with
  traceback but not shown in the sync response (known limitation).
- Visual check: /fira at 1280/390 shows 19 / 2 / 0 / 3, badges, reasons, missing list. A hydration
  warning seen once came from a stale dev cache (server HTML confirmed correct; 0 errors on re-check).
- Verification: lint/typecheck (211 files)/size OK; backend 559; frontend unit 144; Playwright 50.

## 005 US1–US2 — CA report

- Spec Kit: spec, plan, contract, tasks (report data endpoint added so tests compare PDF ⇄ API).
- Built in parallel: backend subagent (report data from the same services as `/dashboard` and `/fira`,
  ReportLab PDF with `pageCompression=0`, sections, AI summary grounded with a code fallback, routes,
  PDF text reader for tests, both-direction number check); frontend subagent (`apiGetBlob`,
  `downloadBlob`, "Download CA report" button, E9). Main agent: integration, E2E amount check,
  CHANGELOG, `render.yaml` + blueprint test.
- Notes: amounts read `₹1,23,456.78`; the ₹ glyph comes from an embedded Noto Sans (OFL) font (hardening fix 3; earlier `INR 1,23,456.78`).
- Review fixes (code-reviewer): report timestamps (`generated_at`, `start`, `end`) no longer ground
  numbers (only their years) — invented summary figures could pass; "lakh/crore/k/rupees/Rs" make a
  number an amount; currency-code prefix made case-sensitive (it matched ordinary words); names the PDF
  font cannot draw print as "?" with a data note; "1 payment is" singular; ai → reports import removed.
- Visual check: generated an all-time report (21 FIRAs) and rendered both pages to PNG — sections,
  tables, labels, disclaimer footer on every page OK.
- Verification (before the review fixes): backend 606, frontend unit 159, Playwright 54; after the
  fixes backend 608 (full loop re-run in hardening).

## Phase 1A hardening

- Journey E2E (`e2e/journey.spec.ts`): seed → /pay (test mode) → Sync now → dashboard → chat FX loss =
  dashboard → 21 FIRAs uploaded (19 matched) → CA report total leakage = dashboard. Passes (chromium;
  skipped on the mobile project by design).
- Real sandbox (fresh token): reporting scope now present; Transaction Search works (1 row, T1900
  balance adjustment, correctly "other"); order create OK. Real LLM call not run: no `LLM_API_KEY` in
  `backend/.env`. Both recorded in research.md.
- `render.yaml` (PostgreSQL 18, backend via uv, frontend via npm; secrets `sync: false`) + test.
- Whole-codebase review (4 parallel reviewers: backend, frontend, security, constitution) → fixed:
  rate-limit spoofing via X-Forwarded-For (last entry, global LLM cap, pruning, FIRA 10/min, sync
  ≤ 3 years); /chat 500 on extreme dates; sync partial results and refresh on unexpected errors,
  non-JSON PayPal bodies, concurrent /pay insert; ORDER_ALREADY_CAPTURED message; answer_question
  ≤ 5 params; package-entry imports; LLM adapter cycle removed; type-ignore reasons; magic numbers;
  one SIMULATED_LABEL; test builders ≤ 5 params; backend constants split into a package; frontend:
  full transactions page (limit 200 + "Showing X of Y"), per-message chat retry, pay double-click
  guard, stable grid row ids, Disclaimer reuse, max-params lint rule, E2E for 003 US3, 004 US3,
  005 US2.
- Final verification, two consecutive runs, both green: lint/typecheck (252 files)/size OK; backend
  635 passed (98% coverage); frontend unit 169 passed; Playwright 61 passed, 1 skipped (journey on
  the mobile project, by design). No flaky tests.

## Gemini adapter (owner choice: free tier) — uncommitted
- Built: `GeminiLlm` behind the single wrapper (generateContent over httpx; translation in
  `gemini_format.py`), provider selection (`LLM_PROVIDER` or key prefix; startup refused when key,
  model or URL belong to another provider; only the provider's own https URL), default model per
  provider, 429 → "The AI is busy, try again shortly" (chat, FIRA), settings errors hide inputs.
- Docs: Google's generateContent docs read 2026-11-11 (research R5). Default `gemini-3.6-flash`
  (3.8 Flash overloaded on the day).
- Review fixes (code-reviewer): URL check by parsed host/scheme (variants of the other provider's
  URL and http were accepted); key whitespace stripped before prefix detection; FIRA reads all text
  parts.
- Real check: chat answer equals the dashboard (FX loss 49750.42, 24 payments); FIRA SEED-0001 all
  fields correct.
