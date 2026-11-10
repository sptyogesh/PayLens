# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. It is the PayLens project
override of the core plan template and follows `.specify/memory/constitution.md` (which always wins).

**Scope**: Phase 1A only — `docs/PayLens_Phase1A_Hackathon_Plan.md`. Feature order:
001-paypal-sync → 002-leakage-dashboard → 003-ask-your-money → (004-fira-matching → 005-ca-report
only if time allows). Do not plan anything from `docs/PayLens_Project_Plan.md` unless it is also
in the Phase 1A plan.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: The defaults below come from the constitution's Technology Stack.
  Keep them unless the spec requires otherwise; any new dependency MUST be justified
  under Complexity Tracking (Principle X).
-->

**Language/Version**: Python 3.11+ (backend), TypeScript strict (frontend)

**Primary Dependencies**: FastAPI, Pydantic v2, pydantic-settings, SQLAlchemy 2.x, httpx; Next.js
(App Router), Tailwind CSS, AG Grid Community, zod, openapi-typescript [add feature-specific ones]

**Storage**: PostgreSQL (`NUMERIC` for money: 2 dp amounts, 6 dp rates)

**Testing**: pytest (+ pytest-cov, pytest-asyncio, respx, hypothesis, freezegun); Vitest + React
Testing Library + MSW; Playwright + @axe-core/playwright. No real PayPal or LLM calls in tests.

**Target Platform**: Render (backend service, frontend service, PostgreSQL); PayPal sandbox only

**Project Type**: Web application (`backend/` + `frontend/`)

**Performance Goals**: [feature-specific or N/A for demo scale]

**Constraints**: [feature-specific, e.g., PayPal 31-day windows, LLM timeout, 5 MB PDF upload]

**Scale/Scope**: Single demo user, sandbox / synthetic data only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*
*Every row MUST be answered. Any ✗ MUST be justified under Complexity Tracking or the plan changed.*

| # | Principle | How this plan complies | ✓ / ✗ / N/A |
|---|---|---|---|
| I | Scope Discipline | [In Phase 1A plan? Must-haves before should-haves? Nothing on the not-built list?] | |
| II | Code Computes, AI Explains | [Which tested code produces every user-visible number? LLM does no arithmetic] | |
| III | Money Correctness | [`Decimal`/`NUMERIC`, currency with every amount, strings in JSON, ROUND_HALF_UP at the end, section 10 formulas, gains shown, "rate unavailable"] | |
| IV | Type Safety End to End | [mypy --strict, Pydantic at every boundary, TS strict, no `any`, zod, generated API types] | |
| V | Verify After Implementation | [Tests written inside each task; pytest + Vitest + ≥1 Playwright per user story; `npm run check:all` loop; coverage targets] | |
| VI | Security and Secrets | [Secrets in env only, sandbox only, LLM key backend-only, upload checks, prompt-injection defense, CORS] | |
| VII | Honest Demo | [`source` label visible, "Simulated (sandbox)" FX, CA disclaimer where relevant] | |
| VIII | PayPal Integration Rules | [Settings base URL, token cache, ≤31-day windows + pagination, idempotent upsert, retries, `raw_json`, docs verified] | |
| IX | AI Agent Rules | [`app/ai/llm.py` wrapper, read-only Pydantic tools, timeout + fallback, prompts in `app/ai/prompts/`] | |
| X | Simplicity | [No login/queue/microservices/caching; new dependencies justified] | |
| XI | Always Deployable | [`main` stays deployable; `/health`; smoke test on Render URL] | |
| XII | Reuse Before Create | [See "Reusable Parts" below] | |
| XIII | Small Files and Clear Hierarchy | [See "File Split Plan" below; limits 200 / 150 / 40 lines] | |
| XIV | Easy to Edit | [New constants listed; single source of truth for each formula/type] | |
| XV | Changelog and Documentation | [`CHANGELOG.md` entry; README updates if setup/features change] | |
| XVI | Automated Git Hooks (Husky) | [No hook bypass; hooks run on approved commits/pushes] | |
| XVII | Tooling and Plugins | [Only agreed tools; new tools justified] | |
| XVIII | Agent-Agnostic Rules | [Artifacts in `specs/NNN-feature/`; nothing tool-specific that contradicts the constitution] | |
| XIX | Human Approval for Git Actions | [No git/GitHub action without the owner's explicit approval for that action] | |

## Reusable Parts

*Required by Principle XII. Search the codebase before listing anything as new.*

**Existing parts used**:

- [e.g., `frontend/components/ui/MoneyText`, `backend/app/common/money.py`]

**New reusable parts created** (live in a shared folder, generic, typed props, no feature logic):

- [e.g., `frontend/components/ui/StatCard` — why it is reusable]

## File Split Plan

*Required by Principle XIII. Parent → child → grandchild, max 3 levels, import through `index`.*

| Parent | Children | Grandchildren | Public entry |
|---|---|---|---|
| [e.g., `frontend/app/dashboard/page.tsx`] | [e.g., `LeakageSummary`, `TransactionsGrid`] | [if needed] | [`index.ts`] |

**New constants** (Principle XIV): [e.g., `app/common/constants.py: PAYPAL_WINDOW_DAYS`]

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Keep only the paths this feature touches, following the constitution's
  Code Structure section. Add real file names.
-->

```text
backend/
├── app/
│   ├── common/          # shared: constants, types, errors, http_client, money, dates
│   ├── models/          # SQLAlchemy tables, one file per table
│   ├── schemas/         # Pydantic API models, one file per feature
│   ├── api/routes/      # thin routers
│   ├── services/        # orchestration
│   ├── paypal/          # PayPal client (sandbox)
│   ├── engine/          # pure, tested calculations (no DB, network, or file access)
│   ├── ai/              # llm.py wrapper, tools/ (read-only), prompts/
│   ├── fakes/           # fake PayPal + LLM adapters (APP_ENV=test only)
│   └── reports/         # CA report (S2 only)
└── tests/               # mirrors app/ paths: unit/, integration/, ai/

frontend/
├── app/                 # routes only — pages compose features
├── components/          # SHARED: ui/ building blocks, layout/ — no feature logic, no API calls
├── features/<feature>/  # feature code: index.ts, parent view, child folders, data hook
├── hooks/               # shared hooks (useApi, useAsync)
├── lib/                 # api/ (client, zod schemas, generated api-types.ts), constants, format
├── test/msw/            # API mock handlers for unit tests (unit tests sit beside their file)
└── e2e/                 # Playwright, one spec per user flow
```

**Structure Decision**: [Which of the paths above this feature uses and why]

## Complexity Tracking

> **Fill ONLY if the Constitution Check has a ✗ that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [principle + what] | [current need] | [why the compliant option is insufficient] |
