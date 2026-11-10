# HTTP API Contract: 001-paypal-sync

Rules for every endpoint:

- Base URL: `NEXT_PUBLIC_API_URL`.
- The FastAPI-generated OpenAPI schema is the machine source. `frontend/lib/api/api-types.ts` is
  generated from it, and this file is the reviewed contract it MUST match.
- **Money** is always `{"amount": "<decimal string, 2 dp>", "currency": "<ISO 4217>"}`. It is never
  a JSON number (FR-051).
- **Times** are ISO 8601 UTC with `Z`.
- **Errors** (constitution Coding Standards) all use this shape:

  ```json
  { "error": { "code": "STRING_CODE", "message": "Plain-language message" } }
  ```

  | HTTP | code | When |
  |---|---|---|
  | 400 | `INVALID_PERIOD` | `start > end`, or `end` in the future |
  | 404 | `NOT_FOUND` | Unknown order |
  | 409 | `SYNC_IN_PROGRESS` | Another sync holds the lock (FR-020) |
  | 422 | `VALIDATION_ERROR` | Body or query failed validation (Required Test A4) |
  | 429 | `RATE_LIMITED` | Over the limit. Includes a `Retry-After` header (research R8) |
  | 502 | `PAYPAL_UNAVAILABLE`, `PAYPAL_AUTH_FAILED`, `PAYPAL_REJECTED` | Upstream failure after retries |
  | 500 | `INTERNAL_ERROR` | Safe message, no stack trace (Required Test A5) |

- **CORS** allows only `FRONTEND_URL` and `http://localhost:3000` (FR-053, Required Test A6).

---

## `GET /health`

`200` → `{"status": "ok"}` (FR-007, Required Test A1).

---

## `POST /sync`

Rate limit: 3 per 60 s per IP. Runs synchronously and returns when the run ends (SC-003: under
30 s).

Request body (optional, all fields optional):

```json
{ "start": "2026-08-12T00:00:00Z", "end": "2026-11-10T12:00:00Z" }
```

Default is the last `SYNC_DEFAULT_DAYS` (90) days up to now (FR-022).

`200` → `SyncRun`. The outcome is `success`, `partial` or `failed`. A failed PayPal call is still a
recorded run, so it returns `200` with `outcome: failed` and `error`. The UI shows the run either
way.

```json
{
  "id": "uuid",
  "trigger": "manual",
  "period": { "start": "…Z", "end": "…Z" },
  "started_at": "…Z",
  "finished_at": "…Z",
  "outcome": "success",
  "windows": { "total": 3, "done": 3 },
  "counts": { "added": 10, "updated": 0, "skipped": 2, "flagged": 0 },
  "error": null,
  "hint": null
}
```

- `error`: `null`, or `{"code": "PAYPAL_UNAVAILABLE", "message": "…"}`.
- `hint`: set to the "new sandbox payments can take up to 3 hours to appear" text when
  `added + updated == 0` (spec edge case).

Other responses: `400 INVALID_PERIOD`, `409 SYNC_IN_PROGRESS`, `422`, `429`.

## `GET /sync/last`

`200` → `SyncRun`, or `null` if sync has never run. A stale `running` row is reported as
`failed` (research R9). Used for the startup-sync result (FR-021).

---

## `GET /transactions`

Query parameters:

| Param | Rules |
|---|---|
| `limit` | 1–200, default 100 |
| `offset` | ≥ 0, default 0 |
| `kind` | default `income`; `all` returns every kind |
| `source` | optional: `paypal_sandbox` or `demo_seed` |

`200`:

```json
{
  "items": [
    {
      "id": "uuid",
      "paypal_transaction_id": "3C679366HH908993F",
      "occurred_at": "2026-11-10T06:30:00Z",
      "client": { "id": "uuid", "name": "Acme Corp (sandbox)", "country": "US" },
      "kind": "income",
      "status": "completed",
      "gross": { "amount": "100.00", "currency": "USD" },
      "fee": { "amount": "3.98", "currency": "USD" },
      "net": { "amount": "96.02", "currency": "USD" },
      "source": "paypal_sandbox",
      "is_flagged": false
    }
  ],
  "total": 34,
  "limit": 100,
  "offset": 0
}
```

- Sorted newest first (FR-023).
- `source` is present on every row (Required Test A3, FR-050).
- `raw_json`, `flag_reason` and the internal `origin` are **not** exposed.
- The leakage fields are added by 002.

---

## `POST /pay/orders`

Rate limit: 10 per 60 s per IP. Creates a PayPal sandbox order on the server (FR-032).

Request:

```json
{ "amount": "50.00", "currency": "USD", "description": "Logo design (optional, ≤127 chars)" }
```

Validation (FR-031): `amount` is a string matching `^\d+(\.\d{1,2})?$`, with
`0 < amount ≤ CHECKOUT_MAX_AMOUNT`. `currency` is one of `USD`, `GBP`, `EUR` or `AUD`.

`201` → `{"order_id": "5O190127TN364715T"}`

Other responses: `422`, `429`, `502`.

## `POST /pay/orders/{order_id}/capture`

Rate limit: 10 per 60 s per IP. The server calls PayPal capture with
`Prefer: return=representation` and a `PayPal-Request-Id` header, then stores the payment at once
(FR-033).

`200`:

```json
{
  "transaction_id": "3C679366HH908993F",
  "order_id": "5O190127TN364715T",
  "status": "completed",
  "gross": { "amount": "50.00", "currency": "USD" },
  "recorded": true
}
```

- `status`: `completed` or `pending`.
- `recorded: false` means the PayPal capture succeeded but the database write failed. The UI still
  shows the confirmation, and the next sync records the payment (spec edge case).

Other responses:

- `422 PAYMENT_DECLINED`: the capture status is `DECLINED`, or the order was not approved. The UI
  shows "No payment was made".
- `404`, `429`, `502`.

---

## Frontend routes (UI contract)

| Route | Shows |
|---|---|
| `/` | Redirects to `/transactions` until 002 adds the dashboard |
| `/transactions` | Sync now button, last sync result, `DataGrid` of transactions (date IST, client, gross, fee, net, status, source `Badge`) and the demo-mode banner |
| `/pay` | Amount, currency select, description, PayPal button (or the test-mode button), sandbox notice, confirmation and error states |
