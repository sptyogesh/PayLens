# Research: 001-paypal-sync

**Date**: 2026-11-10 · **Feature**: [spec.md](spec.md) · **Plan**: [plan.md](plan.md)

Docs were read on 2026-11-10 from developer.paypal.com. Labels used below:

- **DOCUMENTED**: PayPal states it directly (the source is quoted).
- **NOT DOCUMENTED**: PayPal's reference pages don't state it. We have a design decision instead,
  and a sandbox check task in `tasks.md` to confirm it with real data (Principle VIII).

One source could not be fetched: the Transaction Search integration guide,
<https://developer.paypal.com/docs/transaction-search/>. The fetch tool refused that domain page.
The API reference pages listed below were read in its place.

---

## R1. Is the Orders capture ID the same as the Transaction Search transaction ID?

**Finding: NOT DOCUMENTED.** No official page says the two IDs are the same.

- Capture ID: "The PayPal-generated ID for the captured payment"
  — <https://developer.paypal.com/api/payments/v2/captures-get>
- Transaction Search: "A valid transaction ID is 17 characters long, except for an order ID, which
  is 19 characters long." and "A transaction ID is not unique in the reporting system."
  — <https://developer.paypal.com/api/transaction-search/v1/search-get>
- Indirect evidence only: the sample capture IDs (`3C679366HH908993F`,
  `74L756601X447022Y`) are 17 characters, the length of a transaction ID.
  — <https://developer.paypal.com/docs/checkout/standard/integrate/>,
  <https://developer.paypal.com/api/payments/v2/captures-get>

**Decision**:
1. Record a `/pay` payment straight away, keyed by its **capture ID** as `paypal_transaction_id`.
   Also store `paypal_order_id` and set `origin = checkout_capture` (FR-033).
2. When sync reads a Transaction Search row, it upserts by `transaction_id`. If the IDs really are
   equal, this updates the `/pay` row and no duplicate is created.
3. **Fallback** in case they are not equal. Before inserting a new income row, sync looks for exactly
   one unreconciled `checkout_capture` row with:
   - the same gross, currency and payer email, and
   - a date within the reconcile window (constant `CHECKOUT_RECONCILE_WINDOW_HOURS = 72`).

   If it finds exactly one, it re-keys that row to the Transaction Search ID, sets
   `origin = transaction_search`, and counts it as "updated". If it finds zero or several, it inserts
   a new row, flags it, and logs it. It never merges blindly.
4. **Sandbox check task**: make a `/pay` payment, wait for Transaction Search (up to 3 h), and
   compare `transaction_id` with the stored capture ID. Record the result here. If the IDs match,
   the fallback stays as a safety net.

**Alternatives rejected**:
- Waiting for Transaction Search before showing `/pay` payments. That can take up to 3 hours, which
  fails SC-004.
- Matching only on amount and date. It is ambiguous when two clients pay the same amount.

---

## R2. Which event codes mean incoming customer payments (including "Send money")?

**Finding: the codes are DOCUMENTED. The mapping for "Send money" and Orders v2 is NOT DOCUMENTED.**

- "A T-code can be either credit (`CR`) or debit (`DR`), based on the direction of the payment
  (relative to the subject)."
  — <https://developer.paypal.com/docs/transaction-search/transaction-event-codes/>
  (page last updated October 13, 2026)
- Payment group (T00xx), as labelled on the same page:

  | Code | Label |
  |---|---|
  | T0000 | General payment |
  | T0001 | Mass payment |
  | T0002 | Subscription payment |
  | T0003 | Preapproved payment from a user for a recurring bill |
  | T0004 | eBay auction payment |
  | T0005 | Credit card payment |
  | T0006 | Express Checkout payment |
  | T0007 | Standard web checkout payment |
  | T0011 | Mobile payment |
  | T0012 | Virtual Terminal payment |
  | T0018 | PoS payment |
  | T0019 | Generic instrument funded payment |
  | T0023 | Business payment ("Payment between two business accounts") |

- No page maps "Send money" (personal-to-business transfer) or Orders API v2 checkout to a specific
  code. T0000 "General payment" is the closest generic code, but that is not confirmed.
- Excluded groups on the same page:
  - Refunds and reversals: T1100, T1106, T1107, T1110, T1120, T1201
  - Withdrawals: T0400–T0403
  - Currency conversion: T0200–T0202
  - Holds: T1500, T1501, T1503, T2101, T2105, T2107, plus releases T1105, T2102, T2106, T2108
  - Payment fee: T0107
- `transaction_status`:
  - "S": "successfully completed"
  - "P": "pending"
  - "D": "denied"
  - "V": "A successful transaction was reversed and funds were refunded to the original sender."

  — <https://developer.paypal.com/api/transaction-search/v1/search-get>

**Decision** (the constitution's Required Test P8 wins over spec FR-013, so the spec is updated):
- **Store every event** sync receives, with its `event_code` and a derived `kind`. Only
  `kind = income` counts as income. All other events are stored and excluded from income and
  leakage.
- A row is `income` when both of these are true:
  - its event code is in the constant `INCOME_EVENT_CODES` (the T00xx codes listed above), and
  - `transaction_amount.value` > 0 (money received, so CR).

  The same code with a negative amount (we sent the money) is `kind = outgoing_payment`.
- The other kinds are `refund` (T11xx and T1201), `withdrawal` (T04xx), `conversion` (T02xx),
  `hold` (T15xx and T21xx), `fee` (T0107) and `other`.
- Only status `S` and `P` rows can be income. A `D` or `V` row is stored with its status and
  excluded from income.
- **Sandbox check task**: make one "Send money" payment and one `/pay` payment from personal sandbox
  accounts, sync, and record the event codes seen here. If a code shows up that is not in
  `INCOME_EVENT_CODES`, it is stored as `other` and flagged in the sync summary. It is never
  silently counted as income.

**Alternatives rejected**:
- An allowlist of only T0000, T0006 and T0007. That could miss the real code used for Orders or
  "Send money".
- Using the amount sign alone. Refunds and conversions can also carry positive amounts.

---

## R3. The fee field and its sign

**Finding: the field is DOCUMENTED. Its sign is NOT DOCUMENTED.**

- Transaction Search: `transaction_info.fee_amount` `{currency_code, value}`.
  - "The PayPal fee amount. All transaction fees are included in this amount."
  - "This field contains a value only when a transaction fee is applied and processed for this
    transaction."
  - `transaction_amount` is "The all-inclusive gross transaction amount…".
  - The sample response uses placeholder strings, so it shows no signs.

  — <https://developer.paypal.com/api/transaction-search/v1/search-get> and
  <https://developer.paypal.com/api/transaction-search/v1/schema.yaml>
- Orders capture: `seller_receivable_breakdown.gross_amount`, `.paypal_fee` and `.net_amount`. The
  samples show positive values: `paypal_fee "3.98"`, `net_amount "96.02"`.
  — <https://developer.paypal.com/docs/checkout/standard/integrate/>,
  <https://developer.paypal.com/api/payments/v2/captures-get>
- The capture POST defaults to `return=minimal` ("A minimal response includes the id, status and
  HATEOAS links"). Getting the breakdown needs the header `Prefer: return=representation`.
  — <https://developer.paypal.com/api/orders/v2/orders-capture>

**Decision** (constitution Principle III: fees are normalised to positive on ingestion):
- `fee = abs(fee_amount.value)`. A missing `fee_amount` gives `fee = 0.00` with the transaction's
  currency (spec edge case).
- `gross = transaction_amount.value` for income rows, which is positive by the R2 rule.
- `net = gross − fee`, computed in code with `Decimal`.
- For captures, PayPal also returns `net_amount`. If it differs from our `gross − fee` by any amount,
  the row is flagged (FR-016) and stored as computed. It is never "fixed".
- Capture requests send `Prefer: return=representation`. If `seller_receivable_breakdown` is
  missing anyway, the row is stored with `fee = 0.00` and flagged. The next sync corrects it.
- Unit tests cover a negative fee, a positive fee and a missing fee (Required Test P7).
- **Sandbox check task**: record the real sign of `fee_amount` in one synced sandbox payment here.

---

## R4. Pagination fields and page size limits

**Finding: DOCUMENTED, with one inconsistency.**

- Request: `page` (default 1, range 1–2147483647) and `page_size` (default 100, **range 1–500**).
- `start_date` and `end_date` are required: "The maximum supported range is 31 days."
- Response: `page`, `total_items`, `total_pages`, `links`, `last_refreshed_datetime`.
- Inconsistency: `page` is described as "the zero-relative start index", but the docs' example says
  `page=1&page_size=20` returns "the first 20 items".
- No cap on the total number of results is stated.
- "It takes a maximum of three hours for executed transactions to appear in the list transactions
  call."
- `fields=all` returns all field groups (transaction_info, payer_info, shipping_info, auction_info,
  cart_info, incentive_info, store_info).
- `balance_affecting_records_only` defaults to `Y`.

— <https://developer.paypal.com/api/transaction-search/v1/search-get>

**Decision**:
- `page_size = 500` (constant `PAYPAL_PAGE_SIZE`). Start at `page = 1`, following the docs' example.
  Loop while `page < total_pages`.
- Set `fields=all` so `payer_info` comes back for client linking.
- Set `balance_affecting_records_only=N` so pending payments are included.
- Windows: `dates.split_windows(start, end, max_days=31)` produces back-to-back windows with no gap
  and no overlap (end of one window = start of the next). The boundary is in UTC.
- Safety stop: if `page` passes the constant `PAYPAL_MAX_PAGES_PER_WINDOW = 50`, the window stops,
  is flagged, and the run is reported as partial.
- Tests: respx returns 3 pages and we assert all 3 are requested (Required Test P2). A test also
  covers `total_pages = 0`.
- **Sandbox check task**: confirm that `page=1` returns the first page.

---

## R5. Duplicate transaction IDs within a sync

**Finding: DOCUMENTED.** "A transaction ID is not unique in the reporting system."
— <https://developer.paypal.com/api/transaction-search/v1/search-get>

**Decision**:
- Keep the constitution's unique constraint on `paypal_transaction_id`.
- Within one run, if two Transaction Search rows share an ID, keep the `income` row (or the first
  row when neither is income). Count the other as `flagged` and log its event code. The raw JSON is
  not logged (FR-052).

---

## R6. Payer fields for client linking

**Finding: DOCUMENTED.**
- `payer_info.email_address`
- `payer_info.payer_name` (`given_name`, `surname`, `full_name`, and others)
- `payer_info.country_code` (ISO 3166-1 alpha-2)
- `payer_info.account_id`

— <https://developer.paypal.com/api/transaction-search/v1/search-get> and
<https://developer.paypal.com/api/transaction-search/v1/schema.yaml>.

In the capture response, `payer.name` is an object with `given_name` and `surname`.
`payer.address.country_code` appears in the create-order example but not in the capture sample.
— <https://developer.paypal.com/api/orders/v2/schema.yaml>

**Decision**:
- Link clients by lower-cased `email_address`.
- Name: `full_name`, or else `given_name + surname`, or else the email.
- If the email is missing, link to the single "Unknown client" row.
- If the country is missing in a capture, store it as `null`. The next sync fills it from
  `payer_info.country_code`.
- The client's currency is set from the first payment.

---

## R7. Checkout front end: JS SDK and currency

**Finding: DOCUMENTED.**
- Recommended flow: "Your app creates an order on the back end…" and then "…Capture Payment for
  Order API endpoint on the back end." The capture runs in `onApprove`.
  — <https://developer.paypal.com/docs/checkout/standard/integrate/>
- Script parameters:
  - `client-id`: "Your PayPal REST client ID."
  - `currency`: "The currency for the transaction… Defaults to USD."

  — <https://developer.paypal.com/sdk/js/configuration/>
- The docs don't say whether currency can change without reloading the script.
- That page documents SDK v5 and recommends v6.
- `purchase_units[].description`: "any content beyond 127 characters (including spaces) will be
  truncated."
- `PayPal-Request-Id` header: "A unique ID identifying the request header for idempotency purposes."

  — <https://developer.paypal.com/api/orders/v2/orders-create>

**Decision**:
- Use the official `@paypal/react-paypal-js` package, which wraps the JS SDK script.
  - The page reloads the SDK script whenever the selected currency changes, keyed by currency.
  - It passes the public sandbox client ID only.
  - Version and SDK major version are pinned at setup. Pick whichever SDK major the package
    officially supports, and record it in the setup task.
- The backend sends a UUID `PayPal-Request-Id` on create and on capture. Retries reuse the same ID.
- The description limit of 127 characters is enforced in both the zod and Pydantic validation
  (FR-030).
- In test mode (`NEXT_PUBLIC_PAYPAL_MODE=fake`), the page renders a "Pay (test mode)" button that
  calls the same backend endpoints. The backend uses `FakePayPalGateway`. No PayPal script loads.

**Alternatives rejected**:
- Hand-loading `<script>` and managing the button lifecycle ourselves. That means more code and
  more edge cases (Principle X).

---

**Implementation note (2026-11-10, T056):** installed `@paypal/react-paypal-js` 10.6.1 (released
2026-10-23). Its default entry point is now **JS SDK v6** (`@paypal/react-paypal-js/sdk-v6`:
`PayPalProvider` + `PayPalOneTimePaymentButton`); the v5 `PayPalScriptProvider` API is kept as legacy.
PayLens uses **v6**, as PayPal recommends. In v6 the currency comes from the order the backend
creates, and the SDK environment is chosen by `environment="sandbox"` (not by the client ID), so
the SDK is loaded once and is **not** reloaded per currency. This replaces the "keyed by currency"
detail above. Source: the package README (`node_modules/@paypal/react-paypal-js/README.md`).

---

## R8. Rate limiting for `POST /sync` and the `/pay` endpoints (owner request)

**Decision**:
- A small in-memory **fixed-window limiter per client IP** in `app/common/rate_limit.py`, exposed as
  a FastAPI dependency. No new dependency is added.
- Limits are constants:

  | Endpoint | Limit |
  |---|---|
  | `POST /sync` | 3 requests / 60 s / IP |
  | `POST /pay/orders` | 10 / 60 s / IP |
  | `POST /pay/orders/{id}/capture` | 10 / 60 s / IP |

- Over the limit the response is `429`, with `Retry-After` and the standard error shape
  `RATE_LIMITED`.
- The client IP comes from the first `X-Forwarded-For` entry only when the setting
  `TRUST_PROXY_HEADERS=true` (set on Render). Otherwise it comes from the socket peer.
- This works because Render runs a single backend instance. With several instances the limits would
  apply per instance, which is acceptable for a sandbox demo.
- It is separate from the **one-sync-at-a-time lock** (R9).

**Alternatives rejected**:
- `slowapi`. It adds a dependency for about 40 lines of code (Principle X).
- A Redis-backed limiter. That adds infrastructure (Principle X).

---

## R9. One sync at a time

**Decision**:
- A PostgreSQL **session-level advisory lock**: `pg_try_advisory_lock(SYNC_LOCK_KEY)`, taken on a
  dedicated connection held for the length of the run and released in `finally`. PostgreSQL also
  releases it automatically if the connection drops.
- If the lock is not acquired, the response is `409 SYNC_IN_PROGRESS` (FR-020).
- This works across the startup sync, browser tabs and threads, with no extra table state.
- `sync_runs` rows record history. A run left `running` by a crash is shown as `failed` when it is
  older than the constant `SYNC_STALE_AFTER_MINUTES = 10`.

**Alternatives rejected**:
- An in-process `threading.Lock`. It doesn't cover a second worker process.
- A status-row check alone. It has race conditions.

---

## R10. Backend style: sync vs async; database schema management

**Decision**:
- **Synchronous** FastAPI endpoints, a synchronous SQLAlchemy 2 `Session` (psycopg 3 driver) and a
  synchronous `httpx.Client`. FastAPI runs sync endpoints in its threadpool.
  - It is simpler code for a 3-day build (Principles X and XIV).
  - `pytest-asyncio` is not needed for 001.
- The startup sync runs in a background thread from the FastAPI lifespan, so startup is never
  blocked (FR-021).
- Schema: `Base.metadata.create_all()` at startup, plus an idempotent seed script.
  - The `transactions` table is created with **all** Phase 1A columns now, including the
    leakage/FX/FIRA columns, which stay null. So 002–005 need no column changes.
  - Alembic is rejected for Phase 1A because it adds a dependency and migration files for a single
    schema version (Principle X). Revisit in Phase 1B.

---

## R11. Test database

**Finding**: this machine has no PostgreSQL or Docker installed. Advisory locks and `NUMERIC`
behaviour need real PostgreSQL. SQLite would hide real bugs.

**Decision**:
- Unit tests (mapper, windows, money, rate limiter, event classification) use **no database**.
- Repository, sync and API tests use PostgreSQL from `TEST_DATABASE_URL`. Each test runs in a
  transaction that is rolled back.
- If `TEST_DATABASE_URL` is unset, the DB tests **fail** with a clear message. They are not
  skipped (Principle V: never skip).
- CI uses a `postgres:18` service container.
- Local setup: install PostgreSQL 18 with the OS package manager. This is a prerequisite in
  `quickstart.md`.
- E2E runs the backend with `APP_ENV=test`, `PAYPAL_MODE=fake` and a separate `paylens_e2e`
  database, reset and seeded before the run.

---

## R12. Python and Node versions

**Finding**: this machine has Python 3.14 and Node 26.

**Decision**:
- Python: `requires-python = ">=3.11,<3.14"`. `uv` pins **3.12** through `.python-version`, which
  is broadly supported by the dependency set. Render's `PYTHON_VERSION` is set to the same.
- Node: `engines.node` matches the current Next.js LTS-supported range. `.nvmrc` pins the LTS
  major used in CI and on Render.
- Exact package versions are pinned in `uv.lock` and `package-lock.json` (Principle XVII).
