# Research: 002-leakage-dashboard

All findings checked on 2026-11-10. Sources are listed per item.

## R1. FX source: Frankfurter (free, keyless, INR, historical)

- **Decision**: Use Frankfurter **v2** single-rate endpoint
  `GET {FX_API_URL}/v2/rate/{BASE}/INR?date=YYYY-MM-DD&providers=ecb`, with
  `FX_API_URL=https://api.frankfurter.dev`.
- **Verified response** (live call, 2026-11-10):
  - `GET /v2/rate/USD/INR?date=2026-11-07` → `200 {"date":"2026-11-07","base":"USD","quote":"INR","rate":94.09}` (blended sources, default)
  - `GET /v2/rates?base=USD&quotes=INR&date=2026-11-07&providers=ecb` →
    `200 [{"date":"2026-11-06","base":"USD","quote":"INR","rate":93.92}]` — Saturday request
    returns Friday's ECB rate and **the response `date` is the published date**.
  - `GET /v1/2026-11-06?base=XYZ&symbols=INR` → `404 {"message":"not found"}`.
  - Docs: errors are `400` (bad parameter), `404` (currency/rate not found), `422`
    (`{"status":422,"message":"invalid currency: ABC"}`).
- **Facts from docs** (https://frankfurter.dev/, https://frankfurter.dev/v1/,
  https://frankfurter.dev/currencies/):
  - "You don't need an API key." "There are no quotas. Requests are rate-limited to prevent abuse";
    caching is encouraged. Commercial use allowed.
  - v1 is deprecated but "remains available indefinitely"; v2 is current.
  - INR (1973–present), USD, GBP, EUR, AUD all covered. v1 = ECB data; v2 blends many central
    banks, `providers=ecb` restricts to the ECB.
  - Rates are **reference rates**, not live quotes (README says so).
- **Why ECB provider**: one well-known source, documented weekend behaviour (latest earlier
  working day, which satisfies spec FR-002), stable over time.
- **Precision**: `rate` is a JSON number. It MUST be parsed with `json.loads(..., parse_float=Decimal)`
  so no float is ever created (Principle III), then validated by a Pydantic model and quantized to
  6 dp.
- **Alternatives rejected**: exchangerate.host / Open Exchange Rates / currencylayer (API key
  needed); fawazahmed0 currency-api via CDN (no SLA, daily snapshot files, no published-date
  semantics); RBI reference rate (no stable public API).

## R2. Caching and failure handling

- **Decision**: new `fx_rates` table, unique `(currency, rate_date)`, storing `rate`, the
  `published_date` from the response, `source` (`frankfurter_ecb` or `fake`) and `fetched_at`.
  A pair is fetched once; later calculations read the table.
- **Failure policy**: FX is best-effort during recalculation. One attempt per pair with the
  shared HTTP timeout (no retry loop — we must not hold `/pay` responses for 7 s of backoff).
  After the first transport/5xx failure in a run, the remaining missing pairs are skipped for that
  run ("fail fast"); rows stay "rate unavailable" and are retried on the next sync/seed/pay.
  A 404/422 means "no rate for this currency" → not cached, row stays unavailable.
- **Shared code change**: `common/http_client.send_with_retry` currently raises `PayPalError`.
  FX does not need retries, so FX uses `make_client` + a single `client.get` and maps errors to a
  new `FxUnavailableError` in `common/errors.py`. `http_client` stays unchanged.

## R3. Rate date and INR payments

- **Decision**: rate date = payment's calendar date in `Asia/Kolkata` (spec FR-002). INR payments
  use rate `1.000000` for both rates with no fetch (FX loss 0). A future date (clock skew) is
  clamped to today.

## R4. Simulated PayPal rate

- **Decision**: `SIMULATED_FX_SPREAD = Decimal("0.03")` (3%) in `common/constants.py`.
  `r_pp = round6(r_mid × (1 − SIMULATED_FX_SPREAD))`. Plan section 9 says "mid-market rate minus a
  fixed spread"; a percentage keeps it proportional across USD/GBP/EUR/AUD. Stored in
  `transactions.paypal_rate`; the API returns `paypal_rate_simulated: true` so the UI labels it.

## R5. Formulas and rounding

- **Decision**: `engine/leakage/calculate.py` implements plan section 10 exactly, rounding
  half-up to 2 dp only on outputs:
  `ideal = G·r_mid`, `received = N·r_pp`, `fee_loss = F·r_mid`, `fx_loss = N·(r_mid − r_pp)`,
  `total = round2(fee_loss) + round2(fx_loss)` and `received = round2(ideal) − total`, so every
  shown identity holds exactly (fee + FX = total, ideal − received = total, cards = Σ breakdown
  rows). Each value stays within ₹0.015 of its exact section 10 value; this is property-tested
  (L10). `leakage_percent = round2(exact total / exact ideal × 100)`. (Changed after the US2
  review: rounding the total separately made the cards differ by ₹0.01.)
- `ideal_inr` and `leakage_percent` are **derived at read time** from stored values with the same
  engine function (no new column on `transactions`, so no migration is needed;
  `Base.metadata.create_all` only adds the new `fx_rates` table).

## R6. Recalculation strategy

- **Decision**: `recalculate_leakage(session, fx)` recomputes every eligible row (kind `income`,
  status `completed`) and clears leakage on non-eligible rows. Demo scale (< 200 rows) makes
  "recompute all" cheap and removes the need to track amount changes. Called at the end of
  `start_sync`, `capture_and_record`, and the seed CLI. Errors inside recalculation are logged and
  never fail the calling action (FR-005).

## R7. Periods and grouping

- **Decision**: periods computed in IST: `this_month` = [first day of current IST month, now];
  `last_3_months` = [first day of the IST month two months ago, now]; `all_time` = no bounds.
  Month key = `YYYY-MM` of the IST date. Grouping done in Python by the pure engine (`aggregate.py`)
  over the eligible rows, so totals = Σ rows exactly (SC-003).

## R8. Render blueprint (https://render.com/docs/blueprint-spec, /docs/free, /docs/uv-version,
/docs/native-runtimes, /docs/monorepo-support)

- Root keys `services`, `databases`. Database fields: `name`, `databaseName`, `user`, `plan: free`,
  `postgresMajorVersion: "18"` (string; default is "the most recent version supported (currently
  18)"), `region`, `ipAllowList`.
- Web service: `type: web`, `runtime: python` / `runtime: node`, `rootDir`, `buildCommand`,
  `startCommand`, `healthCheckPath`, `plan: free`, `region`, `autoDeployTrigger: commit|checksPass|off`.
- envVars: `sync: false` (prompted on first Blueprint creation only), `generateValue`,
  `fromDatabase: {name, property: connectionString}`. `fromService` exposes only private
  `host`/`port`/`hostport` — **no public URL** — so `NEXT_PUBLIC_API_URL` and `FRONTEND_URL` are
  `sync: false` and entered by the owner (README explains the two-step).
- Versions: `PYTHON_VERSION` / `.python-version` (repo has `backend/.python-version` = 3.12);
  `NODE_VERSION` env var. "Render automatically adds uv to your Python service's runtime if your
  project's root directory includes a uv.lock file" → build `uv sync --frozen --no-dev`, start
  `uv run --frozen --no-dev uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
- Free tier: web services spin down after 15 minutes idle (~1 min to wake); free Postgres expires
  30 days after creation (14-day grace); one free DB per workspace. README notes both.
- `NEXT_PUBLIC_*` values are inlined at build time, so changing them needs a frontend redeploy.
- `autoDeployTrigger: checksPass` waits for GitHub checks (our CI) before deploying.

## R9. Frontend

- New shared `StatCard` (constitution building block) and `SegmentedControl` (period filter; also
  reused by 005's report period). Breakdown tables reuse `DataGrid`. `compareAmounts` sorts
  leakage columns exactly; the frontend does no arithmetic (all totals and percentages come from
  the API).
