---
description: "Tasks for 002-leakage-dashboard"
---

# Tasks: Leakage Dashboard

**Input**: Design documents from `specs/002-leakage-dashboard/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/http-api.md, quickstart.md

**Tests**: REQUIRED (constitution Principle V). Each implementation task writes its own tests in the
same task. Full verification (`npm run check:all`) at the end of each story. Tests never call real
Frankfurter, PayPal or an LLM (respx, MSW, `FX_MODE=fake`, `PAYPAL_MODE=fake` with `APP_ENV=test`).

**Git**: Work stays on `001-paypal-sync` (owner decision). No task commits, pushes or changes
branches; each story ends with **Request commit approval** (Principle XIX).

## Format: `[ID] [P?] [Story] Description`

---

## Phase 1: Setup

- [X] T001 Bookkeeping for 001 in `specs/001-paypal-sync/tasks.md`: mark T032, T050, T062, T067 done (commits fb74ac1…2c19716 exist) and annotate T068–T075 "carried forward: README/CHANGELOG/label check → 002 polish and Phase 1A final step; T071/T075 owner-assisted after deploy"
- [X] T002 Add constants to `backend/app/common/constants.py`: `SIMULATED_FX_SPREAD = Decimal("0.03")`, `INR = "INR"`, `DISPLAY_TIME_ZONE = "Asia/Kolkata"`, `FX_API_DEFAULT_URL = "https://api.frankfurter.dev"`, `FX_PROVIDER = "ecb"`, `FX_SOURCE_NAME = "frankfurter_ecb"`, `FX_FAKE_SOURCE_NAME = "fake"`, `FX_TIMEOUT_S = 5.0`, `PERCENT_PLACES = Decimal("0.01")`, `PERCENT_FACTOR = Decimal(100)`
- [X] T003 [P] Settings: add `fx_mode: Literal["http","fake"] = "http"` and `fx_api_url: str = FX_API_DEFAULT_URL` to `backend/app/config.py`; `FX_MODE=fake` only allowed when `APP_ENV=test` (same rule as PayPal); `FX_MODE`/`FX_API_URL` in `backend/.env.example`; tests in `backend/tests/unit/test_config.py`; conftest sets `FX_MODE=fake`

---

## Phase 2: Foundational

- [X] T004 [P] Shared helpers + tests: `round_rate` (6 dp half-up) and `to_rate_string` in `backend/app/common/money.py`; `ist_date(dt)` and `ist_month_start(now, months_back)` in `backend/app/common/dates.py` (tests in `backend/tests/unit/common/test_money.py`, `test_dates.py`)
- [X] T005 [P] `FxUnavailableError` (code `FX_UNAVAILABLE`, 502) in `backend/app/common/errors.py` + test
- [X] T006 Model `backend/app/models/fx_rate.py` (`fx_rates`: currency CHAR(3), rate_date DATE, published_date DATE, rate NUMERIC(14,6), source VARCHAR(32), fetched_at TIMESTAMPTZ; `UNIQUE(currency, rate_date)`, `CHECK(rate > 0)`, `CHECK(published_date <= rate_date)`), export in `models/__init__.py`; constraint tests in `backend/tests/integration/models/test_constraints.py`

**Checkpoint**: foundation ready

---

## Phase 3: User Story 1 — See what each payment lost (P1) 🎯 MVP

**Goal**: every completed income payment shows INR leakage, recalculated after sync, seed and `/pay`.

**Independent Test**: seed (fake FX) → `/transactions` shows leakage columns matching section 10, "Simulated (sandbox)" visible, sort by total leakage works.

- [X] T007 [P] [US1] Engine `backend/app/engine/leakage/{__init__,types,calculate}.py`: `LeakageInput` (Decimal only, floats rejected; gross ≥ 0, fee ≥ 0, fee ≤ gross), `LeakageResult`, `RateUnavailable`, `calculate_leakage()`, `simulated_paypal_rate(mid)`; tests L1–L10 (L10 with hypothesis) in `backend/tests/unit/engine/leakage/test_calculate.py`
- [X] T008 [P] [US1] FX integration `backend/app/fx/{__init__,gateway,schemas,frankfurter}.py`: `FxGateway` Protocol `mid_rate(currency, on) -> FxQuote | None`; `FrankfurterGateway` calls `GET /v2/rate/{CUR}/INR?date=&providers=ecb`, parses with `json.loads(parse_float=Decimal)` + Pydantic, 404/422 → None, transport/5xx → `FxUnavailableError`; respx tests in `backend/tests/unit/fx/test_frankfurter.py`
- [X] T009 [P] [US1] Fake `backend/app/fakes/fx_fake.py` (fixed rates USD 84.000000, GBP 106.500000, EUR 90.250000, AUD 55.100000; unknown currency → None; weekend → previous Friday as published_date) + `get_fx_gateway()` in `backend/app/api/deps.py`; unit test
- [X] T010 [US1] `backend/app/services/fx_rate_service.py`: `RateLookup` that reads `fx_rates`, fetches missing (currency, IST date) once, stores, INR → 1, fail-fast after the first `FxUnavailableError`; integration tests (cache hit = no second fetch, outage → None for the rest of the run) in `backend/tests/integration/services/test_fx_rate_service.py`
- [X] T011 [US1] `backend/app/services/leakage_service.py`: `recalculate_leakage(session, fx)` recomputes eligible rows (income + completed), clears non-eligible, leaves `rate_unavailable` rows NULL, never raises (logs); `safe_recalculate(factory, fx)` wrapper; integration tests incl. P8 (non-income excluded) in `backend/tests/integration/services/test_leakage_service.py`
- [X] T012 [US1] Hook recalculation into `services/sync_service.start_sync` (+ startup thread), `services/checkout_service.capture_and_record`, `scripts/seed_demo.py`; routes pass `get_fx_gateway`; update existing tests for the new parameter; FX failure never changes sync/pay/seed results (tests)
- [X] T013 [US1] API: `backend/app/schemas/leakage.py` (`LeakageOut`, `leakage_status` derivation) and extend `TransactionOut` in `backend/app/schemas/transaction.py`; tests A3 + leakage fields in `backend/tests/integration/api/test_transactions_api.py`
- [X] T014 [US1] Regenerate `frontend/lib/api/openapi.json` + `api-types.ts` (`npm run gen:api`), extend zod in `frontend/lib/api/schemas.ts` (+ contract), add `formatPercent`/`formatRate` to `frontend/lib/format.ts`, `LEAKAGE_TEXT` to `frontend/lib/constants.ts`; tests in `format.test.ts`, `client.test.ts`
- [X] T015 [US1] Grid columns split: `frontend/features/transactions/columns/{index.ts,baseColumns.tsx,leakageColumns.tsx}`; leakage columns: Mid-market rate, PayPal rate "Simulated (sandbox)", INR received, Fee loss, FX loss (`gainWhenNegative`), Total leakage, Leakage %; INR received and FX loss headers also carry "Simulated (sandbox)" (FR-004); "Rate unavailable"/"Not calculated" text; exact sort via `compareAmounts`; tests in `TransactionsGrid.test.tsx`
- [X] T016 [US1] Playwright: `FX_MODE=fake` in `frontend/playwright.config.ts`; `frontend/e2e/transactions.spec.ts` — seeded rows show leakage, "Simulated (sandbox)" visible (E4), sort by total leakage (E3)
- [X] T017 [US1] Verification run: `npm run check:all` → fix → re-run (stop after 3 failed attempts on one issue); add the story's CHANGELOG entry
- [ ] T018 [US1] Request commit approval: `feat(leakage): calculate per-payment fee and FX loss in INR`

---

## Phase 4: User Story 2 — Leakage summary for a period (P1)

**Goal**: dashboard home page with five cards and a period filter.

**Independent Test**: seed → `/` shows five ₹ cards for "Last 3 months"; switching period changes them; values equal API totals.

- [X] T019 [P] [US2] Engine `backend/app/engine/leakage/aggregate.py`: `LeakageRow`, `LeakageTotals`, `totals(rows)`, `by_month(rows)`, `by_client(rows)` (sorting per contract); tests L11, L12 in `backend/tests/unit/engine/leakage/test_aggregate.py`
- [X] T020 [P] [US2] `backend/app/services/periods.py`: `DashboardPeriod` enum (`this_month`, `last_3_months`, `all_time`), labels, `resolve(period, now)` in IST; freezegun tests in `backend/tests/unit/services/test_periods.py`
- [X] T021 [US2] `backend/app/services/dashboard_service.py` + `backend/app/schemas/dashboard.py` + `backend/app/api/routes/dashboard.py` (`GET /dashboard?period=`): totals, excluded_count, sources, spread; empty → `totals: null`; tests A2 in `backend/tests/integration/api/test_dashboard_api.py`
- [X] T022 [P] [US2] Shared UI `frontend/components/ui/StatCard/` (title, value node, hint; U5) and `frontend/components/ui/SegmentedControl/` (radio group, keyboard accessible); tests beside each
- [X] T023 [US2] Regenerate API types; zod `dashboardSchema`; `DASHBOARD_TEXT`, `PERIOD_OPTIONS`, `ROUTES.dashboard`, nav item "Dashboard" in `frontend/lib/constants.ts`
- [X] T024 [US2] `frontend/features/dashboard/{index.ts,DashboardView.tsx,useDashboard.ts,PeriodFilter.tsx,LeakageSummary/}` + `frontend/app/page.tsx`; empty state, excluded note, sources line, Simulated notice; tests beside each file (MSW)
- [X] T025 [US2] Playwright `frontend/e2e/dashboard.spec.ts`: E1 cards show ₹ and no console errors, period switch, E11 (390 px), E12 axe on dashboard
- [X] T026 [US2] Verification run: `npm run check:all`
- [ ] T027 [US2] Request commit approval: `feat(dashboard): add leakage summary cards with period filter`

---

## Phase 5: User Story 3 — Where the leakage comes from (P2)

**Goal**: month and client breakdown tables under the cards.

**Independent Test**: seed → "All time" → month and client tables sum to the cards.

- [ ] T028 [US3] `by_month`/`by_client` in `GET /dashboard` response (`BreakdownRowOut`); test that Σ rows = totals in `test_dashboard_api.py`
- [ ] T029 [US3] `frontend/features/dashboard/Breakdown/{index.ts,BreakdownTables.tsx,breakdownColumns.tsx}` using `DataGrid`; tests beside
- [ ] T030 [US3] Playwright: month and client tables visible with rows in `frontend/e2e/dashboard.spec.ts`
- [ ] T031 [US3] Verification run: `npm run check:all`
- [ ] T032 [US3] Request commit approval: `feat(dashboard): add leakage breakdown by month and client`

---

## Phase 6: User Story 4 — Deployable on Render (P2, polish)

> **Owner decision 2026-11-10**: render.yaml moves to the Phase 1A hardening pass (created, not deployed); README deploy steps and the deployment itself happen after the owner's manual testing. T033, T034, T037, T038 are deferred; T035 (CHANGELOG) is done per story.

- [ ] T033 [US4] `render.yaml`: database `paylens-db` (`postgresMajorVersion: "18"`, plan free), `paylens-api` (runtime python, rootDir backend, `uv sync --frozen --no-dev`, uvicorn start, `healthCheckPath: /health`, envVars incl. `DATABASE_URL` fromDatabase, secrets `sync: false`), `paylens-web` (runtime node, rootDir frontend, `npm ci && npm run build`, `npm start`); `autoDeployTrigger: checksPass`; a pytest that parses render.yaml and checks every Settings field without a default and every `NEXT_PUBLIC_*` used by the frontend is declared, in `backend/tests/unit/test_render_blueprint.py`
- [ ] T034 [US4] README: "Deploy on Render" steps + environment variable table (backend and frontend; secret / where from); free-tier notes (15-min spin-down, 30-day DB expiry); FX reference-rate and "Simulated (sandbox)" notes
- [ ] T035 Update `CHANGELOG.md` under `[Unreleased]` for 002
- [ ] T036 [US4] Verification run: `npm run check:all`
- [ ] T037 [US4] Request commit approval: `chore(deploy): add Render blueprint and deployment guide`
- [ ] T038 Owner deploys on Render (quickstart V5) and confirms the live URL; then run the live smoke test (001 T075 + dashboard)

---

## Dependencies & Execution Order

- Setup (T001–T003) → Foundational (T004–T006) → US1 → US2 → US3 → US4.
- US2 needs US1's stored leakage; US3 extends US2's endpoint and view.
- Within US1: T007, T008, T009 in parallel; T010 → T011 → T012; T013 → T014 → T015 → T016.

## Parallel Examples

- US1: engine (T007), Frankfurter client (T008), fake FX (T009).
- US2: aggregate (T019), periods (T020), StatCard/SegmentedControl (T022).

## Implementation Strategy

MVP = US1 (per-payment leakage in the grid). US2 makes M2's done-when (cards). US3 and US4
complete the feature and the first deployment.
