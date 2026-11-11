# Quickstart / Validation Guide: 001-paypal-sync

This guide proves the feature works. For the details, see
[contracts/http-api.md](contracts/http-api.md) and [data-model.md](data-model.md).

## Prerequisites

- **Python 3.12** through `uv`, which installs it for you.
- **Node** at the LTS version in `.nvmrc`.
- **PostgreSQL 18**, running locally (matches CI and Render). On
  Ubuntu/Debian:
  `sudo apt install postgresql`. Then create two databases, `paylens_test` and `paylens_e2e`.
  Add `paylens_dev` if you want to run the app against real sandbox data.
- Only for the real-sandbox checks (V5–V8), a PayPal sandbox set up as in plan section 8:
  - 1 Business account (the freelancer)
  - 4 Personal accounts (US/USD, UK/GBP, DE/EUR, AU/AUD)
  - 1 REST app with **Transaction Search** enabled
- `backend/.env` and `frontend/.env.local` copied from the `.env.example` files and filled in.
  Never commit them.

## Install

```bash
npm install                       # root tooling + husky hooks
(cd backend && uv sync)
(cd frontend && npm install)
npx playwright install chromium
```

## V1 — Verification loop (automated, no PayPal needed)

```bash
export TEST_DATABASE_URL=postgresql+psycopg://localhost/paylens_test
npm run check:all
```

**Expected**: every step passes, in this order: lint → typecheck → size → pytest → Vitest →
Playwright. Required Tests P1–P9, A1, A3–A6 and U1–U3, U6–U8, U11 are green. E2E E2 (Sync now),
E3 (source badge part), E10, E11 and E12 are green for `/transactions` and `/pay`.

## V2 — Hooks

1. Stage a file that is over 200 lines or contains a fake secret. `git commit` is **blocked**.
2. Use the commit message `update stuff`. commitlint **rejects** it.

Run this only on throwaway changes, with the owner's approval for the commit attempt (Principle XIX).

## V3 — Fake-mode demo (local, no PayPal)

```bash
(cd backend && APP_ENV=test PAYPAL_MODE=fake uv run uvicorn app.main:app --reload)
(cd frontend && NEXT_PUBLIC_PAYPAL_MODE=fake npm run dev)
```

1. Open `/transactions` and press **Sync now**. The fake data shows up: 10 added and 2 skipped.
2. Press **Sync now** again. The summary shows 0 added, and the row count doesn't change.
3. Open `/pay`, enter `50.00 USD`, and click **Pay (test mode)**. A confirmation shows the
   transaction ID, and the row is listed with **PayPal sandbox**.
4. Try to set `APP_ENV=production PAYPAL_MODE=fake`. The backend **refuses to start**.

## V4 — Seed

```bash
(cd backend && uv run python -m scripts.seed_demo)
(cd backend && uv run python -m scripts.seed_demo)
(cd backend && uv run python -m scripts.seed_demo --reset)
```

- After the first run: 24 rows labelled **Demo seed**, across 4 clients and 4 months.
- After the second run: still 24 rows.
- After `--reset`: the seed rows are gone, and the `paypal_sandbox` rows are untouched.

## V5–V8 — Real sandbox checks

These answer the open questions in research R1–R4. Record each result in
[research.md](research.md).

| # | Do | Record |
|---|---|---|
| V5 | Pay 50.00 USD on `/pay` with the US personal account, wait up to 3 h, then Sync now | R1: does Transaction Search `transaction_id` equal the stored capture ID? Was the row updated, not duplicated? |
| V6 | Use "Send money" from the UK personal account to the business account, wait, then Sync now | R2: the event code for "Send money" and for the `/pay` payment. Is each classified as `income`? |
| V7 | Inspect `raw_json` of a synced payment (DB only) | R3: the real sign of `fee_amount`. Stored fee is positive and gross − fee = net |
| V8 | Call Sync with `page_size` forced to 2 (test setting) over a period with more than 2 payments | R4: `page=1` is the first page, and every payment is stored once |

## V9 — Deployed smoke test

Run this after an approved push and the Render deploy:

1. `GET /health` returns `ok`.
2. `/transactions` loads, and Sync now succeeds.
3. A `/pay` payment shows up in the list.
4. Pressing Sync now 4 times within a minute gives **429 Too many requests** on the 4th.
