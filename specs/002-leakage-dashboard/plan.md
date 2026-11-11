# Implementation Plan: Leakage Dashboard

**Branch**: `001-paypal-sync` (owner decision: no new branch) | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-leakage-dashboard/spec.md`

**Scope**: Phase 1A only — M2 leakage dashboard, plus the Render blueprint and README deploy steps
(polish).

## Summary

Compute per-payment fee loss, FX loss, total leakage and leakage % in INR with a pure, tested
engine (plan section 10). Mid-market rates come from Frankfurter (ECB reference rates, keyless),
cached in a new `fx_rates` table; the PayPal rate is simulated as mid-market minus a 3% spread
constant and labelled "Simulated (sandbox)". Leakage is recalculated synchronously after sync,
seed and `/pay`. A new `GET /dashboard?period=` returns cards plus month and client breakdowns, all
computed in backend code; `GET /transactions` gains leakage fields. Frontend: the home page becomes
the dashboard (StatCards, period SegmentedControl, two DataGrid breakdowns) and the transactions
grid gets leakage columns. Polish: `render.yaml` + README deployment section.

## Technical Context

**Language/Version**: Python 3.12 (backend), TypeScript strict (frontend)

**Primary Dependencies**: existing stack only — FastAPI, Pydantic v2, SQLAlchemy 2, httpx; Next.js,
AG Grid Community, zod. **No new dependencies.**

**Storage**: PostgreSQL 18; new table `fx_rates`; existing leakage columns on `transactions`
(created empty by 001) are now filled.

**Testing**: pytest (+ hypothesis for L10, respx for Frankfurter, freezegun for periods); Vitest +
RTL + MSW; Playwright + axe. FX in tests and E2E uses `FX_MODE=fake` (test only).

**Target Platform**: Render (blueprint), PayPal sandbox only

**Project Type**: Web application (`backend/` + `frontend/`)

**Performance Goals**: demo scale (< 200 rows); dashboard response < 1 s locally

**Constraints**: FX fetch is best-effort (single attempt, fail fast) so `/pay` and sync never wait
on retries; money/rates as `Decimal`; `create_all` cannot alter existing tables → no new columns on
`transactions`.

**Scale/Scope**: Single demo user, sandbox / synthetic data only

## Constitution Check

| # | Principle | How this plan complies | ✓ / ✗ / N/A |
|---|---|---|---|
| I | Scope Discipline | M2 from plan sections 2, 9, 10, 12; render.yaml is plan section 14. No login, queue or extra features | ✓ |
| II | Code Computes, AI Explains | Every number from `engine/leakage` (unit + property tests) and `dashboard_service`; no LLM in this feature | ✓ |
| III | Money Correctness | `Decimal`/`NUMERIC(14,2)`/`NUMERIC(14,6)`; rates parsed with `parse_float=Decimal`; ROUND_HALF_UP only on outputs; strings in JSON with currency `INR`; negative FX loss shown as gain; "rate unavailable" status, no numbers | ✓ |
| IV | Type Safety End to End | mypy strict; Pydantic for Frankfurter response, engine inputs/outputs and API; TS strict; zod schemas; `npm run gen:api` regenerates `api-types.ts` | ✓ |
| V | Verify After Implementation | Tests inside each task (L1–L12, A2, A3, U4, U5, E1, E3, E4, E11, E12); Playwright per story; `check:all` at each story end; engine ≥ 90% coverage | ✓ |
| VI | Security and Secrets | No new secrets (Frankfurter is keyless); `FX_API_URL` from settings; render.yaml uses `sync: false` for secrets; CORS unchanged | ✓ |
| VII | Honest Demo | "Simulated (sandbox)" on PayPal rate, INR received and FX loss (grid headers + dashboard notice); source labels listed on dashboard; README notes reference rates | ✓ |
| VIII | PayPal Integration Rules | No change to PayPal calls; recalculation runs after the existing idempotent upsert | N/A |
| IX | AI Agent Rules | No AI in this feature | N/A |
| X | Simplicity | Recompute-all at demo scale; no cache layer beyond the `fx_rates` table the spec requires; no new dependency | ✓ |
| XI | Always Deployable | `render.yaml` with `/health` check and `autoDeployTrigger: checksPass`; branch not merged until owner decides | ✓ |
| XII | Reuse Before Create | See Reusable Parts | ✓ |
| XIII | Small Files and Clear Hierarchy | See File Split Plan; engine and dashboard split into packages with `__init__`/`index` | ✓ |
| XIV | Easy to Edit | New constants listed below; formulas only in `engine/leakage/calculate.py` | ✓ |
| XV | Changelog and Documentation | CHANGELOG entries per story; README deploy + env var section | ✓ |
| XVI | Automated Git Hooks | No bypass; hooks run on approved commits | ✓ |
| XVII | Tooling and Plugins | No new tools | ✓ |
| XVIII | Agent-Agnostic Rules | Artifacts in `specs/002-leakage-dashboard/` | ✓ |
| XIX | Human Approval for Git Actions | Commit gate after every story; no branch/push/merge without approval | ✓ |

## Reusable Parts

**Existing parts used**:

- Backend: `common/money.round_money`/`to_api_string`, `common/types.Money`, `common/http_client.make_client`,
  `common/errors.AppError`, `common/dates.ensure_utc`/`utc_now`, `schemas/common.MoneyOut`,
  `models/base.RATE`/`MONEY`, `api/deps` pattern (`get_gateway` → `get_fx_gateway`), seed CLI, sync
  and checkout services (hook points).
- Frontend: `MoneyText` (`gainWhenNegative` for FX loss, U4), `DataGrid`, `Card`, `Badge`,
  `Disclaimer`, `EmptyState`, `ErrorState`, `Spinner`, `PageHeader`, `useApi`, `compareAmounts`,
  `formatDate`, `DISCLAIMERS.simulated`, `SOURCE_LABELS`.

**New reusable parts created**:

- `backend/app/common/dates.py`: `ist_date(dt)`, `ist_month_start(dt, months_back)` — IST helpers
  reused by 003 (chat periods) and 005 (report periods).
- `backend/app/common/money.py`: `round_rate(value)` (6 dp half-up), `to_rate_string`.
- `backend/app/engine/leakage/` — public API `calculate_leakage`, `aggregate`, used by 003 tools and
  005 report.
- `frontend/components/ui/StatCard` — title + `MoneyText`/text value + hint (U5).
- `frontend/components/ui/SegmentedControl` — accessible radio group for period choice (005 reuses).
- `frontend/lib/format.ts`: `formatPercent("7.25")` → `7.25%`, `formatRate("84.000000")`.

## File Split Plan

| Parent | Children | Grandchildren | Public entry |
|---|---|---|---|
| `backend/app/engine/leakage/__init__.py` | `calculate.py` (one row), `aggregate.py` (totals, by month, by client), `types.py` (inputs/outputs) | — | `engine/leakage/__init__.py` |
| `backend/app/fx/__init__.py` | `gateway.py` (Protocol), `frankfurter.py` (HTTP), `schemas.py` (response) | — | `fx/__init__.py` |
| `backend/app/services/leakage_service.py` | uses `fx_rate_service.py` (cache lookup/fetch) | — | module |
| `backend/app/services/dashboard_service.py` | uses `periods.py` (in `services/`) and engine aggregate | — | module |
| `frontend/features/dashboard/DashboardView.tsx` | `useDashboard.ts`, `PeriodFilter.tsx`, `LeakageSummary/` (`LeakageSummary.tsx`), `Breakdown/` (`BreakdownTables.tsx`) | `LeakageSummary/SummaryNotes.tsx`, `Breakdown/breakdownColumns.tsx` | `features/dashboard/index.ts` |
| `frontend/features/transactions/TransactionsGrid.tsx` | `columns/baseColumns.tsx`, `columns/leakageColumns.tsx` | — | `columns/index.ts` |

**New constants** (Principle XIV):
- Backend `common/constants.py`: `SIMULATED_FX_SPREAD`, `INR`, `FX_RATE_DATE_TZ = "Asia/Kolkata"`,
  `FX_PROVIDER = "ecb"`, `FX_SOURCE_NAME = "frankfurter_ecb"`, `PERCENT_PLACES`,
  `DASHBOARD_PERIODS`, `DASHBOARD_DEFAULT_PERIOD`, `FX_API_DEFAULT_URL`.
- Frontend `lib/constants.ts`: `ROUTES.dashboard`, nav item, `DASHBOARD_TEXT`, `PERIOD_OPTIONS`,
  `LEAKAGE_TEXT` (column headers, "Rate unavailable", "Not calculated").

## Project Structure

### Documentation (this feature)

```text
specs/002-leakage-dashboard/
├── plan.md  research.md  data-model.md  quickstart.md
├── contracts/http-api.md
└── tasks.md
```

### Source Code

```text
backend/app/
├── common/{constants,dates,money,errors}.py      # extended
├── config.py                                     # + fx_mode, fx_api_url (fake only in test)
├── models/fx_rate.py                             # new table
├── engine/leakage/{__init__,types,calculate,aggregate}.py
├── fx/{__init__,gateway,frankfurter,schemas}.py
├── fakes/fx_fake.py
├── services/{fx_rate_service,leakage_service,periods,dashboard_service}.py
├── services/{sync_service,checkout_service}.py   # call recalculate at the end
├── schemas/{leakage,dashboard}.py, schemas/transaction.py (+ leakage)
├── api/deps.py (+ get_fx_gateway), api/routes/dashboard.py
backend/scripts/seed_demo.py                      # recalculate after seed
backend/tests/unit/engine/leakage/, unit/fx/, integration/services/, integration/api/

frontend/
├── app/page.tsx                                  # dashboard
├── components/ui/{StatCard,SegmentedControl}/
├── features/dashboard/…
├── features/transactions/columns/…
├── lib/{constants,format}.ts, lib/api/schemas.ts (+ generated api-types)
├── e2e/dashboard.spec.ts, e2e/transactions.spec.ts (leakage), playwright.config.ts (FX_MODE=fake)
render.yaml, README.md
```

**Structure Decision**: Web app; follows the constitution's Code Structure. `app/fx/` is a new
integration package parallel to `app/paypal/` (FX is an outbound integration with its own
schema and fake, like PayPal).

## Complexity Tracking

No ✗ in the Constitution Check.
