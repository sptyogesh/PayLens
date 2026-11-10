# Data Model: 002-leakage-dashboard

## New table: `fx_rates`

| Column | Type | Rules |
|---|---|---|
| id | UUID PK | |
| currency | CHAR(3) | ISO 4217, base currency (USD, GBP, EUR, AUD, …) |
| rate_date | DATE | Payment's IST calendar date requested |
| published_date | DATE | Date the source actually published (≤ rate_date; weekends fall back) |
| rate | NUMERIC(14,6) | Mid-market INR per 1 unit of `currency`; > 0 |
| source | VARCHAR(32) | `frankfurter_ecb` or `fake` |
| fetched_at | TIMESTAMPTZ | UTC |
| created_at / updated_at | TIMESTAMPTZ | mixin |

Constraints: `UNIQUE(currency, rate_date)`, `CHECK(rate > 0)`, `CHECK(published_date <= rate_date)`.

## Existing table `transactions` — leakage columns (created empty in 001)

| Column | Filled with |
|---|---|
| mid_market_rate NUMERIC(14,6) | `r_mid` from `fx_rates` (1.000000 for INR) |
| paypal_rate NUMERIC(14,6) | `round6(r_mid × (1 − SIMULATED_FX_SPREAD))` — simulated |
| inr_received NUMERIC(14,2) | `round2(N × r_pp)` |
| fee_loss_inr NUMERIC(14,2) | `round2(F × r_mid)` |
| fx_loss_inr NUMERIC(14,2) | `round2(N × (r_mid − r_pp))`, may be negative (gain) |
| total_leakage_inr NUMERIC(14,2) | `fee_loss_inr + fx_loss_inr` |

Derived at read time (engine, not stored): `ideal_inr = round2(G × r_mid)`,
`leakage_percent = round2(total / (G × r_mid) × 100)`.

**Eligibility**: `kind = income AND status = completed`. Non-eligible rows have all six columns
NULL (recalculation clears them).

**Leakage status** (derived, API only):

| Status | When |
|---|---|
| `calculated` | eligible, all six columns set |
| `rate_unavailable` | eligible, no rate yet (FX source missing/unreachable) |
| `not_calculated` | eligible but invalid amounts (fee > gross) — engine rejects |
| `not_applicable` | not eligible (non-income, pending, denied, reversed) |

## Engine types (`engine/leakage/types.py`, Pydantic, frozen)

- `LeakageInput`: gross, fee, net (Decimal, floats rejected), currency, mid_rate (Decimal | None),
  paypal_rate (Decimal | None). Validation: gross ≥ 0, fee ≥ 0, fee ≤ gross (L5, L6).
- `LeakageResult`: ideal_inr, inr_received, fee_loss_inr, fx_loss_inr, total_leakage_inr,
  leakage_percent (Decimal), `is_gain` (fx_loss < 0).
- `RateUnavailable`: marker result (L7).
- `LeakageRow` (aggregate input): month key, client id, client name, gross, mid_rate, the stored
  INR values.
- `LeakageTotals`: payment_count, income_inr, fee_loss_inr, fx_loss_inr, total_leakage_inr,
  leakage_percent (None when income is 0).

## Dashboard periods

| Key | Label | Start (IST) | End |
|---|---|---|---|
| `this_month` | This month | 1st of current IST month 00:00 | now |
| `last_3_months` | Last 3 months (default) | 1st of IST month two months back | now |
| `all_time` | All time | none | none |
