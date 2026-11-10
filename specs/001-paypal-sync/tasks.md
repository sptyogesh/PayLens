---

description: "Task list for 001-paypal-sync (PayLens)"
---

# Tasks: PayPal Sandbox Sync

**Input**: Design documents from `/specs/001-paypal-sync/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: REQUIRED (constitution Principle V).
- Every implementation task writes its own tests in the same task, based on the spec and the
  constitution's **Required Test Cases** (IDs such as P1 and A3 are quoted where they apply).
- The full verification run happens after implementation.
- Every user story has at least one Playwright test.
- No test calls real PayPal. Use respx, MSW, or `FakePayPalGateway` with `APP_ENV=test`.

**Git**: No task commits, pushes, creates branches, or touches GitHub Actions on its own. Each phase
ends with a **Request commit approval** task, and only the owner's explicit approval allows a git
action (Principle XIX). Work happens on branch `001-paypal-sync`. Creating or switching to that
branch also needs approval: ask before T001.

**Organization**: Tasks are grouped by user story. Spec User Story 0 (project foundation) becomes
Phase 1 (Setup) and Phase 2 (Foundational).

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: US1 = sync, US2 = `/pay` checkout, US3 = demo seed
- Size limits for every file: file ≤ 200 lines, component ≤ 150, function ≤ 40, test file ≤ 300

## Path Conventions

- **Backend**: `backend/app/...`. Tests live in `backend/tests/{unit,integration}/...` and mirror
  the app paths.
- **Frontend**:
  - Feature code in `frontend/features/<feature>/`.
  - Shared code in `frontend/components/ui/`, `frontend/components/layout/`, `frontend/hooks/` and
    `frontend/lib/`.
  - Unit tests sit beside the file they test. E2E tests go in `frontend/e2e/`.

---

## Phase 1: Setup (Shared Infrastructure) — spec US0, part 1

**Purpose**: Lean tooling for 001 and the verification loop only (FR-001–FR-003, FR-006, FR-008)

**Before T001**: ask the owner to approve `git switch -c 001-paypal-sync`.

- [X] T001 Create root `package.json` (private, tooling only), `.nvmrc` (Node LTS) and `.editorconfig`.
  - Add these scripts, exactly as named in the constitution Commands section:

    | Script | Runs |
    |---|---|
    | `lint` | ESLint + Prettier check (frontend), `ruff check` + `ruff format --check` (backend) |
    | `typecheck` | `tsc --noEmit` + `mypy app` |
    | `test:backend` | `uv run pytest --cov=app` |
    | `test:unit` | Vitest |
    | `test:e2e` | Playwright |
    | `check:size` | `python scripts/check_file_size.py` |
    | `check` | all of the above except E2E |
    | `check:all` | everything, in the order lint → typecheck → size → pytest → Vitest → Playwright |
    | `gen:api` | `scripts/export_openapi.py` + openapi-typescript (see T023) |
- [X] T002 [P] Create the backend project: `backend/pyproject.toml` (uv project, `requires-python = ">=3.11,<3.14"`), `backend/.python-version` (`3.12`), `uv.lock`, and `backend/.env.example`.
  - Runtime dependencies: fastapi, uvicorn, pydantic v2, pydantic-settings, sqlalchemy 2.x, `psycopg[binary]` (v3), httpx.
  - Dev dependencies: ruff, mypy, pytest, pytest-cov, respx, hypothesis, freezegun.
  - Configure ruff (lint + format) and `mypy --strict` with the `pydantic.mypy` plugin.
  - Configure pytest: `testpaths`, a `slow` marker, coverage `fail_under = 70`.
  - `.env.example` keys, all with empty values: `APP_ENV`, `PAYPAL_MODE`, `PAYPAL_CLIENT_ID`, `PAYPAL_CLIENT_SECRET`, `PAYPAL_BASE_URL`, `DATABASE_URL`, `TEST_DATABASE_URL`, `FRONTEND_URL`, `TRUST_PROXY_HEADERS`.
  - Export `backend/requirements.txt` from `uv.lock` for Render.
- [X] T003 [P] Create the Next.js App Router project in `frontend/`.
  - `frontend/tsconfig.json` with `"strict": true`, `"noUncheckedIndexedAccess": true`, `"noImplicitOverride": true` and `"exactOptionalPropertyTypes": true`.
  - Tailwind CSS.
  - `frontend/eslint.config.mjs`:
    - typescript-eslint strict-type-checked
    - react-hooks, next, `import-x/no-cycle`, jsx-a11y
    - `@typescript-eslint/no-explicit-any: error`
    - `max-lines` 200, and 150 for `*.tsx` components
    - `max-lines-per-function` 40
    - test files allowed 300
  - Prettier with `prettier-plugin-tailwindcss`.
  - `frontend/.env.example` with `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_PAYPAL_CLIENT_ID` and `NEXT_PUBLIC_PAYPAL_MODE` (empty values).
  - Install zod, openapi-typescript and ag-grid-community/ag-grid-react, pinned in `package-lock.json`.
- [X] T004 [P] Create `scripts/check_file_size.py`.
  - Limits (Principle XIII): `.py/.ts/.tsx` ≤ 200 lines, React component `.tsx` ≤ 150, test files ≤ 300.
  - Exclude `api-types.ts`, lock files and `node_modules`.
  - Exit non-zero with a list of offenders.
  - Accept file arguments so lint-staged can pass staged files.
  - Tests: `backend/tests/unit/scripts/test_check_file_size.py`, using `tmp_path` files over and under each limit.
- [X] T005 [P] Set up Husky in `.husky/` and `.lintstagedrc.json`.
  - `pre-commit` runs lint-staged:
    - ESLint `--fix` + Prettier on TS/TSX/JSON/MD
    - `ruff check --fix` + `ruff format` on Python
    - `check_file_size.py` on staged files
    - secretlint
  - `commit-msg` runs commitlint (`commitlint.config.mjs` extends `@commitlint/config-conventional`).
  - `pre-push` runs `tsc --noEmit`, Vitest, `mypy` and `pytest -m "not slow"`.
  - Add `.secretlintrc.json` with the recommended preset.
  - Use `npm`/`npx`/`uv run` only, so the hooks work on any OS (Principle XVI).
- [X] T006 [P] Set up Vitest.
  - `frontend/vitest.config.ts`: jsdom, coverage thresholds of 80% for `components/ui/**` and `lib/**`.
  - `frontend/test/setup.ts`: jest-dom, plus an MSW server started before all tests, reset after each test, closed at the end.
  - `frontend/test/msw/handlers.ts`, initially empty, and `frontend/test/msw/server.ts`.
- [X] T007 [P] Set up Playwright.
  - `frontend/playwright.config.ts`:
    - chromium project plus a mobile project (390 px wide)
    - `webServer` entries: the backend runs `uv run uvicorn app.main:app` with `APP_ENV=test`, `PAYPAL_MODE=fake` and `DATABASE_URL` set to the `paylens_e2e` database. The frontend runs with `NEXT_PUBLIC_PAYPAL_MODE=fake`.
  - `frontend/e2e/global-setup.ts`: drop and recreate the e2e schema before the run.
  - Install `@axe-core/playwright`.
- [X] T008 [P] Create the agent and editor files (Principle XVIII; `AGENTS.md` already exists and is not changed):
  - `CLAUDE.md`, containing only `@AGENTS.md` plus one line pointing to the constitution
  - `.cursor/rules/paylens.mdc` with `alwaysApply: true`, pointing to `AGENTS.md` and `.specify/memory/constitution.md`
  - `.vscode/extensions.json` and `.vscode/settings.json` per Principle XVII
  - `CHANGELOG.md` in Keep a Changelog format with an empty `## [Unreleased]` section
- [X] T009 ⚠ **STOP: ask the owner first.** Creating a GitHub Actions workflow needs explicit approval (Principle XIX).
  - After approval, create `.github/workflows/ci.yml`. It runs on push and PR.
  - Steps: setup Node (`.nvmrc`), setup uv with Python 3.12, `npm ci` in the root and frontend, `uv sync`, Playwright chromium install, and `npm run check:all`.
  - Use a `postgres:18` service with `TEST_DATABASE_URL`, plus a `paylens_e2e` database.
  - If the owner declines, skip this task and note it in the phase report.

**Checkpoint**: `npm run lint`, `npm run typecheck` and `npm run check:size` run on the empty skeleton and pass.

---

## Phase 2: Foundational (Blocking Prerequisites) — spec US0, part 2

**Purpose**: Shared, reusable parts used by US1–US3 (Principle XII), plus the app skeleton and `/health`

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

### Backend shared modules (`backend/app/common/`)

- [X] T010 Create `backend/tests/conftest.py`.
  - A session-scoped engine from `TEST_DATABASE_URL`. **Fail, don't skip**, with the message "Set TEST_DATABASE_URL to a PostgreSQL 18 database (see quickstart)" if it is unset (research R11).
  - `create_all` once per session.
  - A per-test `Session` inside a transaction that is rolled back.
  - A settings override fixture (`APP_ENV=test`, `PAYPAL_MODE=fake`).
- [X] T011 [P] Create `backend/app/common/constants.py` with every constant from plan.md "New constants".
  - Exact values: `PAYPAL_WINDOW_DAYS = 31`, `PAYPAL_PAGE_SIZE = 500`, `PAYPAL_MAX_PAGES_PER_WINDOW = 50`, `PAYPAL_TOKEN_REFRESH_MARGIN_S = 60`, `HTTP_TIMEOUT_S = 10`, `HTTP_MAX_RETRIES = 3`, `HTTP_BACKOFF_BASE_S = 1`, `SYNC_DEFAULT_DAYS = 90`, `SYNC_STALE_AFTER_MINUTES = 10`, `CHECKOUT_RECONCILE_WINDOW_HOURS = 72`, `CHECKOUT_CURRENCIES = ("USD", "GBP", "EUR", "AUD")`, `CHECKOUT_MAX_AMOUNT = Decimal("10000.00")`, `CHECKOUT_DESCRIPTION_MAX = 127`, `RATE_LIMIT_SYNC = (3, 60)`, `RATE_LIMIT_PAY = (10, 60)`, `TRANSACTIONS_PAGE_MAX = 200`.
  - `INCOME_EVENT_CODES`: T0000, T0001, T0002, T0003, T0004, T0005, T0006, T0007, T0011, T0012, T0018, T0019, T0023 (research R2).
  - Kind prefixes: T11xx/T1201 → refund, T04xx → withdrawal, T02xx → conversion, T15xx/T21xx → hold, T0107 → fee.
  - `SYNC_LOCK_KEY` as a fixed int64.
- [X] T012 [P] Create `backend/app/common/types.py`.
  - `CurrencyCode` (validated `^[A-Z]{3}$`).
  - A `Money` Pydantic model (`amount: Decimal`, `currency: CurrencyCode`).
  - Enums exactly as in data-model.md: `TransactionSource`, `TransactionOrigin`, `TransactionKind`, `TransactionStatus`, `SyncTrigger`, `SyncOutcome`, `FiraStatus`.
  - Tests in `backend/tests/unit/common/test_types.py`: invalid currency rejected, and `Money` rejects a float input.
- [X] T013 [P] Create `backend/app/common/money.py`: `round_money` (2 dp, `ROUND_HALF_UP`), `parse_money(str) -> Decimal` (rejects floats and NaN), `to_api_string(Decimal) -> str` (always 2 dp).
  - Tests in `backend/tests/unit/common/test_money.py`, including hypothesis properties (round-trip, no float, half-up at .005).
- [X] T014 [P] Create `backend/app/common/dates.py`: `utc_now`, `ensure_utc`, and `split_windows(start, end, max_days)`.
  - Windows are back-to-back: each window's end equals the next window's start, with no gap or overlap.
  - Raises `ValueError` when `start >= end`.
  - Tests in `backend/tests/unit/common/test_dates.py`:
    - **P1**: a 75-day range gives 3 windows, each ≤ 31 days
    - exactly 31 days gives 1 window
    - boundary contiguity
    - freezegun for `utc_now`
- [X] T015 [P] Create `backend/app/common/errors.py`.
  - `AppError(code, message, http_status)` and subclasses: `ValidationAppError` 422, `InvalidPeriodError` 400, `NotFoundError` 404, `SyncInProgressError` 409, `RateLimitedError` 429 (carries `retry_after`), `PaymentDeclinedError` 422, and `PayPalError` 502 with codes `PAYPAL_UNAVAILABLE`, `PAYPAL_AUTH_FAILED` and `PAYPAL_REJECTED`.
  - `register_error_handlers(app)` returns `{"error": {"code", "message"}}`, maps `RequestValidationError` to 422 `VALIDATION_ERROR`, and maps unknown exceptions to 500 `INTERNAL_ERROR` with no stack trace.
  - Tests in `backend/tests/unit/common/test_errors.py`.
- [X] T016 [P] Create `backend/app/common/http_client.py`.
  - `make_client()`: httpx `Client` with `HTTP_TIMEOUT_S`.
  - `send_with_retry(client, request_fn)`:
    - retries 429 and 5xx up to `HTTP_MAX_RETRIES` with exponential backoff (`HTTP_BACKOFF_BASE_S * 2**n`, using an injectable sleep)
    - does not retry other 4xx
    - raises `PayPalError(PAYPAL_UNAVAILABLE)` after the last attempt
  - Tests in `backend/tests/unit/common/test_http_client.py` (respx):
    - **P4**: 429 then 200 succeeds
    - 500 four times raises
    - 400 is not retried
    - the backoff delays are asserted
- [X] T017 [P] Create `backend/app/common/rate_limit.py`.
  - `FixedWindowLimiter(limit, window_s, clock)`, thread-safe.
  - `rate_limit(name, limit_window)` FastAPI dependency. Client IP is the first `X-Forwarded-For` entry only when `settings.trust_proxy_headers`, else `request.client.host`. Raises `RateLimitedError` with `retry_after`.
  - Tests in `backend/tests/unit/common/test_rate_limit.py`: 3 allowed then the 4th rejected, the window resets, IPs are counted separately, and the proxy header is ignored when not trusted.
- [X] T018 Create `backend/app/config.py` and `backend/app/db.py`.
  - `config.py`: `Settings` (pydantic-settings) with:
    - `app_env: Literal["development","test","production"]`
    - `paypal_mode: Literal["http","fake"]`
    - paypal credentials and base URL (default `https://api-m.sandbox.paypal.com`)
    - `database_url`, `frontend_url`, `trust_proxy_headers`
  - Validation:
    - **fail at startup if `paypal_mode == "fake"` and `app_env == "production"`**
    - fail if the base URL is not the sandbox URL (sandbox only, Principle VI)
    - a missing required setting gives a clear error naming it (FR-006)
  - `db.py`: engine plus a `get_session` dependency.
  - Tests in `backend/tests/unit/test_config.py`.

### Backend data and app skeleton

- [X] T019 Create `backend/app/models/base.py`, `backend/app/models/client.py`, `backend/app/models/transaction.py` and `backend/app/models/__init__.py`, exactly per data-model.md.
  - `clients`: `email` VARCHAR(254) NULL **UNIQUE**, stored lower-cased; `is_unknown` with a partial unique index (only one true); `source`.
  - `transactions`:
    - `paypal_transaction_id` VARCHAR(32) NOT NULL **UNIQUE**
    - money columns `NUMERIC(14,2)`, rates `NUMERIC(14,6)`, `raw_json` JSONB
    - CHECKs: `fee_amount >= 0`, `gross_amount >= 0`, `net_amount = gross_amount - fee_amount`
    - nullable 002/004 columns: `mid_market_rate`, `paypal_rate`, `inr_received`, `fee_loss_inr`, `fx_loss_inr`, `total_leakage_inr`, `fira_status`
    - indexes on `occurred_at DESC`, `client_id`, `source` and `kind`
  - Tests in `backend/tests/integration/models/test_constraints.py`: a duplicate `paypal_transaction_id` is rejected, a negative fee is rejected, gross − fee ≠ net is rejected, a second unknown client is rejected.
- [X] T020 Create `backend/app/main.py` (an app factory with nothing else in it) and `backend/app/api/routes/health.py`.
  - `create_app()`: CORS allowing only `settings.frontend_url` and `http://localhost:3000`, `register_error_handlers`, a router list from `backend/app/api/routes/__init__.py`, and a lifespan that runs `create_all`.
  - `GET /health` returns `{"status": "ok"}`.
  - Tests in `backend/tests/integration/api/test_app.py`:
    - **A1** health
    - **A4** invalid body gives 422 in the standard shape (use a test-only route)
    - **A5** an unhandled error gives 500 with a safe message and no stack trace
    - **A6** a disallowed origin gets no CORS allow header
- [X] T021 Create `backend/app/paypal/schemas.py`, `backend/app/paypal/auth.py`, `backend/app/paypal/gateway.py` and `backend/app/paypal/__init__.py`.
  - `schemas.py`: Pydantic models for the token response.
  - `auth.py`: `TokenCache` that reuses the token until `expires_in − PAYPAL_TOKEN_REFRESH_MARGIN_S` and has `invalidate()`.
  - `gateway.py`: a `PayPalGateway` Protocol (empty for now; each story adds its methods), `HttpPayPalGateway(settings, client, token_cache)` with a helper that calls with a bearer token and **on 401 invalidates and retries once**, then raises `PAYPAL_AUTH_FAILED`, and `get_gateway(settings)` that returns `FakePayPalGateway` only when `paypal_mode == "fake"`.
  - `backend/app/fakes/paypal_fake.py`: the `FakePayPalGateway` skeleton.
  - Tests in `backend/tests/unit/paypal/test_auth.py` (respx): **P9** the token is reused before expiry (one token call); **P5** a 401 refreshes once and retries; a second 401 raises.
- [X] T022 Create `backend/app/schemas/common.py` and `backend/app/schemas/__init__.py`.
  - `MoneyOut` (`amount: str` matching `^-?\d+\.\d{2}$`, `currency`), built from `Money` via `to_api_string`, never a float.
  - `ErrorOut`.
  - Tests in `backend/tests/unit/schemas/test_common.py`.
- [X] T023 Create `backend/scripts/export_openapi.py`, which writes `frontend/lib/api/openapi.json` from `create_app().openapi()`.
  - Wire the root `gen:api` script to also run `openapi-typescript frontend/lib/api/openapi.json -o frontend/lib/api/api-types.ts`.
  - Add a header comment "Generated — do not edit".
  - Run it once and commit the result together with the phase.

### Frontend shared modules

- [X] T024 [P] Create `frontend/lib/constants.ts` and `frontend/lib/format.ts`.
  - `constants.ts`: routes, source labels `"PayPal sandbox"` and `"Demo seed"`, the demo banner "Demo mode — PayPal sandbox data", the sandbox checkout notice, sync messages, and `CHECKOUT_CURRENCIES`/`CHECKOUT_DESCRIPTION_MAX = 127` (must match the backend).
  - `format.ts`:
    - `formatMoney(amount: string, currency)`: `Intl.NumberFormat`, `en-IN` for INR. No arithmetic on the number beyond display parsing.
    - `formatINR`
    - `formatDate` (IST `Asia/Kolkata`)
  - Tests in `frontend/lib/format.test.ts`: **U1** `formatINR("77914.00")` gives `₹77,914.00`; **U2** `formatINR("1234567.50")` gives `₹12,34,567.50`; USD/GBP/EUR/AUD; IST conversion.
- [X] T025 [P] Create `frontend/lib/api/client.ts` and `frontend/lib/api/schemas.ts`.
  - `client.ts`: typed fetch on `NEXT_PUBLIC_API_URL` that parses the error shape into an `ApiError`.
  - `schemas.ts`: zod `MoneySchema` (`amount: z.string().regex(/^-?\d+\.\d{2}$/)`), the error schema, and a `parseWith(schema, data)` helper.
  - Tests in `frontend/lib/api/client.test.ts` (MSW): **U3** a numeric money field fails validation; a 4xx maps to `ApiError` with code and message.
- [X] T026 [P] Create `frontend/hooks/useApi.ts` (GET with loading/error/data plus a zod schema and `reload()`) and `frontend/hooks/useMutation.ts` (POST with the same states).
  - Tests: **U8** success, error and invalid-data states with MSW, in `frontend/hooks/useApi.test.tsx` and `frontend/hooks/useMutation.test.tsx`.
- [X] T027 [P] Create `frontend/components/ui/Button/`, `Card/`, `Spinner/`, `EmptyState/` and `ErrorState/` (with a retry callback).
  - Each is a folder with `index.ts`, the component and its `.test.tsx`. Typed props, named exports.
- [X] T028 [P] Create `frontend/components/ui/Badge/`, `MoneyText/` and `Disclaimer/`.
  - `Badge` has variants `matched`, `needs_review`, `missing`, `paypal_sandbox` and `demo_seed`, with labels from constants.
  - `MoneyText` uses `formatMoney` and has a `tone` prop. A negative value with `gainWhenNegative` renders as a gain label.
  - `Disclaimer` takes text from constants.
  - Tests beside each component: **U6** Badge variants, **U4** MoneyText negative shown as gain, **U11** Disclaimer text.
- [X] T029 [P] Create `frontend/components/ui/DataGrid/`: an AG Grid Community wrapper with shared defaults (sortable, resizable, no CSS-class selectors needed by tests, accessible grid role). It renders `EmptyState` when there are no rows.
  - Test: **U7** no rows shows `EmptyState`, in `frontend/components/ui/DataGrid/DataGrid.test.tsx`.
- [X] T030 Create `frontend/components/layout/AppShell/` (nav: Transactions, Pay) and `frontend/components/layout/PageHeader/` (title plus the demo-mode banner, FR-050).
  - Pages: `frontend/app/layout.tsx` uses `AppShell`, and `frontend/app/page.tsx` redirects to `/transactions`.
  - Tests beside the components.

### Foundation verification

- [X] T031 Foundation verification run: `npm run check:all`.
  - E2E has only a smoke test, `frontend/e2e/smoke.spec.ts`: the app loads, the banner is visible, and the backend `/health` is ok.
  - Fix the root cause and re-run until green. Stop and report after 3 failed attempts on the same issue.
- [ ] T032 Request commit approval. Show:
  - the verification report (constitution format)
  - the changed files
  - the proposed commit `chore: set up tooling, hooks, tests and shared modules`
  - the exact `git add`/`git commit` command

  Then wait for the owner.

**Checkpoint**: Foundation ready. User story implementation can now begin.

---

## Phase 3: User Story 1 — Sync PayPal sandbox payments (Priority: P1) 🎯 MVP

**Goal**: Sync now (and on startup) reads every sandbox event over ≤31-day windows and all pages. It classifies, normalises and idempotently stores the events, links clients, and shows the result plus a source-labelled list (FR-010–FR-023).

**Independent Test**: In fake mode, press Sync now. The summary shows 10 added and 2 skipped, and the list shows 10 rows with source "PayPal sandbox". Pressing again shows 0 added and an unchanged count (quickstart V3 steps 1–2).

### Implementation for User Story 1 (each task includes its tests)

- [X] T033 [P] [US1] Create `backend/app/models/sync_run.py` per data-model.md.
  - Columns: `trigger`, `period_start`, `period_end`, `started_at`, `finished_at` NULL, `outcome`, `windows_total`, `windows_done`, `added`, `updated`, `skipped`, `flagged` (INT NOT NULL DEFAULT 0), `error_code` VARCHAR(50) NULL, `error_message` VARCHAR(500) NULL.
  - Export it from `models/__init__.py`.
  - Test: insert and read, in `backend/tests/integration/models/test_sync_run.py`.
- [X] T034 [P] [US1] Create `backend/app/paypal/classify.py`.
  - `classify(event_code, amount, status) -> TransactionKind`, following research R2: income only when the code is in `INCOME_EVENT_CODES` **and** the amount is > 0; the same code with amount < 0 is `outgoing_payment`; prefix rules give refund/withdrawal/conversion/hold/fee; anything else is `other`.
  - `map_status("S"|"P"|"D"|"V") -> TransactionStatus`.
  - `counts_as_income(kind, status)` is true only for income with status completed or pending.
  - Tests in `backend/tests/unit/paypal/test_classify.py`: every listed code; T0400/T1107/T0200/T2105/T0107; an unknown code gives `other`; **P8** a withdrawal or refund is not income; D/V are not income.
- [X] T035 [P] [US1] Extend `backend/app/paypal/schemas.py` with Transaction Search models (`SearchResponse`, `TransactionDetail`, `TransactionInfo`, `PayerInfo`, `PayerName`, `AmountWithCurrency`), using only the fields in research R2–R6.
  - Create `backend/app/paypal/mapper.py` with `from_search_row(detail) -> TransactionUpsert`, a typed DTO:
    - `fee = abs(fee_amount.value)`, or `0.00` in the transaction currency when missing (**P7**)
    - `net = gross − fee` (Decimal)
    - payer email lower-cased
    - name fallback: `full_name`, then `given_name + surname`, then the email
    - a missing email maps to the unknown client
    - `raw_json` kept
  - Fixtures: `backend/tests/fixtures/paypal/search_page_*.json`.
  - Tests in `backend/tests/unit/paypal/test_mapper.py`: negative fee, positive fee, missing fee, missing payer email, name fallbacks.
- [X] T036 [US1] Create `backend/app/paypal/transactions_api.py`: `fetch_page(gateway_http, start, end, page) -> SearchResponse`, calling `GET /v1/reporting/transactions` with `start_date`, `end_date`, `fields=all`, `balance_affecting_records_only=N`, `page_size=PAYPAL_PAGE_SIZE` and `page` starting at 1 (research R4). It goes through `send_with_retry` and the 401 helper.
  - Add `search_transactions(start, end, page)` to the `PayPalGateway` Protocol, `HttpPayPalGateway` and `FakePayPalGateway`. The fake returns 12 deterministic rows (10 income T0006/T0000, 1 T0400 withdrawal, 1 T1107 refund) across 2 pages.
  - Tests in `backend/tests/unit/paypal/test_transactions_api.py` (respx): the query params are exact; the parsed response.
- [X] T037 [US1] Create `backend/app/paypal/upsert.py`.
  - `upsert_client(session, payer) -> Client`: by lower-cased email; creates it the first time with country and currency; otherwise uses the single unknown client.
  - `upsert_transaction(session, dto) -> Literal["added","updated"]`:
    - matches by `paypal_transaction_id`
    - on update, refreshes the PayPal-derived columns, sets `source=paypal_sandbox` and `origin=transaction_search`, and **never touches the 002/004 columns**
  - Tests in `backend/tests/integration/paypal/test_upsert.py`: **P3** the same DTO twice gives 1 row; status pending → completed updates the row; a new payer creates a client; a known payer is reused; a missing email links to the unknown client.
- [X] T038 [US1] Create `backend/app/services/sync_lock.py`: a `sync_lock(engine)` context manager using `pg_try_advisory_lock(SYNC_LOCK_KEY)` on a dedicated connection, released in `finally`. It raises `SyncInProgressError` when the lock is not acquired.
  - Tests in `backend/tests/integration/services/test_sync_lock.py`: a second acquire while the first is held raises; it can be acquired again after release.
- [X] T039 [US1] Create `backend/app/paypal/sync.py`: `run_sync(session_factory, gateway, start, end) -> SyncCounts`, the coordinator.
  - Split windows with `split_windows(…, PAYPAL_WINDOW_DAYS)`. For each window, loop pages while `page < total_pages`, stopping at `PAYPAL_MAX_PAGES_PER_WINDOW` (flag the window and mark the run partial).
  - Classify and map each row. Within one run, de-duplicate rows that share a transaction ID, keeping the income row; the other is counted as `flagged` and logged without `raw_json` (research R5).
  - Upsert. Non-income rows count as `skipped`.
  - **Commit per window.** On error, roll back that window, keep the earlier windows, and re-raise with partial counts.
  - Tests in `backend/tests/integration/paypal/test_sync.py` (respx + DB):
    - **P1** a 75-day period makes 3 window requests
    - **P2** 3 pages are all fetched
    - **P3** running twice gives no duplicates
    - **P4** 429 then 200 succeeds
    - **P5** a 401 refreshes and retries
    - **P6** 500 three times in window 2: window 1 is kept and window 2 has no rows
    - **P7** a negative fee is stored positive
    - **P8** a withdrawal/refund is stored with `kind ≠ income` and counted as skipped
    - a duplicate ID in a page is flagged
    - `total_pages = 0`
- [X] T040 [US1] Create `backend/app/services/sync_service.py`.
  - `start_sync(trigger, start, end) -> SyncRun`:
    - validates the period (`start < end`, `end <= now`, else `InvalidPeriodError`); the default is the last `SYNC_DEFAULT_DAYS`
    - takes `sync_lock`, inserts a `running` row, calls `run_sync`, then stores outcome `success`/`partial`/`failed` with `error_code`/`error_message`
    - sets a `hint` when `added + updated == 0`
  - `get_last_run()` reports a `running` row older than `SYNC_STALE_AFTER_MINUTES` as failed.
  - `run_startup_sync()` runs in a background thread and swallows the error after recording it (FR-021).
  - Tests in `backend/tests/integration/services/test_sync_service.py`: success counts; a failed PayPal call gives outcome failed with a safe message; a stale row is reported as failed; an invalid period; the lock is held, so `SyncInProgressError`.
- [X] T041 [US1] Create `backend/app/schemas/sync.py` (`SyncRunOut`, `SyncRequest` with optional `start`/`end`, `PeriodOut`, `CountsOut`, `WindowsOut`, `SyncErrorOut`, per contracts/http-api.md), `backend/app/services/transaction_service.py` (`list_transactions(limit 1–200 default 100, offset ≥ 0, kind default income | all, source optional)`, newest first, joined with client), and `backend/app/schemas/transaction.py` (`TransactionOut` with `MoneyOut` gross/fee/net, `source`, `is_flagged`, and **no** `raw_json`, `flag_reason` or `origin`).
  - Tests in `backend/tests/integration/services/test_transaction_service.py`: order, filters, paging.
- [X] T042 [US1] Create `backend/app/api/routes/sync.py`: `POST /sync` with the `rate_limit("sync", RATE_LIMIT_SYNC)` dependency, returning 200 `SyncRunOut`; `GET /sync/last` returning `SyncRunOut | null`.
  - Create `backend/app/api/routes/transactions.py`: `GET /transactions`.
  - Register both. Add the startup sync to the lifespan, skipped when `app_env == "test"` unless enabled by a fixture.
  - Tests in `backend/tests/integration/api/test_sync_api.py` and `test_transactions_api.py`:
    - **A3** every row has `source`
    - money values are strings
    - 409 `SYNC_IN_PROGRESS`
    - 400 `INVALID_PERIOD`
    - 429 on the 4th `POST /sync` within 60 s, with `Retry-After`
    - startup sync failure leaves the app up and `GET /sync/last` shows failed
- [X] T043 [US1] Run `npm run gen:api`. Add zod schemas `SyncRunSchema`, `TransactionSchema` and `TransactionListSchema` to `frontend/lib/api/schemas.ts`, matching the generated types (type-level assertion), and add MSW handlers for `/sync`, `/sync/last` and `/transactions` in `frontend/test/msw/handlers.ts`.
- [X] T044 [P] [US1] Create `frontend/features/transactions/useTransactions.ts` (`useApi` on `/transactions`) and `frontend/features/transactions/useSync.ts` (`useMutation` on `POST /sync`, then reload the list and `/sync/last`).
  - Tests beside each, using MSW.
- [X] T045 [P] [US1] Create `frontend/features/transactions/TransactionsGrid.tsx`.
  - Column definitions for `DataGrid`: date (IST via `formatDate`), client, gross/fee/net (`MoneyText`), status, source (`Badge`), and a flagged marker.
  - Test: every row shows a source badge, in `TransactionsGrid.test.tsx`.
- [X] T046 [P] [US1] Create `frontend/features/transactions/SyncPanel/` (`index.ts`, `SyncPanel.tsx` with the Sync now `Button`, disabled while running, plus `Spinner`) and its grandchild `SyncResult.tsx`.
  - `SyncResult` shows added/updated/skipped/flagged, the period, the finished time, the error (`ErrorState`), the hint, and the 409/429 messages from constants.
  - Tests beside each component.
- [X] T047 [US1] Create `frontend/features/transactions/TransactionsView.tsx` (the parent: `PageHeader`, `SyncPanel`, `TransactionsGrid`, plus loading, empty and error states) and `frontend/features/transactions/index.ts`.
  - Create `frontend/app/transactions/page.tsx`, which only renders `TransactionsView`.
  - Test: `TransactionsView.test.tsx` covers the error state with retry.
- [X] T048 [US1] Write the E2E tests in `frontend/e2e/transactions.spec.ts`:
  - **E2** Sync now: success message, then 10 rows
  - Sync again: 0 added, still 10 rows
  - **E3** (source part) a "PayPal sandbox" badge on every row
  - **E10** backend unavailable: `ErrorState` with retry
  - **E11** at 390 px there is no horizontal page scroll

  Also write `frontend/e2e/a11y.spec.ts`: **E12** axe on `/transactions` finds no critical or serious violations. Use role/label selectors only, with no fixed sleeps.

### Verification for User Story 1

- [X] T049 [US1] Verification run: `npm run check:all`. Fix the root cause and re-run until green. Stop and report after 3 failed attempts on the same issue.
- [ ] T050 [US1] Request commit approval. Show the verification report, the changed files, the proposed commit `feat(sync): sync PayPal sandbox transactions` and the exact command. Wait for the owner.

**Checkpoint**: US1 works and is independently testable. M1 is demonstrable with sandbox data synced from PayPal.

---

## Phase 4: User Story 2 — Sandbox checkout `/pay` (Priority: P2)

**Goal**: A client pays through `/pay`. The order is created and captured on the backend, and the payment is recorded at once and reconciled with the later sync (FR-030–FR-035).

**Independent Test**: In fake mode, pay `50.00 USD` on `/pay`. A confirmation shows the transaction ID, and the row is listed with "PayPal sandbox". A later sync does not duplicate it (quickstart V3 step 3).

### Implementation for User Story 2 (each task includes its tests)

- [X] T051 [P] [US2] Add Orders models to `backend/app/paypal/schemas.py`. If the file would pass 120 lines, split it into `schemas_search.py` and `schemas_orders.py` behind `paypal/__init__.py`.
  - Models: `CreateOrderResponse`, `CaptureResponse`, `Capture`, `SellerReceivableBreakdown` (`gross_amount`, `paypal_fee`, `net_amount`), `OrderPayer` (`email_address`, `name.given_name`, `name.surname`, optional `address.country_code`).
  - Create `backend/app/paypal/orders_api.py`:
    - `create_order(amount, currency, description)`: `POST /v2/checkout/orders`, intent CAPTURE, `purchase_units[0].description` ≤ 127 characters
    - `capture_order(order_id)`: `POST /v2/checkout/orders/{id}/capture` with `Prefer: return=representation`
    - Both send a UUID `PayPal-Request-Id` that stays the same across retries.
  - Add both methods to the `PayPalGateway` Protocol, `HttpPayPalGateway` and `FakePayPalGateway`. The fake is deterministic: `amount == "13.13"` gives a DECLINED capture, used by E2E.
  - Tests in `backend/tests/unit/paypal/test_orders_api.py` (respx): headers present; the same request ID on retry; parsed models.
- [X] T052 [P] [US2] Add `from_capture(capture_response, order_id) -> TransactionUpsert` to `backend/app/paypal/mapper.py`.
  - The ID is the **capture ID** (`purchase_units[0].payments.captures[0].id`), with `origin=checkout_capture`, `kind=income`, and the status mapped from the capture status.
  - fee is `abs(paypal_fee)`; net is `gross − fee`.
  - If PayPal's `net_amount` differs from `gross − fee`, set `is_flagged` with reason `NET_MISMATCH`.
  - If the breakdown is missing, set fee to `0.00` and flag `MISSING_BREAKDOWN` (research R3).
  - Country may be null.
  - Tests in `backend/tests/unit/paypal/test_mapper_capture.py`.
- [X] T053 [US2] Add the reconcile fallback to `backend/app/paypal/upsert.py` (research R1).
  - When there is no ID match and the incoming row is income, look for **exactly one** row with `origin = checkout_capture`, the same `gross_amount`, `currency` and client email, and `occurred_at` within `CHECKOUT_RECONCILE_WINDOW_HOURS = 72`.
  - If exactly one is found: re-key it to the Transaction Search ID, set `origin=transaction_search`, and return `updated`.
  - If zero are found: insert. If two or more are found: insert and flag `AMBIGUOUS_RECONCILE`.
  - Tests in `backend/tests/integration/paypal/test_reconcile.py`:
    - same ID: updated, not duplicated (FR-033 / US2 scenario 3)
    - different ID with one candidate: re-keyed
    - two candidates: inserted and flagged
    - outside the 72 h window: inserted
- [X] T054 [US2] Create `backend/app/services/checkout_service.py`.
  - `create_order(PayOrderIn) -> order_id`.
  - `capture_and_record(order_id) -> CaptureOut`:
    - a DECLINED capture or an unapproved order raises `PaymentDeclinedError`
    - on success, records the payment through `upsert_client` and `upsert_transaction` in its own transaction
    - if the DB write fails, logs the error (no raw JSON) and returns `recorded=false` (spec edge case)
  - Tests in `backend/tests/integration/services/test_checkout_service.py`, using the fake gateway: success records 1 row with source `paypal_sandbox`; declined stores nothing; a DB failure gives `recorded=false`.
- [X] T055 [US2] Create `backend/app/schemas/pay.py`.
  - `PayOrderIn`:
    - `amount: str` matching `^\d+(\.\d{1,2})?$` with `0 < amount ≤ CHECKOUT_MAX_AMOUNT`
    - `currency` in `CHECKOUT_CURRENCIES`
    - `description: str | None`, max length 127
  - `PayOrderOut` (`order_id`) and `CaptureOut` (`transaction_id`, `order_id`, `status`, `gross: MoneyOut`, `recorded`).
  - Create `backend/app/api/routes/pay.py`: `POST /pay/orders` (201) and `POST /pay/orders/{order_id}/capture` (200), each with `rate_limit("pay", RATE_LIMIT_PAY)`. Register the router.
  - Tests in `backend/tests/integration/api/test_pay_api.py`:
    - 422 for empty, 0, negative or 3-decimal amounts, above the maximum, a bad currency, or a 128-character description
    - 422 `PAYMENT_DECLINED`
    - 429 on the 11th request within 60 s
    - no secret appears in any response
- [X] T056 [US2] Run `npm run gen:api`. Add zod `PayOrderInSchema` to `frontend/lib/api/schemas.ts`, mirroring the backend rules and using `CHECKOUT_CURRENCIES`/`CHECKOUT_DESCRIPTION_MAX` from constants. Add `PayOrderOutSchema`, `CaptureOutSchema` and the MSW handlers.
  - Install `@paypal/react-paypal-js` at a pinned version, and record the supported JS SDK major in research.md R7.
- [X] T057 [P] [US2] Create `frontend/features/pay/PayForm.tsx`: amount, currency select, description, with field-level errors from zod. The pay button stays disabled until the form is valid (US2 scenario 4).
  - Test: `PayForm.test.tsx` covers each invalid case.
- [X] T058 [P] [US2] Create `frontend/features/pay/PayButton/`:
  - `PayPalCheckoutButton.tsx`: `PayPalScriptProvider` keyed by currency, with `client-id` set to `NEXT_PUBLIC_PAYPAL_CLIENT_ID` and `currency`. `createOrder` calls the backend; `onApprove` calls capture; `onCancel`/`onError` report "No payment was made".
  - `FakeCheckoutButton.tsx`: the "Pay (test mode)" button, which calls the same backend endpoints.
  - `index.ts` picks one by `NEXT_PUBLIC_PAYPAL_MODE`.
  - Create `frontend/features/pay/usePayOrder.ts`.
  - Tests: the fake button flow with MSW; cancel shows the message.
- [X] T059 [US2] Create `frontend/features/pay/PayResult.tsx` (amount, currency and transaction ID; when `recorded=false`, a note that it will appear after the next sync) and `frontend/features/pay/PayView.tsx` (the parent, with `PageHeader`, the sandbox notice `Disclaimer` "Sandbox demo — no real money", and no PayPal logo as branding).
  - Create `frontend/features/pay/index.ts` and `frontend/app/pay/page.tsx`.
  - Tests beside each component.
- [X] T060 [US2] Write the E2E tests in `frontend/e2e/pay.spec.ts`:
  - fake checkout of 50.00 USD shows a confirmation with the transaction ID, then the row appears on `/transactions` with "PayPal sandbox"
  - an invalid amount keeps the button disabled
  - amount `13.13` (declined) shows "No payment was made"
  - **E12** axe on `/pay`
  - **E11** 390 px

### Verification for User Story 2

- [X] T061 [US2] Verification run: `npm run check:all`. Fix and re-run until green. Stop and report after 3 failed attempts on the same issue.
- [ ] T062 [US2] Request commit approval. Show the verification report, the changed files, the proposed commit `feat(pay): add sandbox checkout page with immediate recording` and the exact command. Wait for the owner.

**Checkpoint**: US1 and US2 both work independently.

---

## Phase 5: User Story 3 — Seeded demo history (Priority: P3)

**Goal**: 20–30 idempotent `demo_seed` transactions across 4 clients and at least 3 months, with a reset that removes only seed data (FR-040–FR-042).

**Independent Test**: Seed twice: 24 rows. Reset: only `demo_seed` rows are removed (quickstart V4).

### Implementation for User Story 3 (each task includes its tests)

- [X] T063 [P] [US3] Create `backend/scripts/seed_data.py`.
  - 4 fictional clients with `example.com` emails: US/USD, UK/GBP, DE/EUR, AU/AUD.
  - 24 fixed transactions, `SEED-0001`…`SEED-0024`, spread over the 4 months before the current month.
  - Fees come from the `SEED_FEE_PERCENT` + `SEED_FEE_FIXED` constants (add both to `constants.py`), computed with `round_money` so that gross − fee = net.
  - Each row has `source=demo_seed`, `origin=seed`, `kind=income` and `status=completed`.
- [X] T064 [US3] Create `backend/scripts/seed_demo.py`, a CLI run as `python -m scripts.seed_demo [--reset]`.
  - It upserts by `paypal_transaction_id`, so it is idempotent.
  - `--reset` deletes only `source=demo_seed` transactions, then seed clients that have no transactions left.
  - It prints counts.
  - Tests in `backend/tests/integration/scripts/test_seed_demo.py`:
    - the first run gives 24 rows, 4 clients and ≥ 3 distinct months
    - the second run still gives 24
    - reset keeps `paypal_sandbox` rows
    - every row satisfies gross − fee = net
- [X] T065 [US3] E2E: extend `frontend/e2e/global-setup.ts` to run the seed, and add a test to `frontend/e2e/transactions.spec.ts`: the grid shows "Demo seed" and "PayPal sandbox" badges side by side after a sync (FR-050, E3 source part).

### Verification for User Story 3

- [X] T066 [US3] Verification run: `npm run check:all`. Fix and re-run until green. Stop and report after 3 failed attempts on the same issue.
- [ ] T067 [US3] Request commit approval. Show the verification report, the changed files, the proposed commit `feat(seed): add idempotent demo seed data` and the exact command. Wait for the owner.

**Checkpoint**: All user stories are independently functional.

---

## Phase N: Polish & Cross-Cutting Concerns

- [ ] T068 [P] Update `README.md`:
  - tagline and description
  - "Demo mode / sandbox only" note
  - local setup (PostgreSQL 18 prerequisite, uv, npm, env files, `npm run check:all`)
  - PayPal sandbox setup (plan section 8)
  - PayPal APIs used (OAuth, Transaction Search, Orders v2 + JS SDK)
  - the no-login and rate-limit notes
  - the Transaction Search 3 h delay
  - the seed command
  - MIT license
- [ ] T069 Label check across the UI: a `source` badge on every row, the demo banner on every page, the sandbox notice on `/pay`, no PayPal logo as branding (FR-035, FR-050). Fix any gaps and add tests where they are missing.
- [ ] T070 Run quickstart V2 (hooks) and V3 (fake-mode demo) by hand and note the results in the phase report. The V2 commit attempt needs the owner's approval.
- [ ] T071 Owner-assisted sandbox checks V5–V8 from `specs/001-paypal-sync/quickstart.md`. These need the owner's sandbox accounts and can run as soon as payments exist (Transaction Search delay up to 3 h).
  - Record the results in `specs/001-paypal-sync/research.md`: R1 (are the IDs equal?), R2 (the event codes for `/pay` and "Send money"), R3 (the fee sign), R4 (`page=1` is the first page).
  - If a finding contradicts the design, raise it with the owner before changing code.
- [ ] T072 Final verification run: `npm run check:all` until green.
- [ ] T073 Update `CHANGELOG.md` under `## [Unreleased]`:
  - `Added`: PayPal sandbox transaction sync (specs/001-paypal-sync)
  - `Added`: sandbox checkout page
  - `Added`: demo seed data
  - `Added`: project tooling, hooks, test setup
- [ ] T074 Request commit approval. Show the verification report, the changed files, the proposed commit `docs: README and changelog for 001-paypal-sync` and the exact command. Wait for the owner.
  - **Push and merge to `main` each need their own separate approval.**
- [ ] T075 After an approved push or merge and the Render deploy, run the quickstart V9 smoke test on the live URL: `/health`, Sync now, a `/pay` payment shows up, and the 4th quick Sync now gets 429. Report the results.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: T001 first (root scripts). T002–T008 can then run in parallel. T009 waits for the owner's approval.
- **Foundational (Phase 2)**: depends on Setup.
  - T010 comes before the DB tests (T019 onward).
  - T011–T017 and T024–T029 can run in parallel.
  - T018 → T019 → T020 → T021 → T022 → T023.
  - T030 needs T027–T028.
  - This phase blocks all stories.
- **US1 (Phase 3)**: depends on Foundational.
- **US2 (Phase 4)**: depends on Foundational. It reuses the US1 `upsert.py` and `/transactions` for its E2E check, so run it after US1.
- **US3 (Phase 5)**: depends on Foundational only. T065 uses the US1 page. It can run in parallel with US2 if staffed.
- **Polish**: after the desired stories. T071 can start as soon as US2 is deployed or running against the sandbox.

### Within User Story 1

T033/T034/T035 (parallel) → T036 → T037 → T038 → T039 → T040 → T041 → T042 → T043 → T044/T045/T046 (parallel) → T047 → T048 → T049 → T050

### Within User Story 2

T051/T052 (parallel) → T053 → T054 → T055 → T056 → T057/T058 (parallel) → T059 → T060 → T061 → T062

### Within User Story 3

T063 → T064 → T065 → T066 → T067

### Parallel Opportunities

- Setup: T002, T003, T004, T005, T006, T007, T008
- Foundational: the backend common modules T011–T017, and the frontend T024–T029. The two groups can also run in parallel with each other.
- US1: T033, T034 and T035; later T044, T045 and T046
- US2: T051 and T052; later T057 and T058
- US3 can run in parallel with US2

## Parallel Example: User Story 1

```bash
# Backend building blocks, all in different files:
Task: "T033 sync_run model in backend/app/models/sync_run.py"
Task: "T034 classify in backend/app/paypal/classify.py"
Task: "T035 search schemas + mapper in backend/app/paypal/{schemas,mapper}.py"

# Frontend pieces after T043:
Task: "T044 useTransactions/useSync in frontend/features/transactions/"
Task: "T045 TransactionsGrid in frontend/features/transactions/TransactionsGrid.tsx"
Task: "T046 SyncPanel/SyncResult in frontend/features/transactions/SyncPanel/"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Phase 1 Setup, then Phase 2 Foundational. Verification run, then commit approval.
2. Phase 3 US1. Verification run, then commit approval. **M1 is demonstrable.**
3. Push only after its own approval, then deploy and smoke test.

### Incremental Delivery (Tuesday 10 Nov priority from the Phase 1A plan)

1. Foundation, then US1, then **US2 early**. Sandbox payments need up to 3 h to show up in Transaction Search, so make the 8–12 `/pay` payments the same day.
2. US3 seed fills the dashboard history needed by 002.
3. Polish, including the sandbox checks T071, before starting 002.

---

## Notes

- [P] tasks touch different files and have no dependencies on each other.
- Every user-visible number comes from tested code. 001 has no LLM.
- Money is `Decimal`/`NUMERIC(14,2)`, sent as strings in JSON, always with a currency. Fees are always stored as positive values.
- Never skip, delete or weaken a failing test, and never use `--no-verify`.
- No git or GitHub action without the owner's explicit approval for that action. This includes creating the branch (before T001) and the CI workflow (T009).
- Stay inside Phase 1A scope: no leakage, FX, dashboard, webhooks or refund handling in 001.
