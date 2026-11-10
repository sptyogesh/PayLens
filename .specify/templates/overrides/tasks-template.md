---

description: "Task list template for feature implementation (PayLens override)"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `/specs/[###-feature-name]/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: REQUIRED (constitution Principle V). Each implementation task writes its own tests in the
same task, based on the spec and the constitution's **Required Test Cases**. The full verification
run happens after implementation, not before. Every user story has at least one Playwright test.
Tests never call real PayPal or a real LLM (respx, MSW, fake adapters with `APP_ENV=test`).

**Git**: No task commits, pushes, or changes branches on its own. Each story ends with a
**Request commit approval** task; only the owner's explicit approval allows a git action
(Principle XIX).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions, including the test file(s) the task adds

## Path Conventions

- **Backend**: `backend/app/...`, tests in `backend/tests/` mirroring app paths
- **Frontend**: `frontend/features/<feature>/`, shared code in `frontend/components/ui/`,
  `frontend/hooks/`, `frontend/lib/`; unit tests beside the file they test; E2E in `frontend/e2e/`
- Follow the File Split Plan in plan.md (file ≤ 200 lines, component ≤ 150, function ≤ 40)

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements, Reusable Parts, and File Split Plan from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  Ordering rules (constitution Development Workflow):
  - Shared reusable blocks come before the feature code that uses them
  - Each implementation task includes its tests
  - Each user story ends with: Verification run → Request commit approval
  - The last task of the feature is "Update CHANGELOG.md"

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Anything this feature needs that the project does not have yet

- [ ] T001 [Setup task, e.g., add new constants to backend/app/common/constants.py]
- [ ] T002 [P] [Setup task, e.g., add `.env.example` entry for a new setting]

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared, reusable parts that MUST exist before any user story uses them (Principle XII)

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [ ] T003 [Model/migration, e.g., backend/app/models/[entity].py + tests in backend/tests/unit/...]
- [ ] T004 [P] [Shared helper, e.g., backend/app/common/money.py + hypothesis tests]
- [ ] T005 [P] [Shared UI block, e.g., frontend/components/ui/[Block]/ + [Block].test.tsx]

**Checkpoint**: Foundation ready - user story implementation can now begin

---

## Phase 3: User Story 1 - [Title] (Priority: P1) 🎯 MVP

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Implementation for User Story 1 (each task includes its tests)

- [ ] T006 [P] [US1] [Pure engine logic] in backend/app/engine/[module].py, tests in backend/tests/unit/engine/[module]/
- [ ] T007 [US1] [Service] in backend/app/services/[service].py, tests in backend/tests/integration/...
- [ ] T008 [US1] [Route + Pydantic schema] in backend/app/api/routes/[name].py, API tests with TestClient
- [ ] T009 [US1] Regenerate frontend/lib/api/api-types.ts and add zod schema in frontend/lib/api/schemas.ts
- [ ] T010 [US1] [Feature UI] in frontend/features/[feature]/, Vitest + Testing Library tests beside each file
- [ ] T011 [US1] Playwright test for the story's main flow in frontend/e2e/[flow].spec.ts

### Verification for User Story 1

- [ ] T012 [US1] Verification run: `npm run check:all` → fix root cause → re-run until all pass (stop and report after 3 failed attempts on the same issue)
- [ ] T013 [US1] Request commit approval: show verification report, changed files, proposed Conventional Commit message and exact command; wait for the owner's explicit approval

**Checkpoint**: At this point, User Story 1 should be fully functional and independently testable

---

## Phase 4: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]

**Independent Test**: [How to verify this story works on its own]

### Implementation for User Story 2 (each task includes its tests)

- [ ] T014 [P] [US2] [Task with file path and its test file]
- [ ] T015 [US2] [Task with file path and its test file]
- [ ] T016 [US2] Playwright test in frontend/e2e/[flow].spec.ts

### Verification for User Story 2

- [ ] T017 [US2] Verification run: `npm run check:all` → fix → re-run until green
- [ ] T018 [US2] Request commit approval (wait for the owner)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

---

[Add more user story phases as needed, following the same pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] TXXX [P] README updates if setup, features, or usage changed
- [ ] TXXX Check labels: `source` (`paypal_sandbox` / `demo_seed`), "Simulated (sandbox)", CA disclaimer where relevant
- [ ] TXXX Run quickstart.md validation
- [ ] TXXX Final verification run: `npm run check:all` until green
- [ ] TXXX Update CHANGELOG.md under `[Unreleased]` (reference `specs/[###-feature-name]`)
- [ ] TXXX Request commit approval (wait for the owner); push needs its own separate approval
- [ ] TXXX After an approved push/merge and deploy: smoke test on the Render URL

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - Proceed sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **User Story 3 (P3)**: Can start after Foundational (Phase 2) - May integrate with US1/US2 but should be independently testable

### Within Each User Story

- Shared/reusable parts → engine (pure) → models → services → routes → API types/zod → UI → E2E
- Each implementation task is done only when its tests exist
- Verification run, then Request commit approval, before moving to the next story

### Parallel Opportunities

- Tasks marked [P] touch different files and can run in parallel
- Engine, shared helpers, and shared UI blocks within a phase can usually run in parallel

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (implementation with tests)
4. **Verification run** until green, then **request commit approval**
5. Deploy/demo after the owner approves the push

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Each user story → verification run → owner approval → deploy → smoke test
3. Each story adds value without breaking previous stories; `main` stays deployable

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Every user-visible number comes from tested code, never the LLM (Principle II)
- Money: `Decimal` / `NUMERIC`, strings in JSON, always with a currency (Principle III)
- Never skip, delete, or weaken a failing test; never use `--no-verify`
- No git or GitHub action without the owner's explicit approval for that action (Principle XIX)
- Stay inside Phase 1A scope (Principle I)
