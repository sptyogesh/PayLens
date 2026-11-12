# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- README: live demo URL, demo video, features, tech stack, honest notes (ECB rates as mid-market proxy, simulated 3% spread, Gemini free-tier data use and rate limits, Render wake-up) and a short local-run guide; `docs/DEVPOST.md` submission text
- `SEED_DEMO_ON_STARTUP` setting (off by default, on in `render.yaml`): loads the labelled demo seed in the startup background thread, idempotent, for hosts without a shell; startup jobs (seed, sync, refresh) run in one thread so `/health` answers at once
- Free-tier wake-up handling: page loads retry while the backend starts (network error, 502/503/504, up to 90 s) and an app-wide "Waking up the PayLens server…" notice shows until `/health` answers, with a retry when it never does; actions that change data are never retried
- Frontend build guard (`prebuild`, `scripts/check-public-env.ts`): the build stops when a `NEXT_PUBLIC_*` value is missing or wrong, because Next.js bakes them in at build time
- README: Render deploy section (what runs on deploy, every environment variable per service and which are secret, free-plan sleep and database limits)
- Gemini adapter behind the single LLM wrapper (`generateContent` over httpx, no SDK): tools as function declarations, call ids and thought signatures sent back, PDFs as inline data, JSON schema output for FIRA reading; `LLM_PROVIDER` setting, provider detected from the key prefix when empty, per-provider default model (`gemini-3.6-flash`, free tier) and URL; startup refused when the key, model or URL belongs to another provider; README note on free-tier data use (specs/003-ask-your-money research R5)
- "The AI is busy, try again shortly" answer in the chat and on FIRA upload when the AI returns HTTP 429 (rate limit or free-tier quota) (specs/003-ask-your-money research R5)

- CA report PDF (`GET /report.pdf`, `GET /report/data`, "Download CA report" on the dashboard): income summary, by month and by client, fee and FX loss (Simulated (sandbox)), FIRA status with missing payments, data notes and the "not tax advice, confirm with a CA" disclaimer on every page; every number comes from the same code as the dashboard and FIRA page; the AI writes only a short grounded summary with a code-written fallback (specs/005-ca-report)
- `render.yaml` Render Blueprint (backend, frontend, PostgreSQL 18) with secrets as prompted values — not deployed yet (specs/002-leakage-dashboard US4)
- FIRA matching (`/fira`, `POST /fira/upload`, `GET /fira`): PDF-only uploads up to 5 MB with duplicate (SHA-256) rejection before any AI call; AI extraction into a strict JSON schema, validated in code; pure matching engine (reference +60, amount ±1% +25, date ±7 days +15; ≥80 matched, 50–79 needs review), one payment per FIRA, weekly sum-match; FIRA badges in the transactions grid; statuses recomputed after upload, sync, seed and /pay (specs/004-fira-matching)
- `fira_status` read-only chat tool; demo FIRA sample generator (`scripts.generate_fira_samples`, 21 PDFs in `sample_data/fira_samples`: 19 match, 2 need review, 3 payments missing) (specs/004-fira-matching)
- Shared `FileUpload` component with client-side type/size checks (specs/004-fira-matching)
- Ask Your Money chat (`/chat`, `POST /chat`): the AI answers only from read-only PayLens tools (`income_summary`, `fee_summary`, `get_transactions`), states period and currency, shows the figures behind each answer, says "data not available" when tools return nothing, adds the CA disclaimer to tax questions, and refuses to change data; every number in an answer is checked against tool results by code (specs/003-ask-your-money)
- Single LLM wrapper (Anthropic Messages API over httpx, model from `LLM_MODEL`), timeout and friendly fallback, rate limit on `POST /chat`, fake LLM for tests; `chat_messages` log table; `LLM_*` settings (specs/003-ask-your-money)
- Named periods (this/last month, last 3 months, this/last quarter, this/last financial year, all time) resolved in IST; shared leakage query reused by the dashboard and chat tools (specs/003-ask-your-money)
- Shared `TextArea` component; frontend constants split by area under `lib/constants/` (specs/003-ask-your-money)
- Per-payment leakage in INR (Phase 1A plan section 10): fee loss, FX loss (gains shown as gains), total leakage and leakage %, recalculated after sync, demo seed and `/pay`; "Rate unavailable" instead of numbers when no rate exists (specs/002-leakage-dashboard)
- Mid-market FX rates from Frankfurter (ECB reference rates, keyless), cached in a new `fx_rates` table; PayPal rate simulated as mid-market minus a 3% spread and labelled "Simulated (sandbox)"; `FX_MODE` / `FX_API_URL` settings (specs/002-leakage-dashboard)
- Leakage columns in the transactions grid with exact sorting (specs/002-leakage-dashboard)
- Leakage dashboard on the home page: five summary cards (total income INR, fee loss, FX loss, total leakage, leakage %), period filter (this month, last 3 months, all time, in IST), notes for payments without a rate and the simulated rate; `GET /dashboard?period=` (specs/002-leakage-dashboard)
- Shared `StatCard` and `SegmentedControl` UI components (specs/002-leakage-dashboard)
- Dashboard breakdown tables by month (IST) and by client, in API order; `autoHeight` option on the shared `DataGrid` (specs/002-leakage-dashboard)
- Demo seed history: 24 "Demo seed" transactions for 4 fictional clients over 4 months, idempotent, with `--reset` that removes only seed rows (`uv run python -m scripts.seed_demo`) (specs/001-paypal-sync)
- `/pay` sandbox checkout (PayPal JS SDK v6): order created and captured on the backend, payment recorded at once and linked to the later Transaction Search row; rate-limited `POST /pay/orders` and capture (specs/001-paypal-sync)
- Shared `TextField` form component (specs/001-paypal-sync)
- PayPal sandbox sync: Sync now and on startup, ≤31-day windows with full pagination, idempotent storage, client linking, non-payment events stored but excluded from income, one sync at a time, rate-limited `POST /sync`, `GET /sync/last`, `GET /transactions` (specs/001-paypal-sync)
- Transactions page with sync result and source-labelled grid (specs/001-paypal-sync)
- CI workflow running `npm run check:all` with a PostgreSQL 18 service on every push and PR (specs/001-paypal-sync)
- Project tooling: root check scripts, Husky hooks (lint-staged, commitlint, secretlint), file size check, Vitest + MSW, Playwright setup (specs/001-paypal-sync)
- Backend foundation: typed settings with sandbox-only guard, money/date/error/HTTP-retry/rate-limit helpers, `clients` and `transactions` tables, `GET /health` (specs/001-paypal-sync)
- Frontend foundation: shared UI components (Button, Card, Badge, MoneyText, DataGrid, Spinner, EmptyState, ErrorState, Disclaimer), app shell with demo-mode banner, typed API client with zod validation (specs/001-paypal-sync)

### Fixed

- CI: the Playwright browser install tries twice with system packages (5 minutes each), then installs the browser alone, so an Ubuntu mirror outage on the GitHub runner no longer fails the run
- Settings errors at startup no longer print the input values (they could show `LLM_API_KEY` or PayPal secrets) (specs/003-ask-your-money research R5)
- Rate limits behind Render's proxy: the client address is set by uvicorn's proxy-headers middleware, which accepts `X-Forwarded-For` only from proxies listed in the new `FORWARDED_ALLOW_IPS` setting (Render's private ranges in `render.yaml`), so each real client has its own limit and client-sent entries are ignored; replaces `TRUST_PROXY_HEADERS`
- Rate limits use the address Render's proxy appends (the last `X-Forwarded-For` entry), so a spoofed header can no longer bypass them; LLM routes (`/chat`, `/fira/upload`, `/report*`) also share one global cap; old limiter windows are pruned; FIRA uploads limited to 10 per minute; sync start limited to the last 3 years (Phase 1A hardening)
- `/chat` no longer returns 500 for extreme dates: tool dates are limited to 2000-01-01–2099-12-31 and any period that cannot be resolved becomes a tool input error the assistant can recover from
- Sync robustness: a database error or non-JSON PayPal page in one window stops the run with a coded error (`SYNC_STORE_FAILED` / `PAYPAL_REJECTED`) while earlier windows stay stored; an unexpected error records the real partial result; `POST /sync` recalculates leakage even when the sync fails; a `/pay` payment stored during a sync no longer aborts the window (treated as an update)
- Non-JSON PayPal responses on order create/capture return `PAYPAL_REJECTED` instead of a 500; capturing an already-paid order returns `ORDER_ALREADY_CAPTURED` ("This order was already paid.") instead of "No payment was made"
- Transactions page asks for the largest page (`?limit=200`) and says "Showing X of Y transactions (newest first)" when more exist, instead of silently stopping at 100 (frontend)
- Chat: a failed question is marked "Not answered" with its own Try again, is left out of the next question's history, and a retried answer appears under its question (frontend)
- Pay (test mode) button is disabled while a payment is processing, so a double click creates one order; `DataGrid` keeps one `getRowId` function for the grid's life (no AG Grid initial-property warning) (frontend)
- Frontend cleanup: `Disclaimer` takes a `kind` or explicit `text` and is used for the chat disclaimer and the dashboard simulated-rate note; `formatDay` moved to `lib/format.ts`; FIRA reason column width is a named constant; ESLint `max-params` (5); shared E2E helpers `formatReportInr`, `pdfText` and `e2e/support/fira.ts`; new E2E tests for chat under AI failure (003 US3), FIRA status in chat (004 US3) and the AI report summary (005 US2)
- Database connections no longer use server-side prepared statements, which failed with `NotSupportedError` after the E2E database was recreated under a running backend (specs/002-leakage-dashboard)
- API times are always UTC with `Z`; sync period and start time were returned in the database server's local time zone (specs/001-paypal-sync)
- Backend tests no longer read `backend/.env`, so local PayPal credentials never reach a test run

### Changed

- Demo seed rows and `seed_demo()` moved from `backend/scripts/` into `app/services/` so the app can load them at startup; `scripts.seed_demo` uses them; the network error message mentions a server that is waking up
- HTTP 429 from the AI service is reported as "busy" (`LLM_BUSY`) instead of a generic outage; `LLM_MODEL` and `LLM_API_URL` default per provider; `render.yaml` uses Gemini (`gemini-3.6-flash`) (specs/003-ask-your-money research R5)
- CA report shows INR amounts with "₹" using an embedded Noto Sans font (SIL OFL 1.1, licence in `backend/app/reports/fonts/OFL.txt`) for the rupee sign only; other text stays in the built-in font (specs/005-ca-report)
- `frontend/.gitignore` ignores the `AGENTS.md` that `next dev` writes into `frontend/`
- Backend constants split into `app/common/constants/` (core, leakage, chat, fira, report) behind the same import path; one `SIMULATED_LABEL`; LLM adapter selection moved to `api/deps.py` (removes an import cycle); package-entry imports; ReportLab type stubs handled by a mypy override (Phase 1A hardening)
- Backend: `answer_question` takes the validated `ChatIn` (5 parameters max); sync, checkout, pay and FIRA service code imports through the `app.paypal` and `app.engine.fira_match` package entries
- `.gitignore`: anchor Python `lib/` rules to the repo root so `frontend/lib/` is tracked; add Node/Next.js patterns
