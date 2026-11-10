# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Per-payment leakage in INR (Phase 1A plan section 10): fee loss, FX loss (gains shown as gains), total leakage and leakage %, recalculated after sync, demo seed and `/pay`; "Rate unavailable" instead of numbers when no rate exists (specs/002-leakage-dashboard)
- Mid-market FX rates from Frankfurter (ECB reference rates, keyless), cached in a new `fx_rates` table; PayPal rate simulated as mid-market minus a 3% spread and labelled "Simulated (sandbox)"; `FX_MODE` / `FX_API_URL` settings (specs/002-leakage-dashboard)
- Leakage columns in the transactions grid with exact sorting (specs/002-leakage-dashboard)
- Demo seed history: 24 "Demo seed" transactions for 4 fictional clients over 4 months, idempotent, with `--reset` that removes only seed rows (`uv run python -m scripts.seed_demo`) (specs/001-paypal-sync)
- `/pay` sandbox checkout (PayPal JS SDK v6): order created and captured on the backend, payment recorded at once and linked to the later Transaction Search row; rate-limited `POST /pay/orders` and capture (specs/001-paypal-sync)
- Shared `TextField` form component (specs/001-paypal-sync)
- PayPal sandbox sync: Sync now and on startup, ≤31-day windows with full pagination, idempotent storage, client linking, non-payment events stored but excluded from income, one sync at a time, rate-limited `POST /sync`, `GET /sync/last`, `GET /transactions` (specs/001-paypal-sync)
- Transactions page with sync result and source-labelled grid (specs/001-paypal-sync)
- CI workflow running `npm run check:all` with a PostgreSQL 18 service on every push and PR (specs/001-paypal-sync)
- Project tooling: root check scripts, Husky hooks (lint-staged, commitlint, secretlint), file size check, Vitest + MSW, Playwright setup (specs/001-paypal-sync)
- Backend foundation: typed settings with sandbox-only guard, money/date/error/HTTP-retry/rate-limit helpers, `clients` and `transactions` tables, `GET /health` (specs/001-paypal-sync)
- Frontend foundation: shared UI components (Button, Card, Badge, MoneyText, DataGrid, Spinner, EmptyState, ErrorState, Disclaimer), app shell with demo-mode banner, typed API client with zod validation (specs/001-paypal-sync)

### Fixed

- Database connections no longer use server-side prepared statements, which failed with `NotSupportedError` after the E2E database was recreated under a running backend (specs/002-leakage-dashboard)
- API times are always UTC with `Z`; sync period and start time were returned in the database server's local time zone (specs/001-paypal-sync)
- Backend tests no longer read `backend/.env`, so local PayPal credentials never reach a test run

### Changed

- `.gitignore`: anchor Python `lib/` rules to the repo root so `frontend/lib/` is tracked; add Node/Next.js patterns
