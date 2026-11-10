# HTTP API changes: 002-leakage-dashboard

All money is `{"amount": "<string, 2 dp>", "currency": "INR"}`. Rates are strings with 6 dp.
Percent is a string with 2 dp. Errors use `{"error": {"code", "message"}}`.

## GET /dashboard?period=this_month|last_3_months|all_time

Default `last_3_months`. Unknown value → 422 `VALIDATION_ERROR`.

```json
{
  "period": {"key": "last_3_months", "label": "Last 3 months",
             "start": "2026-08-31T18:30:00Z", "end": "2026-11-10T09:00:00Z"},
  "totals": {
    "payment_count": 18,
    "income_inr": {"amount": "1234567.50", "currency": "INR"},
    "fee_loss_inr": {...}, "fx_loss_inr": {...}, "total_leakage_inr": {...},
    "leakage_percent": "7.25"
  },
  "excluded_count": 1,
  "sources": ["demo_seed", "paypal_sandbox"],
  "paypal_rate_simulated": true,
  "simulated_spread_percent": "3.00",
  "by_month": [{"key": "2026-11", "label": "Nov 2026", "totals": {...}}],
  "by_client": [{"key": "<client uuid>", "label": "Ava Stone (demo)", "totals": {...}}]
}
```

- `totals` is `null` when the period has no calculated payments (`payment_count` 0) — the UI shows
  an empty state; `excluded_count` still reported.
- `leakage_percent` is `null` when income is 0.
- `by_month` newest first; `by_client` by `total_leakage_inr` desc, then label.
- Σ `by_month[].totals` = Σ `by_client[].totals` = `totals` (exact).
- `start`/`end` UTC with `Z`; `null` for `all_time`.

## GET /transactions (extended)

Each item gains:

```json
"leakage_status": "calculated" | "rate_unavailable" | "not_calculated" | "not_applicable",
"leakage": {
  "mid_market_rate": "84.000000",
  "paypal_rate": "81.480000",
  "paypal_rate_simulated": true,
  "ideal_inr": {"amount": "84000.00", "currency": "INR"},
  "inr_received": {...}, "fee_loss_inr": {...}, "fx_loss_inr": {...},
  "total_leakage_inr": {...},
  "leakage_percent": "7.25"
} | null
```

`leakage` is non-null only when `leakage_status = calculated`.

## Side effects

- `POST /sync`, `POST /pay/orders/{id}/capture`, startup sync, and `scripts.seed_demo` recalculate
  leakage before returning. FX failures never change their status code or body.
