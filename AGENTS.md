# AGENTS.md — PayLens

Rules for every AI coding agent and developer (Claude Code, Cursor, Google Antigravity, OpenCode, Copilot, Codex, Gemini CLI, and others).

## Read first (every session)

1. `.specify/memory/constitution.md` — **the rules. It always wins.**
2. `docs/PayLens_Phase1A_Hackathon_Plan.md` — **current scope.** Build only what is in it.
3. The active feature folder in `specs/NNN-feature/` (`spec.md`, `plan.md`, `tasks.md`).

`docs/PayLens_Project_Plan.md` is for later phases. Do not build from it now.

## Project in one line

PayLens: AI finance copilot for Indian freelancers paid via PayPal (sandbox only). Next.js + TypeScript frontend, FastAPI + Python backend, PostgreSQL, deployed on Render.

## Top rules (summary — details in the constitution)

- **Scope:** Phase 1A only. Order: 001-paypal-sync → 002-leakage-dashboard → 003-ask-your-money → (004-fira-matching → 005-ca-report if time allows).
- **Code computes, AI explains:** every number shown to users comes from tested code, never from the LLM.
- **Money:** `Decimal` / `NUMERIC` only, never `float`. Money is a string in JSON. Always with a currency.
- **Types:** Python type hints + `mypy --strict` + Pydantic at every boundary. TypeScript strict, no `any`, zod for API data, generated API types.
- **Verify after implementation:** write each task's tests as part of the task (backend pytest, frontend Vitest + Testing Library, Playwright E2E per user story). When the implementation is complete, run `npm run check:all`; fix and re-run until everything passes. Stop and report after 3 failed attempts on the same issue. Never call real PayPal or a real LLM in tests (use mocks / fake adapters).
- **Reuse first:** search for an existing component, hook, or helper before creating one. Shared code lives in `frontend/components/ui/`, `frontend/hooks/`, `frontend/lib/`, `backend/app/common/`.
- **Small files:** file ≤ 200 lines, component ≤ 150, function ≤ 40. Split parent → child → grandchild (max 3 levels). Import split folders through `index`.
- **No magic values:** thresholds and labels go in constants.
- **Security:** secrets only in `.env` / Render env vars. Sandbox only. No real personal data. Never expose the LLM key to the frontend.
- **Honest demo:** label `paypal_sandbox` / `demo_seed` data and "Simulated (sandbox)" FX rates.
- **Changelog:** add an entry to `CHANGELOG.md` under `[Unreleased]` for every change.
- **Git needs the owner's approval:** never `git add`/`commit`/`push`/`merge`/`rebase`/`reset`, change branches/tags, open PRs, or touch GitHub Actions without explicit approval for that exact action. Commit approval ≠ push approval. Read-only git (`status`, `diff`, `log`) is fine. Turn off auto-commit.
- **Commits:** Conventional Commits. Husky hooks run on approved commits and pushes. Never use `--no-verify`.

## Commands (run from repo root)

```
npm run lint          # ESLint, Prettier, ruff
npm run typecheck     # tsc --noEmit, mypy
npm run test:backend  # pytest
npm run test:unit     # Vitest
npm run test:e2e      # Playwright
npm run check:size    # file size limits
npm run check         # everything except E2E
npm run check:all     # everything (same as CI)
```

## Before saying a task is done

- [ ] Implementation complete, tests written, full verification loop green (`npm run check:all`)
- [ ] No lint, type, or size errors
- [ ] Reused existing blocks; no duplicated code
- [ ] `CHANGELOG.md` updated
- [ ] Still inside Phase 1A scope
- [ ] Show the verification report, changed files, proposed commit message and command
- [ ] **Wait for the owner's approval** before any git action

## If unsure

Stop and ask, or write `[NEEDS CLARIFICATION]` in the spec. Do not guess.

## Tool without Spec Kit commands?

Follow the same steps manually using `.specify/templates/` and save `spec.md`, `plan.md`, `tasks.md` in `specs/NNN-feature/`.
