# Contracts: 005-ca-report

## GET /report.pdf?period=this_month|last_3_months|all_time   (rate limit RATE_LIMIT_REPORT = 10/60 s)
- 200 `application/pdf`, `Content-Disposition: attachment; filename="paylens-ca-report-<period>-<YYYY-MM-DD>.pdf"`.
- 422 standard error for an unknown period. AI failure never changes the status (fallback summary).

## GET /report/data?period=...   (same rate limit)
The exact data the PDF is built from (all money strings with currency, counts, percents):
```json
{
  "period": {"key": "last_3_months", "label": "Last 3 months", "start": "…Z" | null, "end": "…Z" | null},
  "generated_at": "…Z",
  "totals": DashboardTotals | null,              // same object as GET /dashboard totals
  "gross_by_currency": [{"amount": "7080.00", "currency": "USD"}],
  "by_month": [BreakdownRow], "by_client": [BreakdownRow],     // as GET /dashboard
  "excluded_count": 0, "not_calculated_count": 0,
  "fira": {"matched": 19, "needs_review": 2, "missing": 3,
           "missing_payments": [{"date": "2026-07-18", "client": "…", "paypal_transaction_id": "SEED-0022", "gross": Money}]},
  "summary": {"text": "…", "source": "ai" | "code"},
  "notes": ["Sandbox data …", "Simulated (sandbox) PayPal rate …", "ECB reference rates …", "Demo seed rows …"],
  "disclaimer": "Prepared from user data — not tax advice. Confirm with a CA."
}
```
FIRA counts are for eligible payments in the period. Everything except `summary.text` (when source
"ai") is computed by code; the AI summary is grounded against these numbers (003 grounding rules).

## Frontend
"Download CA report" button on the dashboard next to the period filter; downloads
`/report.pdf?period=<current dashboard period>` with fetch → Blob → object URL → `<a download>`;
shows "Preparing report…" while pending and an error message with retry on failure (timeout 60 s).
