# Contracts: 004-fira-matching

## POST /fira/upload?file_name=<name.pdf>  (one file per request; rate limit RATE_LIMIT_FIRA)
Body: the raw PDF bytes, `Content-Type: application/pdf` (no multipart: `python-multipart` is not
installed and installing it is not approved). The page uploads up to FIRA_MAX_FILES files one after another.
200:
```json
{"result": {"file_name": "fira-SEED-0001.pdf", "outcome": "stored" | "duplicate" | "rejected" | "failed",
   "message": "…", "fira_id": "uuid" | null, "status": "matched" | "needs_review" | "no_match" | null},
 "summary": {"matched": 19, "needs_review": 2, "no_match": 0, "missing_payments": 3}}
```
`rejected` = not a PDF / too large / empty (no AI call; the body is read only up to the limit + 1 byte);
`failed` = AI unavailable or output not JSON (E4) — nothing stored. Per-file problems are 200 with an
outcome; 422 only for a missing/invalid `file_name`.

## GET /fira
```json
{"summary": {...same...},
 "items": [{"id": "…", "file_name": "…", "status": "needs_review", "score": 75, "reason": "Amount differs by more than 1%",
   "foreign_amount": {"amount": "1030.00", "currency": "USD"}, "inr_amount": {"amount": "…", "currency": "INR"} | null,
   "remittance_date": "2026-10-05", "reference_no": "SEED-0020", "purpose_code": "P0802",
   "matches": [{"transaction_id": "…", "paypal_transaction_id": "SEED-0020", "score": 75, "kind": "direct"}]}],
 "missing": [{"transaction_id": "…", "paypal_transaction_id": "SEED-0022", "date": "2026-…", "client": "…", "gross": {...}}]}
```

## GET /transactions — each item gains `fira_status`: "matched" | "needs_review" | "missing" | null.

## Chat tool `fira_status` (input: period like other tools) → content {period, matched_count,
needs_review_count, missing_count, missing: [{date, client, gross, paypal_transaction_id}], needs_review: [...], has_data}.
