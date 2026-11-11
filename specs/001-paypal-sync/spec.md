# Feature Specification: PayPal Sandbox Sync

**Feature Branch**: `001-paypal-sync`

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Feature 001-paypal-sync from docs/PayLens_Phase1A_Hackathon_Plan.md: connect to PayPal sandbox, fetch transactions with Transaction Search (31-day windows, pagination), store them idempotently in PostgreSQL with source labels, and add a /pay sandbox checkout page to create demo payments. Include project setup and foundational tasks (root tooling, Husky, test setup, shared common modules) as the setup phase."

## Scope (Phase 1A) *(mandatory)*

- **Phase 1A item**: M1 PayPal sandbox sync (first must-have). This feature also lays the project
  foundation that every later feature (002–005) builds on.
- **Phase 1A plan sections used**: 2 (scope, M1 done-when), 3 (no login, "Sync now" + on startup),
  6 (environment variables), 7 (data model: `clients`, `transactions`), 8 (PayPal sandbox APIs and
  setup), 9 (demo data plan and source labels), 12 (`/health`, `/sync`, `/transactions`),
  13 (Tuesday tasks), 18 (rules and safety), 19 (Transaction Search delay fallback).
- **Out of scope for this feature**:
  - Leakage calculations (fee loss, FX loss, total leakage), FX rates, dashboard cards, and the full
    transactions grid — feature 002-leakage-dashboard
  - Chat, FIRA, and CA report — features 003–005
  - Webhooks (optional in the plan; only if time remains after M1–M3)
  - Refunds, disputes, withdrawals, and payouts as income adjustments
  - Real-user login/OAuth, live PayPal credentials, other payment connectors, background job queues

## User Scenarios & Testing *(mandatory)*

The primary actor is the **freelancer** (the demo account owner, viewed by a judge). The secondary
actor is a **client** who pays the freelancer through the sandbox checkout. There is no login: the
app runs in a single, clearly labelled demo mode.

### User Story 0 - Project foundation is ready for feature work (Priority: P0, setup)

The owner and every AI coding tool can run the project locally, run all checks with one command,
and trust that automated hooks catch mistakes before code reaches the repository. Shared building
blocks for money, dates, errors, constants, and HTTP calls exist before any feature code uses them.

**Why this priority**: The constitution requires tooling, hooks, test setup, and shared modules
before feature 001 code. Without them nothing else can be verified or reused.

**Independent Test**: On a fresh clone, following the README sets up backend and frontend; the
single verification command runs lint, type checks, file-size checks, backend tests, frontend unit
tests, and one end-to-end smoke test, and all pass; the backend health check responds.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** a developer follows the README, **Then** backend and frontend
   start locally and the health check returns OK.
2. **Given** the project is set up, **When** the developer runs the single "check everything"
   command, **Then** lint, type checks, file-size checks, backend tests, frontend unit tests, and
   end-to-end tests all run and report pass/fail.
3. **Given** a staged file that breaks lint, formatting, file-size limits, or contains a secret,
   **When** an approved commit is attempted, **Then** the commit is blocked with a clear message.
4. **Given** a commit message that does not follow Conventional Commits, **When** the commit is
   attempted, **Then** it is rejected.
5. **Given** the app runs in test mode, **When** tests execute, **Then** no real PayPal or LLM
   service is contacted (fake adapters are used), and test mode cannot be enabled in production.
6. **Given** a required setting (such as the database URL) is missing, **When** the backend
   starts, **Then** it fails immediately with a message naming the missing setting.

---

### User Story 1 - Sync PayPal sandbox payments into PayLens (Priority: P1) 🎯 MVP

The freelancer presses **Sync now**. PayLens reads all incoming sandbox payments from PayPal for the
sync period, saves them, links each one to the paying client, and shows a summary: how many were
added, updated, and skipped. Synced transactions are listed with their source label
"PayPal sandbox". Running sync again never creates duplicates.

**Why this priority**: M1's done-when is "sandbox transactions appear in the database and UI". Every
later feature (dashboard, chat, FIRA matching) reads this data.

**Independent Test**: With sandbox payments present in the PayPal sandbox business account (or a
fake PayPal adapter in test mode), press Sync now; the summary and transaction list show exactly
those payments with correct amounts, fees, net, currency, date, client, and source label; pressing
Sync now again shows 0 added and the total count is unchanged.

**Acceptance Scenarios**:

1. **Given** the sandbox business account has 10 completed incoming payments in the sync period,
   **When** the freelancer presses Sync now, **Then** the summary shows 10 added and the list shows
   all 10 with gross, fee, net, currency, date, client name, and source "PayPal sandbox".
2. **Given** a sync has already stored those 10 payments, **When** Sync now is pressed again,
   **Then** the summary shows 0 added and the stored total is still 10.
3. **Given** the sync period is longer than 31 days, **When** sync runs, **Then** every part of the
   period is read (split into windows of at most 31 days) and no payment at a window boundary is
   missed or duplicated.
4. **Given** one window has more results than fit on one page, **When** sync runs, **Then** all
   pages are read and every payment is stored.
5. **Given** PayPal reports a fee as a negative value, **When** the payment is stored, **Then** the
   fee is stored as a positive amount and gross − fee = net.
6. **Given** a payment from a payer seen before (same payer email), **When** it is synced, **Then**
   it is linked to the existing client; a payer seen for the first time creates a new client with
   name, email, country, and currency from the payment.
7. **Given** PayPal returns non-payment events (withdrawals, currency conversions, holds, fee-only
   rows), **When** sync runs, **Then** they are stored with their kind, excluded from income, and
   counted as skipped.
8. **Given** PayPal is unreachable, rate-limits the request, or rejects the credentials, **When**
   sync runs, **Then** the freelancer sees a plain-language error, payments already stored are
   unchanged, and partial progress from completed windows is kept.
9. **Given** a sync is already running, **When** Sync now is pressed again, **Then** the second
   request is refused with a "sync already in progress" message instead of running twice.
10. **Given** the app starts, **When** startup completes, **Then** one sync runs automatically; if it
    fails, the app still starts and the error is visible as the last sync result.

---

### User Story 2 - Client pays through the sandbox checkout page (Priority: P2)

On the `/pay` page a client (using a PayPal sandbox personal account) enters an amount, picks a
currency (USD, GBP, EUR, or AUD), adds a short description, and pays the freelancer with the PayPal
checkout button. On success the page shows a confirmation with the PayPal transaction ID. The
payment appears in PayLens at once, labelled "PayPal sandbox", without waiting for Transaction
Search.

**Why this priority**: The demo plan needs 8–12 real sandbox payments made through PayLens to prove
the PayPal integration end to end. It is P2 because sync (P1) can already be shown with payments
made directly in the sandbox.

**Independent Test**: Open `/pay`, pay 50.00 USD with a sandbox personal account; a confirmation
with the transaction ID appears, and the payment is listed in PayLens with source "PayPal sandbox".
A later Sync now does not create a duplicate. In test mode the checkout is replaced by the fake
adapter.

**Acceptance Scenarios**:

1. **Given** the `/pay` page, **When** a client enters 50.00, picks USD, and completes checkout with
   a sandbox personal account, **Then** a confirmation shows the amount, currency, and PayPal
   transaction ID.
2. **Given** a payment was just completed on `/pay`, **When** the freelancer views the transaction
   list, **Then** the payment is already listed with gross, fee, net, currency, and source
   "PayPal sandbox".
3. **Given** a payment recorded from `/pay`, **When** Transaction Search later returns the same
   payment during sync, **Then** the existing record is updated, not duplicated.
4. **Given** an amount that is empty, zero, negative, has more than 2 decimals, or is above the
   allowed maximum, **When** the client tries to pay, **Then** the checkout button is not enabled
   and the problem is shown next to the field.
5. **Given** the client cancels or the payment fails at PayPal, **When** they return to `/pay`,
   **Then** a clear message says no payment was made and nothing is stored.
6. **Given** the `/pay` page, **When** it is shown, **Then** it states that it is a sandbox demo
   (no real money) and does not use the PayPal logo as PayLens branding.

---

### User Story 3 - Seeded demo history while sandbox data arrives (Priority: P3)

The owner loads 20–30 synthetic past transactions across several months and the four client
countries/currencies, labelled "Demo seed", so the product is meaningful even before Transaction
Search data appears. Seeded data can be reset without touching synced sandbox data.

**Why this priority**: Fallback from plan section 19 (Transaction Search delay) and part of the demo
data plan (section 9). Needed by 002 and 003, but not by M1's core proof.

**Independent Test**: Run the seed command on an empty database; 20–30 transactions labelled
"Demo seed" appear across at least 3 past months and 4 clients; running it again does not
duplicate them; sandbox-synced rows are untouched.

**Acceptance Scenarios**:

1. **Given** an empty database, **When** the seed command runs, **Then** 20–30 transactions with
   source "Demo seed" exist across at least 3 calendar months and 4 clients (USD, GBP, EUR, AUD).
2. **Given** seed data exists, **When** the seed command runs again, **Then** no duplicates are
   created.
3. **Given** both seeded and synced transactions exist, **When** the seed data is reset, **Then**
   only "Demo seed" rows are removed and "PayPal sandbox" rows remain.
4. **Given** the transaction list, **When** it shows both sources, **Then** every row visibly shows
   its source label.

---

### Edge Cases

- Sync period end is in the future or start is after end → rejected with a clear message.
- A payment exactly on a window boundary (e.g., 23:59:59 / 00:00:00 UTC) → stored exactly once.
- PayPal returns a payment that was stored earlier with different values (e.g., status changed from
  pending to completed) → the stored record is updated, not duplicated; source stays
  "PayPal sandbox".
- Pending or non-completed incoming payments → stored with their status but clearly not counted as
  completed income (later features count completed payments only).
- Payment with no fee information → fee recorded as 0.00 in the payment currency and the raw data
  kept for review.
- Payer with no email in the PayPal data → linked to an "Unknown client" record rather than dropped.
- Currency outside USD/GBP/EUR/AUD received in sandbox → stored as-is with its currency code.
- Access token expires mid-sync → refreshed once and the request retried; a second rejection stops
  sync with a credentials error.
- Rate limiting or server errors from PayPal → retried with increasing delay up to 3 times, then
  reported as a failure for that window.
- Transaction Search returns no data yet for new payments (known sandbox delay) → summary shows
  0 added with a hint that new sandbox payments can take time to appear.
- `/pay` checkout completes but recording the payment in PayLens fails → the client still sees the
  PayPal confirmation; the next sync records the payment.
- Two browser tabs press Sync now at the same moment → only one sync runs.

## Requirements *(mandatory)*

### Functional Requirements

**Project foundation (User Story 0 — becomes the Setup and Foundational task phases)**

- **FR-001**: The project MUST provide one shared command set from the repository root for lint,
  type checks, file-size checks, backend tests, frontend unit tests, end-to-end tests, "check" (all
  but E2E), and "check all" (everything), used identically by every developer and AI tool.
- **FR-002**: Automated git hooks MUST check staged files (lint/format, file size, secret scan) on
  commit, enforce Conventional Commit messages, and run type checks and fast tests on push. Hooks
  run only on owner-approved git actions and MUST NOT be bypassed.
- **FR-003**: The test setup MUST include backend tests with HTTP mocking, frontend unit tests with
  API mocking, and end-to-end tests that run the backend in test mode with fake PayPal and fake LLM
  adapters and seeded data. Fake adapters MUST be impossible to enable in production.
- **FR-004**: Shared backend building blocks MUST exist before feature code uses them: named
  constants, money type and rounding helpers (decimal, never floating point; always with a
  currency), currency codes and source enums, date/window helpers (UTC/IST), error types with
  user-friendly mapping, and one HTTP client with timeout and retry.
- **FR-005**: Shared frontend building blocks needed by this feature MUST exist before feature code
  uses them: money display (from string amounts, `en-IN` formatting), source badge, card, button,
  spinner, empty state, error state, sandbox/simulated disclaimer, an app shell, a typed API client
  with runtime validation, and generated API types.
- **FR-006**: The backend MUST load all settings through one typed settings object and fail at
  startup with a clear message if a required setting is missing. Only example settings files with
  empty values are committed.
- **FR-007**: The backend MUST expose a health check that reports OK when the service is running.
- **FR-008**: The repository MUST include agent rule files that point to the constitution
  (`AGENTS.md`, `CLAUDE.md`, Cursor rule), a `CHANGELOG.md` in Keep a Changelog format, recommended
  editor settings/extensions, a CI workflow running the full check set, and a README with local
  setup and sandbox setup steps.

**PayPal sandbox sync (User Story 1)**

- **FR-010**: The system MUST connect to PayPal **sandbox only**, using credentials from settings;
  the PayPal base URL MUST come from settings.
- **FR-011**: The system MUST reuse a PayPal access token until shortly before it expires instead
  of requesting one per call, and refresh it once on a rejected-token response.
- **FR-012**: Sync MUST read transactions for the sync period by splitting it into consecutive
  windows of at most 31 days and reading every page of every window.
- **FR-013**: Sync MUST store every event it reads, classified by kind. Only completed and pending
  **incoming customer payments** count as income; other events (withdrawals, refunds, conversions,
  holds, fees, outgoing payments) MUST be stored but excluded from income and counted as skipped
  (constitution Required Test P8).
- **FR-014**: Each stored transaction MUST include: PayPal transaction ID (unique), client link,
  date/time, gross amount, fee amount (positive), net amount, currency code, status, source
  `paypal_sandbox`, and the raw PayPal record for debugging. Amounts keep 2 decimal places.
- **FR-015**: Storage MUST be idempotent: the PayPal transaction ID is unique, and re-syncing
  updates an existing record instead of inserting a duplicate.
- **FR-016**: Fee values reported as negative by PayPal MUST be stored as positive amounts, and the
  stored record MUST satisfy gross − fee = net; a record that does not MUST be flagged in the sync
  summary and logs, not silently corrected.
- **FR-017**: Sync MUST link each payment to a client by payer email, creating the client (name,
  email, country, currency) the first time a payer is seen.
- **FR-018**: On rate-limit or server errors, the system MUST retry with increasing delays up to 3
  times; after that, sync MUST stop, keep stored progress from completed windows, and report a
  plain-language error.
- **FR-019**: The freelancer MUST be able to start a sync with a **Sync now** action and see the
  result: added, updated, skipped, flagged, period covered, finished time, and success or error.
- **FR-020**: Only one sync MAY run at a time; a second request while one is running MUST be
  refused with a clear message.
- **FR-021**: One sync MUST run automatically at backend startup; a failure MUST NOT stop the app
  from starting and MUST be visible as the last sync result.
- **FR-022**: The default sync period MUST be the last 90 days up to now, set by a named constant.
- **FR-023**: The freelancer MUST be able to see the list of stored transactions (date, client,
  gross, fee, net, currency, status, source label), newest first. This basic list is the base the
  002 dashboard grid extends.

**Sandbox checkout `/pay` (User Story 2)**

- **FR-030**: The `/pay` page MUST let a client enter an amount, choose USD, GBP, EUR, or AUD, add an
  optional description (up to 127 characters), and pay the freelancer's sandbox business account
  via the PayPal checkout button.
- **FR-031**: The amount MUST be validated before checkout: required, greater than 0, at most 2
  decimal places, and no more than a maximum set by a named constant.
- **FR-032**: Creating and capturing the order MUST happen through the PayLens backend; secret
  credentials MUST never reach the browser (only the public sandbox client ID).
- **FR-033**: After a successful capture the system MUST immediately store the payment as a
  `paypal_sandbox` transaction using the capture result (gross, fee, net, currency, payer), keyed by
  the same PayPal transaction ID that Transaction Search later returns, so a later sync updates it.
- **FR-034**: The page MUST show a confirmation (amount, currency, PayPal transaction ID) on success,
  and a clear "no payment was made" message on cancel or failure.
- **FR-035**: The page MUST state that it is a sandbox demo with no real money, and MUST NOT use the
  PayPal logo as PayLens branding or imply PayPal endorsement (the standard PayPal checkout button is
  allowed).

**Demo seed data (User Story 3)**

- **FR-040**: A seed command MUST create 20–30 synthetic transactions labelled `demo_seed`, spread
  over at least 3 past months, across 4 clients (US/USD, UK/GBP, Germany/EUR, Australia/AUD), with
  realistic gross, fee, and net values.
- **FR-041**: The seed command MUST be idempotent and MUST have a reset option that removes only
  `demo_seed` rows.
- **FR-042**: Seeded data MUST use clearly fictional client names and emails; no real person's data.

**Cross-cutting**

- **FR-050**: Every transaction shown in the UI MUST display its source label ("PayPal sandbox" or
  "Demo seed"), and the app MUST show that it is running in demo mode on sandbox data.
- **FR-051**: Money MUST cross the API as strings with a currency code, never as JSON numbers; the
  frontend MUST NOT do money arithmetic.
- **FR-052**: Logs MUST NOT contain secrets, access tokens, or full raw PayPal records.
- **FR-053**: Cross-origin access MUST be allowed only from the deployed frontend URL and localhost.

*Constitution rules covered here:* Principle II (no LLM in this feature; every number is stored or
computed by tested code), Principle III (decimal money, currency always attached, positive fees),
Principle VI (sandbox only, secrets in settings, CORS), Principle VII (source labels, demo mode),
Principle VIII (token cache, 31-day windows, pagination, idempotent upsert, retries, raw record).

### Key Entities *(include if feature involves data)*

- **Client**: A person or company that pays the freelancer. Name, email (unique when present),
  country, default currency. One client has many transactions.
- **Transaction**: One incoming payment. PayPal transaction ID (unique), client, date/time, gross,
  fee, net, currency, status, source (`paypal_sandbox` or `demo_seed`), raw PayPal record. Holds
  empty leakage/FX/FIRA fields that features 002 and 004 fill in (`mid_market_rate`, `paypal_rate`,
  `inr_received`, `fee_loss_inr`, `fx_loss_inr`, `total_leakage_inr`, `fira_status`).
- **Sync Run**: One sync attempt. Start/finish time, period covered, trigger (manual or startup),
  counts (added, updated, skipped, flagged), outcome (success, partial, failed) and error message.
  Used to show the last sync result and to enforce one sync at a time.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of completed incoming sandbox payments in the sync period appear in PayLens after
  one Sync now, with gross, fee, net, and currency matching PayPal to the cent.
- **SC-002**: Running Sync now 3 times in a row leaves the transaction count unchanged after the
  first run (0 duplicates).
- **SC-003**: For a sandbox account with up to 100 payments across 90 days, a sync completes in
  under 30 seconds.
- **SC-004**: A client completes a `/pay` sandbox payment in under 1 minute, and the payment is
  visible in PayLens within 5 seconds of the confirmation.
- **SC-005**: 100% of transactions shown in the UI display a source label.
- **SC-006**: For every stored transaction, gross − fee = net exactly.
- **SC-007**: When PayPal is unavailable, the freelancer sees a plain-language error within
  60 seconds and no stored data is lost or changed.
- **SC-008**: A new developer gets the project running locally from the README alone in under
  30 minutes, and the full check set passes on a clean checkout.
- **SC-009**: Zero automated tests contact real PayPal or a real LLM.

## Assumptions

- The PayPal sandbox business account (freelancer), 3–4 personal accounts (clients in US/USD,
  UK/GBP, Germany/EUR, Australia/AUD), and a sandbox REST app with Transaction Search enabled are set
  up manually by the owner (plan section 8); credentials are supplied through settings.
- Transaction Search data can take hours to appear in sandbox; recording `/pay` payments from the
  capture result (FR-033) and seeded data (User Story 3) cover the gap.
- The PayPal capture ID equals the transaction ID that Transaction Search returns for the same
  payment; this MUST be verified against current PayPal documentation during planning (Principle
  VIII). If it does not hold, `/pay` payments are matched on another stable identifier.
- "Incoming customer payment" event codes and the field holding fees are taken from current PayPal
  Transaction Search documentation during planning.
- There is no login. `Sync now`, the seed command, and `/pay` are reachable by anyone with the demo
  URL; this is acceptable for a sandbox-only demo with no real money.
- 90 days is enough history for the demo; seeded data provides older months.
- Refunds, reversals, and disputes are not handled in Phase 1A.
- Leakage, FX rates, and the dashboard grid are built in 002; this feature only stores the fields
  they need.
- Setup tooling and structure follow the constitution's Technology Stack, Code Structure, and
  Principle XVII lists; they are not re-decided here.
