# Research: 003-ask-your-money

Checked 2026-11-10 against the bundled Claude API reference (claude-api skill, models table cached
2026-10-06) — Anthropic Messages API.

## R1. Provider and transport
- **Decision**: Anthropic Messages API over **httpx** (owner instruction: no SDK, no new packages).
  `POST {LLM_API_URL}/v1/messages`, headers `x-api-key: <LLM_API_KEY>`,
  `anthropic-version: 2026-10-21`, `content-type: application/json`.
- **Model**: `LLM_MODEL`, default `claude-opus-5-5` (current default model). On this model thinking is
  always on (no `thinking` param), `temperature`/`top_p` are rejected (400 on API version 2026-10-21),
  forced `tool_choice` `any`/`tool` returns 400 → use default `auto`. Effort via
  `output_config: {"effort": "low"}` (chat is a low-effort route).
- **Response**: `content` is a list of blocks: `text`, `tool_use` (`id`, `name`, `input`), and
  `thinking` blocks. `stop_reason` ∈ `end_turn`, `tool_use`, `max_tokens`, `stop_sequence`,
  `pause_turn`, `refusal`. In the tool loop the full assistant `content` (including thinking blocks)
  is appended unchanged, then one user message with **all** `tool_result` blocks
  (`{"type":"tool_result","tool_use_id":..., "content": "<json string>", "is_error"?: true}`).
- **Errors**: 429 / 5xx / 529 / network / timeout → `LlmUnavailableError` (no retry loop in the
  request path: the chat must answer within the timeout); 400/401/403/404 → `LlmConfigError`
  (logged without the key). Both become the friendly fallback (FR-009).
- **PDF (004)**: user content block `{"type":"document","source":{"type":"base64","media_type":"application/pdf","data":<b64>}}` before the text block.

## R2. Grounding check (FR-004, SC-003)
- Code extracts number tokens from the answer (`\d[\d,]*(\.\d+)?`), normalises (strip `,`), and
  accepts a token if it appears in: tool result values (money strings, counts, percents, rates,
  dates/years), the question, the resolved period dates, or is an integer ≤ 12. Otherwise the answer
  text is replaced by a safe sentence and outcome `fallback`; figures stay.
- Rationale: the LLM may legitimately round "₹1,26,678.93" — rounding is calculation, so it is
  rejected too (prompt tells it to copy numbers exactly).

## R3. Periods
- Named periods resolved by code in IST: calendar quarters, Indian financial year (Apr–Mar).
  Half-open ranges `[start, end)`; current periods end at "now".

## R4. Fake LLM
- `FakeLlm` (APP_ENV=test only) picks a tool from keywords, then writes an answer that copies the tool
  result numbers verbatim. Trigger words for tests: `FAKE_FAIL` (raises unavailable), `FAKE_INVENT`
  (answers with an invented number), `FAKE_LOOP` (keeps calling tools past the round limit).

## Hardening check — real LLM (2026-11-10)
- Not run: `LLM_API_KEY` and `LLM_MODEL` are not present in `backend/.env` (checked by key name only).
  With the default `LLM_MODE=http` the backend refuses to start without the key (fail fast). Owner
  action: add both to `backend/.env`, start the backend, ask "How much FX loss last quarter?" on `/chat`
  and compare with the dashboard; download a CA report to see an AI-written summary.
