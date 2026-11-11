# Implementation Plan: PayPal Sandbox Sync

**Branch**: `001-paypal-sync` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/001-paypal-sync/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. It is the PayLens project
override of the core plan template and follows `.specify/memory/constitution.md` (which always wins).

**Scope**: Phase 1A only — `docs/PayLens_Phase1A_Hackathon_Plan.md`. Feature order:
001-paypal-sync → 002-leakage-dashboard → 003-ask-your-money → (004-fira-matching → 005-ca-report
only if time allows). Do not plan anything from `docs/PayLens_Project_Plan.md` unless it is also
in the Phase 1A plan.

## Summary

Build the **lean project foundation** (root tooling, Husky, test setup, the shared modules 001
needs) and **M1 PayPal sandbox sync** on top of it. The pieces are:

- **Sync**: a backend `paypal/` package that:
  - caches the OAuth token
  - splits the period into ≤31-day UTC windows
  - reads every page (`page_size=500`)
  - classifies each row by event code and amount sign
  - normalises fees to positive values
  - upserts by `paypal_transaction_id`
- **Run control**: each sync is recorded in `sync_runs`, guarded by a PostgreSQL advisory lock
  (one at a time), and runs once on startup.
- **`/pay` checkout**: the order is created and captured on the backend
  (`Prefer: return=representation`). The capture is recorded immediately. A reconcile fallback
  covers the case where the capture ID does not equal the Transaction Search ID, which PayPal
  doesn't document (research R1).
- **Seed**: an idempotent seed script for `demo_seed` history.
- **Rate limits**: an in-memory per-IP limiter on `POST /sync` and the `/pay` endpoints.
- **Front end**: Next.js `/transactions` (Sync now, last result, `DataGrid` list) and `/pay`.
- **Tests**: no test touches real PayPal. respx and MSW mock the HTTP calls, and E2E uses
  `FakePayPalGateway`.

## Technical Context

**Language/Version**:
- Python 3.12 (`>=3.11,<3.14`), pinned by `uv` through `.python-version` (R12)
- TypeScript (strict, all constitution flags)
- Node LTS (`.nvmrc`)

**Primary Dependencies**:
- Backend: FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2.x (typed `Mapped[...]`),
  psycopg 3 (binary), httpx, uvicorn.
- Frontend: Next.js (App Router), React, Tailwind CSS, AG Grid Community (`DataGrid`), zod,
  openapi-typescript, `@paypal/react-paypal-js` (justified in Complexity Tracking).
- Root: husky, lint-staged, @commitlint/cli, @commitlint/config-conventional, secretlint.

**Storage**: PostgreSQL 18.
- `NUMERIC(14,2)` for money, `NUMERIC(14,6)` for rates, `JSONB` for `raw_json`.
- Schema is created with `create_all` (no Alembic in Phase 1A, R10).

**Testing**:
- Backend: pytest, pytest-cov, respx, hypothesis, freezegun.
  - DB tests run against real PostgreSQL through `TEST_DATABASE_URL`, rolled back per test (R11).
- Frontend unit: Vitest, React Testing Library, user-event, jest-dom, jsdom, MSW.
- E2E: Playwright and @axe-core/playwright. The backend runs with `APP_ENV=test` and
  `PAYPAL_MODE=fake`.
- Not needed for 001: pytest-asyncio, because the backend is synchronous (R10).

**Target Platform**: Render (backend web service, frontend web service, PostgreSQL). PayPal sandbox
only, at `https://api-m.sandbox.paypal.com`.

**Project Type**: Web application (`backend/` + `frontend/`).

**Performance Goals**:
- Sync of ≤100 payments over 90 days in < 30 s (SC-003). That is 3 windows × 1 page each.
- A `/pay` payment is visible within 5 s of the confirmation (SC-004).

**Constraints**:
- Transaction Search: max 31-day range per request, `page_size` ≤ 500, data latency up to 3 h (R4).
- Retries: 3, with exponential backoff (base 1 s). On 401, refresh the token once.
- HTTP timeout: 10 s. Token refresh margin: 60 s before expiry.
- Rate limits:

  | Endpoint | Limit |
  |---|---|
  | `POST /sync` | 3 / 60 s / IP |
  | `POST /pay/orders` | 10 / 60 s / IP |
  | `POST /pay/orders/{id}/capture` | 10 / 60 s / IP |

- Checkout: max amount `CHECKOUT_MAX_AMOUNT = 10000.00`, description ≤ 127 characters.
- There is no PostgreSQL or Docker on the owner's machine yet. It is a quickstart prerequisite.

**Scale/Scope**: a single demo user. About 10–40 sandbox payments plus 24 seed rows.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Every row MUST be answered. Any ✗ MUST be justified under Complexity Tracking or the plan changed.*

**Pre-research gate: PASS. Post-design re-check: PASS** (see the note under the table).

| # | Principle | How this plan complies | ✓ / ✗ / N/A |
|---|---|---|---|
| I | Scope Discipline | M1 only, plus the foundation it needs. No leakage, FX, dashboard, chat, FIRA, webhooks or refunds. The `/pay` page and seed come from plan sections 5, 8 and 9. The setup phase is lean: no StatCard, FileUpload or LLM wrapper yet | ✓ |
| II | Code Computes, AI Explains | No LLM in 001. Every number (gross, fee, net, counts) comes from tested mapper and service code | ✓ |
| III | Money Correctness | `Decimal` and `NUMERIC(14,2)`. `Money{amount, currency}` everywhere. Strings in JSON. `abs(fee)` on ingestion. `net = gross − fee` in code plus a DB CHECK. Rounding happens only in `money.round_money` (ROUND_HALF_UP). No floats (ruff rule plus review) | ✓ |
| IV | Type Safety End to End | `mypy --strict` with the `pydantic.mypy` plugin. Pydantic models for every PayPal response, API body and setting. TS strict flags, no `any`, zod on every response, generated `api-types.ts` | ✓ |
| V | Verify After Implementation | Each task ships its tests (P1–P9, A1, A3–A6, U1–U3, U6–U8, U11, E2/E3/E10–E12 for these pages). `npm run check:all` loop. Coverage targets: engine N/A in 001, backend overall ≥ 70%, `components/ui` and `lib` ≥ 80% | ✓ |
| VI | Security and Secrets | Secrets only in `.env` or Render. Only the public sandbox client ID goes to the browser. Sandbox base URL comes from settings. CORS allowlist. Logs carry no tokens or `raw_json`. secretlint in pre-commit. Rate limits (R8) | ✓ |
| VII | Honest Demo | `source` badge on every row. Demo-mode banner. Sandbox notice on `/pay`. No PayPal logo as branding (the official button is allowed) | ✓ |
| VIII | PayPal Integration Rules | Base URL from settings. Token cache. ≤31-day windows with full pagination. Idempotent upsert on the unique `paypal_transaction_id`. 429/5xx retried 3× with backoff. 401 refreshes once. `raw_json` stored. Endpoints verified in research.md, with sandbox checks V5–V8 for the undocumented points | ✓ |
| IX | AI Agent Rules | No AI in 001. The `fakes/` pattern is set up so `llm_fake` slots in for 003 | N/A |
| X | Simplicity | Synchronous stack, `create_all`, an in-memory rate limiter, an advisory lock. No queue, Redis or Alembic. Two new dependencies are justified below | ✓ |
| XI | Always Deployable | `/health`. Work stays on the `001-paypal-sync` branch until the owner approves a merge. Smoke test V9 after deploy | ✓ |
| XII | Reuse Before Create | See Reusable Parts. This is a greenfield repo, so everything shared is created in shared folders first | ✓ |
| XIII | Small Files and Clear Hierarchy | See File Split Plan. Every module is ≤ 200 lines and every component ≤ 150. `scripts/check_file_size.py` and ESLint `max-lines` enforce it | ✓ |
| XIV | Easy to Edit | All limits are constants: windows, page size, retries, rate limits, max amount, sync days, reconcile window, stale minutes, income event codes. Labels live in `lib/constants.ts` | ✓ |
| XV | Changelog and Documentation | `CHANGELOG.md` is created in setup, and the final task adds 001 under `[Unreleased]`. The README gets setup and sandbox steps | ✓ |
| XVI | Automated Git Hooks (Husky) | Hooks: pre-commit (lint-staged, size, secretlint), commit-msg (commitlint), pre-push (tsc, Vitest, mypy, fast pytest). Never `--no-verify` | ✓ |
| XVII | Tooling and Plugins | Only tools from the constitution list, plus `@paypal/react-paypal-js` and `psycopg` (needed as the PostgreSQL driver). Versions pinned in the lockfiles. `.vscode` recommendations included | ✓ |
| XVIII | Agent-Agnostic Rules | `CLAUDE.md` imports `AGENTS.md`. `.cursor/rules/paylens.mdc` points to `AGENTS.md`. All artifacts live in `specs/001-paypal-sync/` | ✓ |
| XIX | Human Approval for Git Actions | No git action without approval. **Creating `.github/workflows/ci.yml` needs the owner's explicit approval** (Principle XIX lists creating Actions workflows). The task is marked to stop and ask | ✓ |

Post-design note: two changes came out of research.
- Required Test **P8** wins over spec FR-013, so non-payment events are **stored** with a `kind` and
  excluded from income. The spec has been updated to match.
- The capture-ID question is undocumented (R1), so the design adds a guarded reconcile fallback
  instead of assuming the IDs match.

Neither change creates a violation.

## Reusable Parts

*Required by Principle XII. The repo is greenfield, so the search found nothing to reuse yet.*

**Existing parts used**: none (no application code exists yet).

**New reusable parts created** (all live in shared folders, are generic, and contain no feature
logic):

Backend (`backend/app/common/`):

| Part | What it does |
|---|---|
| `constants.py` | Every threshold and limit for 001 |
| `types.py` | `Money`, `CurrencyCode`, and the enums `TransactionSource`, `TransactionOrigin`, `TransactionKind`, `TransactionStatus`, `SyncTrigger`, `SyncOutcome`, `FiraStatus` |
| `money.py` | `round_money`, `parse_money`, `to_api_string` (`to_inr` is deferred to 002) |
| `dates.py` | `split_windows(start, end, max_days)`, `utc_now`, `ensure_utc` |
| `errors.py` | `AppError` hierarchy (`PayPalError`, `SyncInProgressError`, `RateLimitedError`, `ValidationAppError`, …) plus the handlers that produce the standard error shape |
| `http_client.py` | httpx `Client` factory with timeout, plus `send_with_retry` (429/5xx backoff, no retry on other 4xx) |
| `rate_limit.py` | `FixedWindowLimiter` and a `rate_limit(name, limit, window)` FastAPI dependency |
| `db.py` / `config.py` | Typed settings; engine and session dependency (app root, per the constitution) |

Backend fakes: `backend/app/fakes/paypal_fake.py`, which provides `FakePayPalGateway` behind the
same `PayPalGateway` Protocol.

Frontend:

| Location | Parts |
|---|---|
| `components/ui/` | `Button`, `Card`, `Badge` (all 5 variants), `MoneyText`, `DataGrid`, `Spinner`, `EmptyState`, `ErrorState`, `Disclaimer` |
| `components/layout/` | `AppShell`, `PageHeader` (with the demo-mode banner) |
| `hooks/` | `useApi` (GET with loading, error and data, plus zod), `useMutation` (POST with the same states) |
| `lib/` | `api/client.ts`, `api/schemas.ts` (zod), `api/api-types.ts` (generated), `format.ts` (`formatMoney`, `formatINR`, `formatDate` in IST), `constants.ts` |

Deferred until the feature that first needs them: `StatCard` (002), `FileUpload` (004),
`money.to_inr` (002), `ai/llm.py` and `fakes/llm_fake.py` (003).

## File Split Plan

*Required by Principle XIII. Parent → child → grandchild, max 3 levels, import through `index`.*

| Parent | Children | Grandchildren | Public entry |
|---|---|---|---|
| `backend/app/paypal/sync.py` (coordinator: lock → windows → pages → upsert → run record) | `transactions_api.py` (one page fetch), `mapper.py` (row → `TransactionUpsert`), `classify.py` (event code + sign → kind), `upsert.py` (match, reconcile, insert) | — | `paypal/__init__.py` |
| `backend/app/paypal/` gateway | `auth.py` (token cache), `orders_api.py` (create/capture), `gateway.py` (`PayPalGateway` Protocol + `HttpPayPalGateway`), `schemas.py` (PayPal Pydantic models) | `schemas_search.py`, `schemas_orders.py` if `schemas.py` passes 120 lines | `paypal/__init__.py` |
| `backend/app/services/sync_service.py` (runs sync, records `sync_runs`, startup hook) | `sync_lock.py` (advisory lock context manager) | — | module |
| `backend/app/services/checkout_service.py` (create order, capture, record) | uses `paypal.mapper.from_capture` | — | module |
| `backend/app/services/transaction_service.py` (list query) | — | — | module |
| `backend/app/api/routes/` | `health.py`, `sync.py`, `transactions.py`, `pay.py` (thin) | — | `api/routes/__init__.py` (router list) |
| `backend/app/models/` | `client.py`, `transaction.py`, `sync_run.py`, `base.py` | — | `models/__init__.py` |
| `backend/app/schemas/` | `common.py` (`MoneyOut`, `ErrorOut`), `transaction.py`, `sync.py`, `pay.py` | — | `schemas/__init__.py` |
| `backend/scripts/seed_demo.py` (CLI) | `seed_data.py` (fixed rows) | — | script |
| `frontend/features/transactions/TransactionsView.tsx` | `SyncPanel/` (`SyncPanel.tsx`, `SyncResult.tsx`), `TransactionsGrid.tsx` (column defs → `DataGrid`), `useTransactions.ts`, `useSync.ts` | `SyncResult.tsx` is the grandchild | `features/transactions/index.ts` |
| `frontend/features/pay/PayView.tsx` | `PayForm.tsx` (amount, currency, description + zod), `PayButton/` (`PayPalCheckoutButton.tsx`, `FakeCheckoutButton.tsx`, `index.ts` picks one by mode), `PayResult.tsx`, `usePayOrder.ts` | `PayPalCheckoutButton` / `FakeCheckoutButton` are the grandchildren | `features/pay/index.ts` |
| `frontend/app/` | `layout.tsx` (`AppShell`), `page.tsx` (redirect), `transactions/page.tsx`, `pay/page.tsx` (each only renders its feature view) | — | Next.js routes |

**New constants** (Principle XIV):

`backend/app/common/constants.py`:

| Constant | Value |
|---|---|
| `PAYPAL_WINDOW_DAYS` | 31 |
| `PAYPAL_PAGE_SIZE` | 500 |
| `PAYPAL_MAX_PAGES_PER_WINDOW` | 50 |
| `PAYPAL_TOKEN_REFRESH_MARGIN_S` | 60 |
| `HTTP_TIMEOUT_S` | 10 |
| `HTTP_MAX_RETRIES` | 3 |
| `HTTP_BACKOFF_BASE_S` | 1 |
| `SYNC_DEFAULT_DAYS` | 90 |
| `SYNC_LOCK_KEY` | |
| `SYNC_STALE_AFTER_MINUTES` | 10 |
| `CHECKOUT_RECONCILE_WINDOW_HOURS` | 72 |
| `INCOME_EVENT_CODES` | |
| `EVENT_CODE_KIND_PREFIXES` | |
| `CHECKOUT_CURRENCIES` | |
| `CHECKOUT_MAX_AMOUNT` | |
| `CHECKOUT_DESCRIPTION_MAX` | 127 |
| `RATE_LIMIT_SYNC` | (3, 60) |
| `RATE_LIMIT_PAY` | (10, 60) |
| `TRANSACTIONS_PAGE_MAX` | 200 |
| `SEED_FEE_PERCENT` | |
| `SEED_FEE_FIXED` | per currency |

`frontend/lib/constants.ts`: routes, source labels ("PayPal sandbox", "Demo seed"), "Demo mode — PayPal
sandbox data", the sandbox checkout notice, sync messages, `CHECKOUT_CURRENCIES`,
`CHECKOUT_DESCRIPTION_MAX`.

## Project Structure

### Documentation (this feature)

```text
specs/001-paypal-sync/
├── plan.md              # This file
├── research.md          # PayPal doc findings R1–R12 with sources
├── data-model.md        # clients, transactions, sync_runs, seed
├── quickstart.md        # V1–V9 validation guide
├── contracts/
│   └── http-api.md      # /health, /sync, /sync/last, /transactions, /pay/*
├── checklists/
│   └── requirements.md
└── tasks.md             # /speckit-tasks output (not created yet)
```

### Source Code (repository root)

The setup phase creates only what 001 and the verification loop need:

```text
package.json                 # root tooling + the shared scripts (lint, typecheck, test:*, check, check:all, check:size)
.husky/{pre-commit,commit-msg,pre-push}
.lintstagedrc.json  commitlint.config.mjs  .secretlintrc.json  .editorconfig  .nvmrc
.vscode/{extensions.json,settings.json}
.github/workflows/ci.yml     # ⚠ create only after the owner's explicit approval (XIX)
AGENTS.md (exists)  CLAUDE.md  .cursor/rules/paylens.mdc  CHANGELOG.md  README.md (update)
scripts/check_file_size.py   # repo-level, run by check:size and pre-commit

backend/
├── pyproject.toml  uv.lock  .python-version  .env.example  requirements.txt (exported)
├── app/
│   ├── main.py  config.py  db.py
│   ├── common/      constants, types, money, dates, errors, http_client, rate_limit
│   ├── models/      base, client, transaction, sync_run
│   ├── schemas/     common, transaction, sync, pay
│   ├── api/routes/  health, sync, transactions, pay
│   ├── services/    sync_service, sync_lock, checkout_service, transaction_service
│   ├── paypal/      auth, gateway, transactions_api, orders_api, schemas, classify, mapper, upsert, sync
│   └── fakes/       paypal_fake (APP_ENV=test only)
├── scripts/         seed_demo, seed_data, export_openapi
└── tests/
    ├── conftest.py              # TEST_DATABASE_URL session, rollback per test, settings override
    ├── fixtures/paypal/         # JSON samples: search pages, token, capture
    ├── unit/common/             # money, dates, rate_limit, errors
    ├── unit/paypal/             # classify, mapper, auth cache
    ├── integration/paypal/      # sync P1–P9 (respx + DB)
    ├── integration/services/    # checkout, reconcile, seed
    └── integration/api/         # A1, A3–A6, 409, 429

frontend/
├── package.json  tsconfig.json  next.config.ts  eslint.config.mjs  vitest.config.ts  playwright.config.ts  .env.example
├── app/            layout, page (redirect), transactions/page, pay/page
├── components/ui/  Button, Card, Badge, MoneyText, DataGrid, Spinner, EmptyState, ErrorState, Disclaimer
├── components/layout/ AppShell, PageHeader
├── features/       transactions/, pay/
├── hooks/          useApi, useMutation
├── lib/            api/{client,schemas,api-types}, format, constants
├── test/           setup.ts, msw/{handlers,server}.ts
└── e2e/            transactions.spec.ts, pay.spec.ts, a11y.spec.ts, global-setup.ts (reset + seed e2e DB)
```

**Structure Decision**: this follows the constitution's Code Structure. There are two changes, both
splitting a planned file further (Principle XIII):
- `paypal/` adds `classify.py`, `upsert.py`, `gateway.py` and `orders_api.py`.
- `services/` adds `sync_lock.py` and `checkout_service.py`.

`scripts/check_file_size.py` lives at the repo root, not under `backend/`, because it checks both
apps. The constitution's tree places it under `backend/scripts/`. Either location satisfies the
principle, and the root is chosen so the frontend doesn't depend on `backend/`.

## Complexity Tracking

> **Fill ONLY if the Constitution Check has a ✗ that must be justified**

There are no ✗ rows. New dependencies are recorded here as Principle X requires:

| Dependency | Why Needed | Simpler Alternative Rejected Because |
|---|---|---|
| `@paypal/react-paypal-js` | Official wrapper for loading the JS SDK and rendering the buttons, including reloading the script when the currency changes (R7) | Hand-managing the `<script>` and button lifecycle means more code and edge cases |
| `psycopg[binary]` (v3) | A PostgreSQL driver is required by SQLAlchemy | No alternative: some driver is needed. psycopg 3 is the maintained default for SQLAlchemy 2 |
| Reconcile fallback (R1) | Capture ID = Transaction Search ID is undocumented. Without the fallback, `/pay` payments could duplicate | Assuming the IDs match risks duplicate income (breaks SC-002) |
