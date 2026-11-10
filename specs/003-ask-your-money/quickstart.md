# Quickstart: validate 003-ask-your-money

- V1 `npm run check:all` — tests G1–G10, N1–N5, T1–T2, injection, grounding, timeout, rate limit; chat E2E.
- V2 real LLM (owner key in `backend/.env`: `LLM_API_KEY`, `LLM_MODEL`): seed, start backend, open `/chat`,
  ask "How much FX loss last quarter?" and compare with the dashboard (All time / month table).
- V3 remove `LLM_API_KEY` temporarily with `LLM_MODE=http` → backend refuses to start with a clear message.
