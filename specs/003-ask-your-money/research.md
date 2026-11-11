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

## R5. Gemini adapter (owner choice 2026-11-11: free tier, no budget)
Sources, read 2026-11-11 (ai.google.dev/gemini-api/docs/* now redirects to aistudio.google.com/docs/*;
the generateContent variants are the `*.md?generate-content=true` pages listed in
https://aistudio.google.com/llms.txt): `pricing`, `models`, `function-calling`, `thought-signatures`,
`structured-output`, `document-processing`, `whats-new-gemini-3.8`, `api-errors`, `api-key`, and the
API reference `api-reference/generate-content/generate-content`. Context7 was not available in this
session; no SDK is used (httpx only, no new packages).
- **Decision**: `GeminiLlm` (`app/ai/gemini.py`, translation in `gemini_format.py`) implements the same
  `LlmClient` contract as `AnthropicLlm`. The internal format stays the Anthropic block format, so the
  agent loop, FIRA extraction, report summary and their grounding/number checks are unchanged.
- **Endpoint/auth**: `POST https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent`,
  header `x-goog-api-key` (never the `?key=` query form: URLs are logged by httpx).
- **Default model**: `gemini-3.6-flash`. Model page: "Stable: gemini-3.6-flash" (latest update July
  2026); inputs include PDF; function calling, structured outputs and thinking "supported". Pricing
  page: Free Tier input and output "Free of charge". Not chosen: `gemini-3.8-flash` (newest, same
  features and free tier) — on 2026-11-11 the real check got 503 UNAVAILABLE "This model is
  currently experiencing high demand" and four timeouts (60–90 s) while `gemini-3.6-flash` answered
  in 4 s with the same key; set `LLM_MODEL=gemini-3.8-flash` to use it. `gemini-2.5-flash` is
  deprecated (routes to 3.5 Flash-Lite from 1 Dec 2026).
- **Request mapping**: `system` → `systemInstruction.parts[].text`; roles `user`/`model`; tools →
  `tools[].functionDeclarations[]` with `parametersJsonSchema` (JSON Schema; local `$defs`/`$ref` are
  inlined because the docs do not promise `$ref` support); `generationConfig.maxOutputTokens`,
  `thinkingConfig.thinkingLevel: LOW` (supported on Gemini 3 Flash models; `minimal` errors on 3.8); no
  temperature/topP/topK (ignored on 3.6+ and to become 400). PDF → `inlineData {mimeType, data}`
  (limit 50 MB / 1000 pages; FIRA uploads are ≤ 5 MB). Strict output →
  `generationConfig.responseFormat.text {mimeType: APPLICATION_JSON, schema}` (supports `anyOf`,
  `null`, `required`, `additionalProperties`, `description`).
- **Function calling**: Gemini 3 "always returns a unique `id` with every `functionCall`"; the result
  is sent back as `functionResponse {id, name, response}` in a `user` turn; `response` must be an
  object (`{"error": ...}` for failures). If an id is ever missing, a local id is used and never sent.
- **Thought signatures**: "When using Gemini 4 and Gemini 3 models, you must pass back thought
  signatures during function calling, otherwise you will get a validation error (4xx)", in the exact
  part where received. The adapter stores `thoughtSignature` on the block (`gemini_thought_signature`)
  and sends it back on the same part. Parts with `thought: true` are dropped.
- **Response mapping**: any `functionCall` → `stop_reason` `tool_use`; `finishReason` `STOP` →
  `end_turn`, `MAX_TOKENS` → `max_tokens`, anything else (SAFETY, MALFORMED_FUNCTION_CALL, …) →
  `refusal`; no candidates + `promptFeedback.blockReason` → `refusal`; no candidates otherwise, invalid
  JSON or wrong shapes → `LlmUnavailableError` (fallback).
- **Errors** (api-errors, generateContent): 429 RESOURCE_EXHAUSTED (rate limit or quota) →
  `LlmUnavailableError(code=LLM_BUSY)` → "The AI is busy, try again shortly" (chat, FIRA upload; the
  report uses its code summary); 500/503/504 → unavailable; 400 (incl. FAILED_PRECONDITION free tier
  not in country), 402 (no prepay credit), 403, 404 → `LlmConfigError`. Applies to Anthropic too.
- **Provider selection** (`app/common/llm_provider.py`, run in Settings validation): `LLM_PROVIDER` if
  set; else from the key prefix: `sk-ant-` → anthropic, `AIza` (standard keys) or `AQ.` (auth keys,
  the default for new AI Studio keys since 28 May 2026 — prefix observed, Google does not document
  it) → gemini; an unknown prefix without `LLM_PROVIDER` is refused. Refused at startup: a key whose
  prefix belongs to another provider than `LLM_PROVIDER`, a model of the other family (`claude*` /
  `gemini*`), the other provider's default URL, a model name with URL-unsafe characters. Settings
  errors hide input values (`hide_input_in_errors`), so the key is never printed.
- **Data use**: pricing page, Free tier: "Content used to improve our products" (Paid: "not used").
  PayLens sends only sandbox data, demo seed and generated sample FIRAs; README states this.

## Hardening check — real LLM (2026-11-10)
- Not run: `LLM_API_KEY` and `LLM_MODEL` are not present in `backend/.env` (checked by key name only).
  With the default `LLM_MODE=http` the backend refuses to start without the key (fail fast). Owner
  action: add both to `backend/.env`, start the backend, ask "How much FX loss last quarter?" on `/chat`
  and compare with the dashboard; download a CA report to see an AI-written summary.

## Real LLM check — Gemini (2026-11-11)
- Provider `gemini` detected from the key prefix (auth key), model `gemini-3.6-flash`, test database
  with the demo seed (24 payments). Key never printed.
- Chat "How much FX loss did I have in all time?" → `fee_summary` (All time), 4.0 s, outcome
  `answered`, passed grounding: "your total FX loss was 49750.42 INR across 24 payments … Simulated
  (sandbox)". Dashboard all time: FX loss 49750.42, payments 24 — equal.
- FIRA `sample_data/fira_samples/fira-SEED-0001.pdf` → 4.3 s, all 8 fields equal to the PDF's true
  fields, no problems.
- `gemini-3.8-flash` on the same day: 503 "high demand" and timeouts (see R5).
