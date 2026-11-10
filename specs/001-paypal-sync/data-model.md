# Data Model: 001-paypal-sync

**Source**: Phase 1A plan section 7, spec Key Entities, research R1–R6, R9.

Common rules for every table:

- Money is `NUMERIC(14,2)`. Rates are `NUMERIC(14,6)`. Every amount has a `currency` column next to
  it (Principle III).
- Timestamps are `TIMESTAMPTZ` stored in UTC.
- Primary keys are `UUID` (generated in code).
- Every table is created by `Base.metadata.create_all()` (research R10).

## Enums (`app/common/types.py`)

| Enum | Values |
|---|---|
| `CurrencyCode` | ISO 4217 codes. Checkout allows `USD`, `GBP`, `EUR`, `AUD` (constant `CHECKOUT_CURRENCIES`). Sync accepts any valid 3-letter code. |
| `TransactionSource` | `paypal_sandbox`, `demo_seed` |
| `TransactionOrigin` | `transaction_search`, `checkout_capture`, `seed` |
| `TransactionKind` | `income`, `outgoing_payment`, `refund`, `withdrawal`, `conversion`, `hold`, `fee`, `other` |
| `TransactionStatus` | `completed` (S), `pending` (P), `denied` (D), `reversed` (V) |
| `SyncTrigger` | `manual`, `startup` |
| `SyncOutcome` | `running`, `success`, `partial`, `failed` |
| `FiraStatus` | `matched`, `needs_review`, `missing` (the column exists now; feature 004 fills it) |

## `clients`

| Column | Type | Rules |
|---|---|---|
| `id` | UUID PK | |
| `name` | VARCHAR(200) NOT NULL | From `full_name`, else `given_name + surname`, else the email (R6) |
| `email` | VARCHAR(254) NULL, **UNIQUE** | Stored lower-cased. Null only for the single "Unknown client" row |
| `country` | CHAR(2) NULL | ISO 3166-1 alpha-2 |
| `currency` | CHAR(3) NOT NULL | Set from the client's first payment |
| `is_unknown` | BOOLEAN NOT NULL DEFAULT false | Exactly one row is true (partial unique index) |
| `source` | `TransactionSource` NOT NULL | `demo_seed` for seeded clients, so a reset can remove them |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

Relationship: one client has many transactions.

## `transactions`

| Column | Type | Rules |
|---|---|---|
| `id` | UUID PK | |
| `paypal_transaction_id` | VARCHAR(32) NOT NULL **UNIQUE** | Upsert key (Principle VIII). Seed rows use the `SEED-NNNN` format |
| `paypal_order_id` | VARCHAR(32) NULL | Set for `/pay` payments (R1) |
| `client_id` | UUID FK → clients.id NOT NULL | |
| `occurred_at` | TIMESTAMPTZ NOT NULL | PayPal `transaction_initiation_date`, or the capture `create_time` |
| `event_code` | VARCHAR(8) NULL | e.g. `T0006`. Null for checkout and seed rows until sync fills it |
| `kind` | `TransactionKind` NOT NULL | Derived as in R2. Only `income` counts as income |
| `status` | `TransactionStatus` NOT NULL | |
| `gross_amount` | NUMERIC(14,2) NOT NULL | > 0 for income |
| `fee_amount` | NUMERIC(14,2) NOT NULL | Always ≥ 0. `abs()` is applied on ingestion (R3) |
| `net_amount` | NUMERIC(14,2) NOT NULL | CHECK `net_amount = gross_amount - fee_amount` |
| `currency` | CHAR(3) NOT NULL | Shared by gross, fee and net |
| `source` | `TransactionSource` NOT NULL | |
| `origin` | `TransactionOrigin` NOT NULL | |
| `is_flagged` | BOOLEAN NOT NULL DEFAULT false | Data-quality flag (FR-016, R1, R2, R5) |
| `flag_reason` | VARCHAR(200) NULL | Short code plus text. Never contains raw PayPal JSON |
| `raw_json` | JSONB NULL | The raw PayPal record (Principle VIII). Never returned by the API and never logged |
| `mid_market_rate`, `paypal_rate` | NUMERIC(14,6) NULL | Filled by 002 |
| `inr_received`, `fee_loss_inr`, `fx_loss_inr`, `total_leakage_inr` | NUMERIC(14,2) NULL | Filled by 002 |
| `fira_status` | `FiraStatus` NULL | Filled by 004 |
| `created_at`, `updated_at` | TIMESTAMPTZ | |

Indexes: `occurred_at DESC` (for the list), `client_id`, `source`, `kind`.

**Validation (Pydantic in the mapper and checkout service, plus DB CHECK constraints)**:

- `fee_amount >= 0`
- `gross_amount >= 0`
- `net_amount = gross_amount - fee_amount`
- `currency` matches `^[A-Z]{3}$`

**Upsert rule (sync)**:

1. Match by `paypal_transaction_id`. On a match, update every PayPal-derived column (`event_code`,
   `kind`, `status`, the amounts, `raw_json`, client link). Keep `source = paypal_sandbox`. Set
   `origin = transaction_search`. Never touch the 002/004 columns.
2. If there is no match and the row is income, run the R1 reconcile fallback against unreconciled
   `checkout_capture` rows.
3. Otherwise insert a new row.

The counters are `added`, `updated`, `skipped` and `flagged`. `skipped` means non-income rows that
were stored (`kind ≠ income`). It is reported separately so the summary matches spec acceptance
scenario 7.

**State transitions (`status`)**: `pending → completed`, `completed → reversed` and
`pending → denied`, each driven by later syncs. `origin`: `checkout_capture → transaction_search`
(on reconcile or ID match).

## `sync_runs`

| Column | Type | Rules |
|---|---|---|
| `id` | UUID PK | |
| `trigger` | `SyncTrigger` NOT NULL | |
| `period_start`, `period_end` | TIMESTAMPTZ NOT NULL | Default period is the last 90 days (`SYNC_DEFAULT_DAYS`) |
| `started_at` | TIMESTAMPTZ NOT NULL | |
| `finished_at` | TIMESTAMPTZ NULL | |
| `outcome` | `SyncOutcome` NOT NULL | `running`, then `success`, `partial` (some windows done) or `failed` |
| `windows_total`, `windows_done` | INT NOT NULL | |
| `added`, `updated`, `skipped`, `flagged` | INT NOT NULL DEFAULT 0 | |
| `error_code` | VARCHAR(50) NULL | e.g. `PAYPAL_UNAVAILABLE`, `PAYPAL_AUTH_FAILED`, `PAYPAL_RATE_LIMITED` |
| `error_message` | VARCHAR(500) NULL | Safe, plain-language text |

A `running` row older than `SYNC_STALE_AFTER_MINUTES` is shown as `failed` (R9). The one-run-at-a-
time rule is enforced by the advisory lock, not by this table.

**Commit granularity**: each 31-day window commits on its own. A failure in window k keeps windows
1…k−1 (FR-018, Required Test P6: "no partial corrupt data" holds because a failed window rolls back
in full).

## Seed data (`backend/scripts/seed_demo.py`)

- 4 clients with clearly fictional names and `example.com` emails:
  - US/USD
  - UK/GBP
  - DE/EUR
  - AU/AUD
- 24 transactions with `source = demo_seed`, `origin = seed`, `kind = income`,
  `status = completed`, spread over the 4 months before the current month.
  - The values are fixed in `backend/scripts/seed_data.py`, so they are deterministic.
  - Fees follow a fixed percentage plus a fixed amount per currency (constants).
- It is idempotent: an upsert by `SEED-NNNN`.
- `--reset` deletes only rows with `source = demo_seed` (transactions first, then seed clients that
  have no remaining transactions).

## Not in this feature

`fira_documents`, `fira_matches` and `chat_messages` are created by features 003–004.
