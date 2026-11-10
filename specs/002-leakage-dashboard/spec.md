# Feature Specification: Leakage Dashboard

**Feature Branch**: `001-paypal-sync` (owner decision 2026-11-10: 002 is built on the current branch; no new branch)

**Created**: 2026-11-10

**Status**: Draft

**Input**: User description: "Feature 002-leakage-dashboard (M2). Per-transaction fee loss, FX loss, total leakage and leakage % in INR using the formulas in Phase 1A plan section 10. Mid-market rates from a free FX API that supports INR, cached in an fx_rates table and mocked in tests. Simulated PayPal rate = mid-market minus a spread stored as a named constant, labelled "Simulated (sandbox)" wherever it shows. "Rate unavailable" is shown without inventing numbers. Recalculate after sync, seed and /pay. Dashboard: summary cards (total income INR, fee loss, FX loss, total leakage, leakage %), period filter (this month, last 3 months, all time), breakdown by month and by client, leakage columns in the transactions grid. Polish phase: create render.yaml (backend web service, frontend web service, PostgreSQL 18), add deployment steps and every required environment variable to README."

## Scope (Phase 1A) *(mandatory)*

- **Phase 1A item**: M2 leakage dashboard (second must-have).
- **Phase 1A plan sections used**: 2 (M2 done-when), 4 (free FX API with INR support), 7 (leakage
  columns on `transactions`), 9 (FX note: simulated PayPal rate, "Simulated (sandbox)" label),
  10 (leakage formulas), 12 (`GET /dashboard`, `GET /transactions`), 14 (Render deployment),
  15 (README checklist: setup, env vars, sandbox and simulated notes), 18 (honest labels).
- **Out of scope for this feature**:
  - Chat, FIRA, CA report (features 003–005)
  - Real PayPal conversion rates (sandbox does not provide INR conversion; the rate is simulated)
  - Leakage for refunds, withdrawals, conversions, holds and other non-income events
  - Charts beyond simple tables/cards, CSV export, custom date pickers
  - Login, live credentials, background job queues

## User Scenarios & Testing *(mandatory)*

The actor is the **freelancer** (demo account owner, viewed by a judge). There is no login.

### User Story 1 - See what each payment lost (Priority: P1) 🎯 MVP

For every income payment the freelancer sees, in INR: what they would have received at the
mid-market rate, what they actually received at the (simulated) PayPal rate, the fee loss, the FX
loss, the total leakage and the leakage %. The values are calculated automatically after every
sync, demo seed and `/pay` payment. When no exchange rate is available for a payment, the row says
"Rate unavailable" instead of showing numbers.

**Why this priority**: Per-payment leakage is the core insight of PayLens and the input for every
total, card and chat answer that follows.

**Independent Test**: Seed demo data (rates served by a fake FX source), open the transactions
page, and check that every income row shows leakage columns whose values match the section 10
formulas, that the PayPal rate is labelled "Simulated (sandbox)", and that sorting by total
leakage works.

**Acceptance Scenarios**:

1. **Given** a payment of 1000.00 USD with fee 44.00, mid-market 84.000000 and PayPal rate
   81.500000, **When** leakage is calculated, **Then** ideal INR is ₹84,000.00, INR received is
   ₹77,914.00, fee loss ₹3,696.00, FX loss ₹2,390.00, total leakage ₹6,086.00 and leakage % is
   7.25%.
2. **Given** new payments arrive through Sync now, the demo seed or `/pay`, **When** that action
   finishes, **Then** those payments show calculated leakage without any other user action.
3. **Given** the FX source has no rate for a payment's currency and date, **When** leakage is
   calculated, **Then** that row shows "Rate unavailable", no INR numbers, and is retried on the
   next calculation.
4. **Given** the transactions grid, **When** the user sorts by total leakage, **Then** rows are
   ordered by the exact INR value (rows without a rate last).
5. **Given** any row with a PayPal rate, **When** it is displayed, **Then** "Simulated (sandbox)"
   is visible next to that rate (column header or cell).

---

### User Story 2 - Leakage summary for a period (Priority: P1)

On the dashboard (home page) the freelancer sees five summary cards for the chosen period: total
income (INR, at the mid-market rate), fee loss, FX loss, total leakage and leakage %. A period
filter offers "This month", "Last 3 months" and "All time" (default: Last 3 months).

**Why this priority**: The cards answer "how much am I losing?" at a glance; they are the M2
done-when.

**Independent Test**: Seed demo data, open the dashboard, switch the period filter and check the
card values equal the sums of the matching rows from the transactions API.

**Acceptance Scenarios**:

1. **Given** seeded data, **When** the dashboard opens, **Then** five cards show ₹ values for
   "Last 3 months" and the period is named on screen.
2. **Given** the period filter, **When** the user picks "This month" or "All time", **Then** the
   cards update to that period's totals.
3. **Given** a period with no income payments, **When** the dashboard loads, **Then** an empty
   state says there are no payments in this period (no ₹0.00 cards pretending to be data).
4. **Given** some payments in the period have no rate, **When** the cards show, **Then** a note
   says how many payments are not included because their rate is unavailable.
5. **Given** the FX loss total is negative (PayPal rate better than mid-market), **When** shown,
   **Then** it is labelled as an FX gain, not hidden or shown as zero.

---

### User Story 3 - Where the leakage comes from (Priority: P2)

Under the cards, the dashboard shows two breakdown tables for the same period: by month and by
client. Each row shows payment count, income (INR), fee loss, FX loss, total leakage and leakage %.

**Why this priority**: Shows which months and clients cost the most; useful but secondary to the
totals.

**Independent Test**: Seed demo data, open the dashboard, and check the month and client rows sum
to the card totals.

**Acceptance Scenarios**:

1. **Given** seeded data over 4 months, **When** "All time" is selected, **Then** the month table
   lists each month (newest first) and its rows sum to the card totals.
2. **Given** 4 clients, **When** the client table shows, **Then** each client has one row, sorted
   by total leakage (highest first), and the rows sum to the card totals.

---

### User Story 4 - Deployable on Render (Priority: P2, polish)

The owner can deploy backend, frontend and PostgreSQL 18 on Render from a blueprint file in the
repository, following README steps that list every environment variable.

**Why this priority**: The constitution requires a first deployment by Wednesday 11 Nov.

**Independent Test**: The blueprint file validates against the Render schema fields used; README
lists every variable read by backend and frontend settings; the owner deploys and opens the live
URL.

**Acceptance Scenarios**:

1. **Given** the repository, **When** the owner creates a Render Blueprint from it, **Then** a
   PostgreSQL 18 database, a backend web service and a frontend web service are created with the
   right root directories, build and start commands, and health check.
2. **Given** the README, **When** the owner reads the deployment section, **Then** every required
   environment variable is listed with where its value comes from, and secrets are marked as
   "set in Render, never committed".

### Edge Cases

- FX source down or slow: leakage is not calculated for affected rows ("Rate unavailable"); sync,
  seed and `/pay` still succeed.
- FX source has no rate on weekends/holidays: the most recent earlier published rate is used (and
  stored for that payment's date), as published reference rates do.
- Payment in a currency the FX source does not cover: "Rate unavailable".
- INR payments (gross already in INR): mid-market and PayPal rates are 1.000000, FX loss is 0.
- Fee greater than gross or negative gross: rejected by the calculation (data error), row flagged
  and shown as "Rate unavailable"-style "Not calculated".
- PayPal rate higher than mid-market (gain): negative FX loss shown as a gain.
- Rounding: values ending in .005 round half-up.
- A payment updated by a later sync (e.g., fee corrected): leakage is recalculated.
- Non-income events (withdrawal, refund, conversion, hold, fee): no leakage columns, not in totals.
- Pending, denied or reversed payments: not in totals; no leakage shown.

## Requirements *(mandatory)*

### Functional Requirements

**Exchange rates**

- **FR-001**: System MUST get the mid-market rate to INR for each (currency, date) from a free FX
  source that publishes INR reference rates, and store it so each (currency, date) is fetched at
  most once.
- **FR-002**: The rate date for a payment MUST be the payment's calendar date in India time (IST).
  If the source has no rate for that date (weekend/holiday), the latest earlier published rate MUST
  be used and the stored record MUST note the date the source actually published.
- **FR-003**: The simulated PayPal rate MUST be the mid-market rate minus a fixed percentage spread
  stored as one named constant, rounded to 6 decimal places.
- **FR-004**: The simulated PayPal rate MUST be labelled "Simulated (sandbox)" everywhere it, or a
  value derived from it (INR received, FX loss), is shown.
- **FR-005**: Fetch failures MUST NOT stop sync, seed or `/pay`; affected payments stay
  "Rate unavailable" and are retried on the next calculation.

**Calculation (Principle II, III)**

- **FR-010**: For each completed income payment, code MUST calculate with the Phase 1A plan
  section 10 formulas: ideal INR = G × r_mid; INR received = N × r_pp; fee loss = F × r_mid;
  FX loss = N × (r_mid − r_pp); total leakage = fee loss + FX loss.
- **FR-011**: Leakage % MUST be total leakage ÷ ideal INR × 100, rounded half-up to 2 decimals.
- **FR-012**: Total leakage MUST equal ideal INR − INR received within ₹0.01.
- **FR-013**: Amounts MUST be exact decimals, rounded half-up to 2 places only when stored or
  shown; rates to 6 places.
- **FR-014**: A missing rate MUST produce a "rate unavailable" status with no numbers.
- **FR-015**: A negative FX loss MUST be kept and shown as a gain.
- **FR-016**: Invalid inputs (fee > gross, negative gross, non-decimal numbers) MUST be rejected
  by the calculation.

**Recalculation**

- **FR-020**: After every sync, demo seed and `/pay` capture, leakage MUST be calculated for
  income payments that have no calculated leakage yet or whose amounts changed.
- **FR-021**: Non-income or non-completed rows MUST have no leakage values.

**Dashboard**

- **FR-030**: The dashboard MUST show five cards for the selected period: total income INR (sum of
  ideal INR), fee loss, FX loss (gain if negative), total leakage, leakage % (total leakage ÷ total
  income × 100).
- **FR-031**: Period filter options: "This month" (current IST calendar month to now), "Last 3
  months" (current IST month plus the two before it), "All time". Default "Last 3 months".
- **FR-032**: The dashboard MUST show breakdown tables by month (IST, newest first) and by client
  (highest total leakage first), each with payment count, income INR, fee loss, FX loss, total
  leakage and leakage %.
- **FR-033**: The dashboard MUST show how many payments in the period are excluded because their
  rate is unavailable.
- **FR-034**: All totals MUST be computed by backend code; the frontend MUST NOT add money values.
- **FR-035**: An empty period MUST show an empty state, not zero cards.
- **FR-036**: The dashboard MUST say which data sources the totals include (PayPal sandbox and/or
  demo seed) and show the "Simulated (sandbox)" notice for FX values.

**Transactions grid**

- **FR-040**: The transactions grid MUST add columns: mid-market rate, PayPal rate (Simulated
  (sandbox)), INR received, fee loss, FX loss, total leakage, leakage %.
- **FR-041**: Rows without a rate MUST show "Rate unavailable" in the leakage columns.
- **FR-042**: The grid MUST sort leakage columns by exact value.

**Deployment (polish)**

- **FR-050**: The repository MUST contain a Render blueprint defining PostgreSQL 18, the backend
  web service (health check `/health`) and the frontend web service.
- **FR-051**: README MUST list deployment steps and every environment variable (backend and
  frontend), marking secrets as set in Render only.
- **FR-052**: Fake adapters MUST stay impossible to enable in production (Principle V).

### Key Entities

- **FX rate**: mid-market rate from one currency to INR for one calendar date; records the date
  the source published it, the source name and when it was fetched. Unique per (currency, date).
- **Transaction leakage** (columns on the existing transaction): mid-market rate, simulated PayPal
  rate, INR received, fee loss, FX loss, total leakage. Ideal INR and leakage % are derived.
- **Dashboard summary**: period, five totals, excluded-row count, sources included, month rows and
  client rows.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The worked example (1000.00 USD, fee 44.00, 84.000000 / 81.500000) produces exactly
  the section 10 values: ₹84,000.00 / ₹77,914.00 / ₹3,696.00 / ₹2,390.00 / ₹6,086.00.
- **SC-002**: For every calculated payment, total leakage equals ideal INR − INR received within
  ₹0.01 (checked over randomly generated inputs).
- **SC-003**: Card totals equal the sum of the month rows and the sum of the client rows exactly.
- **SC-004**: After seeding demo data, 100% of seeded income rows show leakage within one page
  load (with the fake FX source).
- **SC-005**: No screen shows a ₹ value for a payment whose rate is unavailable.
- **SC-006**: The dashboard is usable at 390 px width with no horizontal page scroll and has no
  critical or serious accessibility violations.
- **SC-007**: Following the README, the owner can deploy all three Render services from the
  blueprint without editing the blueprint file.

## Assumptions

- **Spread**: simulated PayPal spread is 3.00% below mid-market (e.g., 84.000000 → 81.480000),
  matching the scale of the plan's worked example; one constant changes it.
- **FX source**: a free, keyless source of central-bank reference rates that includes INR is used
  (chosen and verified in research). Its rates are reference rates, close to but not exactly the
  live mid-market rate; README says so.
- **Rate date**: the payment's IST calendar date; weekend/holiday falls back to the latest earlier
  published rate.
- **Which rows count**: income rows (kind `income`) with status `completed`. Pending, denied and
  reversed rows are excluded.
- **Total income INR** on the cards is the ideal INR (gross × mid-market), so leakage % =
  leakage ÷ income.
- **Months** and "This month" use India time (IST) boundaries.
- **Both sources included**: totals include `paypal_sandbox` and `demo_seed` rows; the dashboard
  states which sources are present. No source filter on the dashboard in Phase 1A.
- **Recalculate trigger**: synchronous at the end of sync, seed and `/pay` (no job queue). Rates
  already cached are reused; only missing (currency, date) pairs are fetched.
- **Dashboard route**: the home page `/` becomes the dashboard; transactions stay at
  `/transactions`.
- **Branch**: by owner decision this feature is built on the current branch `001-paypal-sync`.
- **Render plan**: free-tier services; README notes cold starts and the free database expiry.
