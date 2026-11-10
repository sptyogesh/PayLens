# Quickstart: validate 002-leakage-dashboard

Prerequisites: 001 quickstart done (PostgreSQL 18, `backend/.env`, `npm install`).

## V1 — automated (fake FX)

```bash
npm run check:all
```

Expected: engine tests L1–L12 green (engine coverage ≥ 90%), API tests A2/A3 green, Vitest
U4/U5 green, Playwright dashboard + transactions leakage specs green (desktop + 390 px), axe clean.

## V2 — real Frankfurter, local

```bash
cd backend
# FX_MODE defaults to http, FX_API_URL to https://api.frankfurter.dev
uv run python -m scripts.seed_demo          # seeds 24 rows and calculates leakage
uv run uvicorn app.main:app --reload
curl -s localhost:8000/dashboard?period=all_time | python -m json.tool | head -40
```

Expected: 24 payments in `totals.payment_count` (minus any with `rate_unavailable`), FX values
present, `paypal_rate_simulated: true`. `psql paylens_dev -c "select currency, rate_date,
published_date, rate from fx_rates order by 2 limit 10"` shows weekend dates with an earlier
`published_date`.

## V3 — by hand: worked example

Open `/transactions`, pick one USD row, and check with a calculator:
`fee_loss = fee × mid`, `fx_loss = net × (mid − paypal)`, `total = fee_loss + fx_loss`,
`leakage % = total ÷ (gross × mid) × 100`.

## V4 — FX outage

Stop network or set `FX_API_URL=http://127.0.0.1:9` and run the seed with new dates: rows show
"Rate unavailable"; seed still reports success; restoring the URL and pressing Sync now fills them.

## V5 — Render (owner)

Follow README "Deploy on Render". Expected: `https://<backend>.onrender.com/health` → `{"status":"ok"}`;
dashboard loads on the frontend URL; Sync now works with sandbox credentials.
