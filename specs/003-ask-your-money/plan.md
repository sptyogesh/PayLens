# Implementation Plan: Ask Your Money

**Branch**: `001-paypal-sync` | **Date**: 2026-11-10 | **Spec**: [spec.md](spec.md)

## Summary
`POST /chat` runs a small agent: the single LLM wrapper (`app/ai/llm.py`, Anthropic Messages API over
httpx) may call three read-only tools whose results come from the 002 leakage engine. Code resolves
periods, builds the "Based on" figures from tool results, checks every number in the answer against
tool values (grounding), replaces empty results with a "data not available" answer, and adds the CA
disclaimer for tax questions. Frontend `/chat` page shows the conversation, figures and disclaimer.

## Technical Context
Python 3.12 / FastAPI / SQLAlchemy / httpx; Next.js / zod / Vitest / Playwright. **No new
dependencies.** New table `chat_messages`. LLM timeout 20 s, ≤ 4 tool rounds, 10 req/min per IP.
Tests: respx for the HTTP client, `LLM_MODE=fake` everywhere else.

## Constitution Check
| # | Principle | Compliance | ✓ |
|---|---|---|---|
| I | Scope | M3 from plan sections 2, 11, 12; must-haves before S1/S2 | ✓ |
| II | Code computes | Tools use the leakage engine; figures from tool results; grounding check rejects any LLM number not in tool output; no-data answer written by code | ✓ |
| III | Money | Decimals in tools, strings in JSON with currency; gains kept negative in data | ✓ |
| IV | Types | Pydantic tool inputs/outputs, ChatIn/ChatOut, LLM response models; zod on frontend; generated types | ✓ |
| V | Verify | G1–G10, N1–N5, T1–T2, injection, U9, E5, E6, E11, E12; check:all per story | ✓ |
| VI | Security | Key only in backend settings; never logged; fake LLM test-only; question length limit; rate limit; injection defence (data framing + read-only tools + grounding) | ✓ |
| VII | Honest demo | CA disclaimer by code for tax; "Simulated (sandbox)" note on FX figures; source labels in get_transactions | ✓ |
| VIII | PayPal | Not touched | N/A |
| IX | AI rules | One wrapper; read-only Pydantic tools; timeout + fallback; prompt file in `app/ai/prompts/` | ✓ |
| X | Simplicity | httpx, no SDK; no streaming; stateless chat with client-side history | ✓ |
| XI | Deployable | New env vars in `.env.example`; startup fails fast without key in http mode | ✓ |
| XII | Reuse | See below | ✓ |
| XIII | Small files | Split below | ✓ |
| XIV | Easy to edit | Constants: rate limit, timeout, rounds, limits, tax keywords; prompt file | ✓ |
| XV | Changelog | Per story | ✓ |
| XVI–XIX | Hooks, tooling, agent-agnostic, git approval | No commits during the run (owner) | ✓ |

## Reusable Parts
**Used**: leakage engine (`totals`, `by_month`, `by_client`), `stored_result`, `common/periods`,
`common/dates`, `MoneyOut`, `rate_limit` dependency, `errors`, `useApi`/`apiPost` client, `MoneyText`,
`Button`, `TextField`, `ErrorState`, `Spinner`, `Disclaimer`, `PageHeader`, `Card`.
**New reusable**: `services/leakage_query.py` (eligible rows for any range; dashboard refactored onto
it, reused by tools and the 005 report); `NamedPeriod` resolution in `common/periods.py` (reused by
005); `components/ui/TextArea` (if TextField cannot do multi-line).

## File Split Plan
| Parent | Children | Public entry |
|---|---|---|
| `app/ai/agent.py` (loop coordinator) | `ai/grounding.py`, `ai/answer_rules.py` (no-data, tax, refusal text), `ai/prompts/__init__.py` + `chat_system.md` | `app.ai.agent.answer_question` |
| `app/ai/tools/__init__.py` (registry) | `period_input.py`, `income_summary.py`, `fee_summary.py`, `get_transactions.py` | `TOOL_DEFINITIONS`, `run_tool` |
| `app/ai/llm.py` | `app/fakes/llm_fake.py` | `get_llm` |
| `frontend/features/chat/ChatPanel.tsx` | `MessageList/{MessageList,MessageBubble,FigureList}.tsx`, `ChatInput.tsx`, `SuggestedQuestions.tsx`, `useChat.ts` | `features/chat/index.ts` |

**Parallel subagents (tasks marked [P])**: A = backend tools + periods + leakage_query; B = LLM wrapper,
fake, agent, grounding, schemas, model, route, config; C = frontend chat. Interfaces fixed in
`contracts/http-api.md`; each agent owns disjoint files; main agent integrates.

**New constants**: backend `RATE_LIMIT_CHAT`, `LLM_TIMEOUT_S`, `LLM_MAX_TOOL_ROUNDS`, `LLM_MAX_TOKENS`,
`LLM_EFFORT`, `LLM_API_VERSION`, `LLM_DEFAULT_MODEL`, `LLM_DEFAULT_API_URL`, `CHAT_QUESTION_MAX`,
`CHAT_HISTORY_MAX`, `CHAT_TOOL_ROWS_MAX`, `TAX_KEYWORDS`, `NOT_TAX_ADVICE`; frontend `CHAT_TEXT`,
`ROUTES.chat`, `SUGGESTED_QUESTIONS`.

## Complexity Tracking
None.
