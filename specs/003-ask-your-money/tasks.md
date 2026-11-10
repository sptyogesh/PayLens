---
description: "Tasks for 003-ask-your-money"
---

# Tasks: Ask Your Money

**Tests**: required inside each task (constitution V). **Git**: no commits during the continuous run
(owner); proposals in the final report. Branch `001-paypal-sync`.

## Phase 1: Setup
- [X] T001 Constants (backend `app/common/constants.py`, see plan), settings `llm_mode`, `llm_api_key`, `llm_model`, `llm_api_url` in `app/config.py` (fake only with APP_ENV=test; http requires key), `.env.example`, conftest `LLM_MODE=fake`, Playwright/E2E env `LLM_MODE=fake`; tests in `tests/unit/test_config.py`

## Phase 2: Foundational
- [X] T002 [P] [A] `NamedPeriod` + `resolve_named(period, now)` + `resolve_dates(start, end)` + labels in `app/common/periods.py`; freezegun tests in `tests/unit/common/test_named_periods.py`
- [X] T003 [P] [A] `app/services/leakage_query.py` (`collect(session, start, end) -> Collected`); refactor `dashboard_service` onto it; tests keep passing + new unit tests
- [X] T004 `app/ai/types.py` (Figure, ToolResult, ToolInputError) — written by the main agent before A/B start (shared interface)
- [X] T005 [P] [B] Model `app/models/chat.py` (`chat_messages`), export; constraint test

## Phase 3: US1 — answers from my data (P1) 🎯
- [X] T006 [P] [A] Tools `app/ai/tools/{__init__,period_input,income_summary,fee_summary,get_transactions}.py` with Anthropic tool JSON schemas; integration tests per tool (period resolution, groups, money strings, has_data, figures, client filter, limit, rate-unavailable excluded) in `tests/integration/ai/test_tools.py`
- [X] T007 [P] [B] `app/ai/llm.py` (`AnthropicLlm` over httpx, errors → LlmUnavailableError / LlmConfigError, key never logged) + respx tests `tests/unit/ai/test_llm.py`; `app/fakes/llm_fake.py` + tests
- [X] T008 [P] [B] `app/ai/grounding.py` + `app/ai/answer_rules.py` + `app/ai/prompts/chat_system.md` + loader; unit tests (grounded / ungrounded / en-IN formats / years / small counts; tax keywords)
- [X] T009 [B] `app/ai/agent.py` loop (≤ LLM_MAX_TOOL_ROUNDS, append full content, all tool_results in one message, tool errors as is_error results, refusal/max_tokens → fallback); `app/schemas/chat.py`; `app/api/routes/chat.py` (rate limited, stores chat_messages); tests G1–G10 in `tests/ai/test_golden.py`, API tests in `tests/integration/api/test_chat_api.py`
- [X] T010 [P] [C] Frontend chat: `lib/api/chat-schemas.ts`, `CHAT_TEXT`, nav + `ROUTES.chat`, `features/chat/**`, `app/chat/page.tsx`, MSW fixtures/handler, unit tests (U9, figures, disclaimer, error/retry, loading)
- [X] T011 [US1] Integrate, `npm run gen:api`, contract check; Playwright `e2e/chat.spec.ts` E5 (answer number equals dashboard API), E11, E12
- [X] T012 [US1] Review (pr-review-toolkit) → fix; verification `npm run check:all`; RUN_LOG entry

## Phase 4: US2 — no data, tax, injection (P1)
- [X] T013 [US2] Tests N1–N5, T1, T2, prompt injection (client name with instructions + FAKE_INVENT) in `tests/ai/test_safety.py`; UI shows disclaimer; E2E E6 no-data question
- [X] T014 [US2] Review → fix; `npm run check:all`; RUN_LOG

## Phase 5: US3 — reliability (P2)
- [X] T015 [US3] Tests: LLM timeout/5xx/429 → fallback within timeout; round limit (FAKE_LOOP); 11th request → 429; key not in frontend bundle (E2E grep of served JS for `api.anthropic.com` and `LLM_API_KEY`); chat_messages storage failure ignored
- [X] T016 [US3] Review → fix; `npm run check:all`; CHANGELOG; RUN_LOG; tasks marked
